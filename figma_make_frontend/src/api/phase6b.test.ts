import assert from "node:assert/strict"
import { readFile } from "node:fs/promises"
import { test } from "node:test"

import { InMemoryAuthSession, createCanonicalClient } from "./canonical.ts"
import {
  completeRfqReview,
  rfqReviewPermissions,
  startRfqReview,
  validateRfqReviewCompletePayload,
} from "./rfqCommands.ts"
import { createQuotationAttemptManager } from "./quotationCommands.ts"
import { createOrderConversionAttemptManager } from "./orderCommands.ts"
import type { CanonicalRfq } from "./rfq.ts"

const token = "phase6b-test-token"
const rfq: CanonicalRfq = {
  id: 61,
  data_contract: "MVP_V1",
  rfq_number: "RFQ-2026-0061",
  quotation_family_number: null,
  customer_id: 11,
  status: "SUBMITTED",
  project_name: "Phase 6B fixture",
  notes: "Fictional data",
  quote_due_at: "2026-10-10",
  required_delivery_date: "2026-11-10",
  assigned_to_id: null,
  closure_reason: "",
  created_by_id: 7,
  updated_by_id: 7,
  created_at: "2026-09-16T00:00:00+09:00",
  updated_at: "2026-09-16T00:00:00+09:00",
  compatibility: {},
}

const response = (data: unknown) =>
  new Response(JSON.stringify({ success: true, data }), {
    headers: { "content-type": "application/json" },
  })

function client(fetchImplementation: typeof fetch) {
  const auth = new InMemoryAuthSession()
  auth.setAccessToken(token)
  return createCanonicalClient({
    baseUrl: "/api/v1/canonical/",
    auth,
    fetch: fetchImplementation,
  })
}

test("Manager RFQ review uses only canonical start and complete commands", async () => {
  const calls: Array<Record<string, unknown>> = []
  const reviewedClient = client(async (input, init) => {
    calls.push({ path: String(input), body: JSON.parse(String(init?.body)) })
    const started = calls.length === 1
    return response({
      rfq: { ...rfq, status: started ? "UNDER_REVIEW" : "READY_TO_QUOTE" },
      review: { id: started ? 1 : 2 },
    })
  })

  await startRfqReview(reviewedClient, rfq.id)
  await completeRfqReview(reviewedClient, rfq.id, {
    feasible_line_ids: [71],
    drawing_not_required_line_ids: [71],
    notes: " Browser review ",
  })

  assert.deepEqual(calls, [
    {
      path: "/api/v1/canonical/rfqs/61/review/commands/start/",
      body: {},
    },
    {
      path: "/api/v1/canonical/rfqs/61/review/commands/complete/",
      body: {
        feasible_line_ids: [71],
        drawing_not_required_line_ids: [71],
        notes: "Browser review",
      },
    },
  ])
})

test("RFQ review validation and lifecycle fail closed", () => {
  assert.deepEqual(rfqReviewPermissions("Manager", "SUBMITTED", false), {
    start: true,
    complete: false,
  })
  assert.deepEqual(rfqReviewPermissions("Sales", "SUBMITTED", false), {
    start: false,
    complete: false,
  })
  assert.deepEqual(rfqReviewPermissions("Manager", "UNDER_REVIEW", true), {
    start: false,
    complete: false,
  })
  assert.throws(() =>
    validateRfqReviewCompletePayload({
      feasible_line_ids: [71, 71],
      drawing_not_required_line_ids: [],
    }),
  )
})

test("session reset clears quotation and conversion idempotency contexts", () => {
  const quotationAttempt = createQuotationAttemptManager(
    () => "phase6b.quote.key",
  )
  quotationAttempt.begin({ kind: "initial", rfqId: 61 }, {
    currency: "VND",
    valid_from: "2026-09-16",
    valid_until: "2026-10-16",
    discount_total: "0.0000",
    tax_amount: "0.0000",
    terms: "",
    lines: [
      { source_rfq_line_id: 71, unit_price: "100.0000", discount: "0.0000" },
    ],
  })
  const conversionAttempt = createOrderConversionAttemptManager(
    () => "phase6b.order.key",
  )
  conversionAttempt.begin({ quotationId: 81, familyNumber: "QT-2026-0081" }, {})
  quotationAttempt.reset()
  conversionAttempt.reset()
  assert.equal(quotationAttempt.hasActiveAttempt(), false)
  assert.equal(conversionAttempt.hasActiveAttempt(), false)
})

test("workspace authentication boundaries clear mutable state", async () => {
  const sources = await Promise.all([
    readFile(
      new URL("../components/QuotationWorkspace.tsx", import.meta.url),
      "utf8",
    ),
    readFile(
      new URL("../components/OrderWorkspace.tsx", import.meta.url),
      "utf8",
    ),
  ])
  for (const source of sources) {
    assert.match(source, /if \(!authenticated\) \{/)
    assert.match(source, /\.reset\(\)/)
    assert.match(source, /setWorkspace\(null\)/)
  }
})

test("hash navigation updates the mounted app without reloading memory auth", async () => {
  const source = await readFile(new URL("../App.tsx", import.meta.url), "utf8")
  assert.match(
    source,
    /window\.addEventListener\("hashchange", synchronizeRoute\)/,
  )
  assert.match(
    source,
    /window\.removeEventListener\("hashchange", synchronizeRoute\)/,
  )
})

test("browser runner sets date controls deterministically through UI events", async () => {
  const source = await readFile(
    new URL(
      "../../../tests/e2e/phase6b_canonical_browser_e2e.py",
      import.meta.url,
    ),
    "utf8",
  )
  assert.match(source, /def replace_date\(driver, element, value\):/)
  assert.match(source, /new Event\("input", \{ bubbles: true \}\)/)
  assert.match(source, /new Event\("change", \{ bubbles: true \}\)/)
  assert.doesNotMatch(
    source,
    /replace\(field_by_label\(driver, "(?:Hạn báo giá|Ngày giao hàng|Ngày giao)"\)/,
  )
})

test("browser runner waits for authoritative quotation detail state", async () => {
  const [quotationWorkspace, orderWorkspace, runner] = await Promise.all([
    readFile(
      new URL("../components/QuotationWorkspace.tsx", import.meta.url),
      "utf8",
    ),
    readFile(
      new URL("../components/OrderWorkspace.tsx", import.meta.url),
      "utf8",
    ),
    readFile(
      new URL(
        "../../../tests/e2e/phase6b_canonical_browser_e2e.py",
        import.meta.url,
      ),
      "utf8",
    ),
  ])
  assert.match(quotationWorkspace, /data-testid="quotation-workspace-detail"/)
  assert.match(orderWorkspace, /data-testid="order-workspace-detail"/)
  assert.match(orderWorkspace, /data-order-status=/)
  assert.match(orderWorkspace, /data-order-progress=/)
  assert.match(orderWorkspace, /data-testid="order-progress-input"/)
  assert.match(orderWorkspace, /data-testid="order-reason-input"/)
  assert.match(
    runner,
    /\[data-testid='quotation-workspace-detail'\].*\[data-quotation-status=/s,
  )
  assert.match(
    runner,
    /\[data-testid='order-workspace-detail'\].*\[data-order-number=/s,
  )
  assert.doesNotMatch(runner, /status in current\.page_source/)
})

test("Phase 6B adds no browser credential persistence or legacy workflow writes", async () => {
  const sources = await Promise.all([
    readFile(
      new URL("../components/RfqWorkspace.tsx", import.meta.url),
      "utf8",
    ),
    readFile(
      new URL("../components/QuotationWorkspace.tsx", import.meta.url),
      "utf8",
    ),
    readFile(
      new URL("../components/OrderWorkspace.tsx", import.meta.url),
      "utf8",
    ),
  ])
  const source = sources.join("\n")
  assert.equal(
    /localStorage|sessionStorage|indexedDB|document\.cookie/.test(source),
    false,
  )
  assert.equal(/\/api\/v1\/(?!canonical\/)/.test(source), false)
})
