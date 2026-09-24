import assert from "node:assert/strict"
import { readFile } from "node:fs/promises"
import { test } from "node:test"

import {
  CanonicalClientError,
  InMemoryAuthSession,
  createCanonicalClient,
} from "./canonical.ts"
import {
  archiveQuotation,
  canCreateInitialQuotation,
  createQuotation,
  createQuotationAttemptManager,
  createQuotationRequestGuards,
  decideQuotation,
  executeQuotationCreateAttempt,
  fetchQuotationIndex,
  fetchQuotationWorkspace,
  quotationCommandStateFromError,
  quotationIndexPaths,
  quotationLifecyclePermissions,
  quotationReadPaths,
  recordQuotationCustomerDecision,
  sendQuotation,
  settleQuotationCommandOnDeactivate,
  submitQuotation,
  updateQuotation,
  validateQuotationCreatePayload,
  validateQuotationDecisionPayload,
  validateQuotationRejectionPayload,
  validateQuotationSendPayload,
  validateQuotationUpdatePayload,
  type CanonicalApprovalDecision,
  type CanonicalCustomerDecision,
  type CanonicalQuotation,
  type CanonicalQuotationFamily,
  type CanonicalQuotationLine,
  type QuotationCreatePayload,
} from "./quotationCommands.ts"
import type { CanonicalPage } from "./rfq.ts"

const token = "phase5d-test-token"

const quotation: CanonicalQuotation = {
  id: 101,
  data_contract: "MVP_V1",
  quotation_family_number: "QT-2026-0001",
  quotation_number: "QT-2026-0001-R0",
  revision: 0,
  rfq_id: 41,
  customer_id: 11,
  workflow_status: "DRAFT",
  currency: "USD",
  valid_from: "2026-09-14",
  valid_until: "2026-09-28",
  subtotal: "100.0000",
  discount_total: "5.0000",
  tax_amount: "10.0000",
  total: "105.0000",
  sent_at: null,
  created_by_id: 7,
  created_at: "2026-09-14T00:00:00+09:00",
  updated_at: "2026-09-14T00:00:00+09:00",
  compatibility: {},
  terms: "Net 30",
  customer_snapshot: { id: 11, company_name: "Canonical Customer" },
  rfq_snapshot: { id: 41, rfq_number: "RFQ-2026-0001" },
  updated_by_id: 7,
}

const line: CanonicalQuotationLine = {
  id: 201,
  quotation_id: quotation.id,
  data_contract: "MVP_V1",
  line_number: 1,
  source_rfq_line_id: 51,
  part_id: 21,
  description: "Machined bracket",
  part_code_snapshot: "PART-001",
  material_snapshot: "SUS304",
  unit: "PCS",
  quantity: "10.0000",
  unit_price: "10.0000",
  discount: "0.0000",
  line_subtotal: "100.0000",
  line_total: "100.0000",
  created_at: "2026-09-14T00:00:00+09:00",
}

const approval: CanonicalApprovalDecision = {
  id: 301,
  quotation_id: quotation.id,
  reviewer_id: 9,
  decision: "APPROVED",
  reason: "",
  notes: "Approved",
  decided_at: "2026-09-14T01:00:00+09:00",
}

const customerDecision: CanonicalCustomerDecision = {
  id: 401,
  quotation_id: quotation.id,
  recorded_by_id: 7,
  decision: "ACCEPTED",
  reason: "",
  contact_evidence_recorded: true,
  decision_evidence_recorded: true,
  decided_at: "2026-09-14T02:00:00+09:00",
}

const family: CanonicalQuotationFamily = {
  quotation_family_number: "QT-2026-0001",
  rfq_id: 41,
  rfq_number: "RFQ-2026-0001",
  customer_id: 11,
  revision_count: 1,
  revisions: [quotation],
}

const workspaceData = {
  quotation,
  lines: [line],
  family,
  revisions: [quotation],
  approvals: [approval],
  customerDecisions: [customerDecision],
}

const payload: QuotationCreatePayload = {
  currency: "USD",
  valid_from: "2026-09-14",
  valid_until: "2026-09-28",
  discount_total: "5",
  tax_amount: "10",
  terms: "Net 30",
  lines: [{ source_rfq_line_id: 51, unit_price: "10", discount: "0" }],
}

type CreateCall = {
  path: string
  method?: string
  key: string | null
}

type CommandCall = {
  path: string
  body: unknown
}

const page = <T>(results: T[]): CanonicalPage<T> => ({
  count: results.length,
  limit: 100,
  offset: 0,
  next_offset: null,
  previous_offset: null,
  results,
})

const response = (data: unknown, status = 200) =>
  new Response(JSON.stringify({ success: true, data }), {
    status,
    headers: { "content-type": "application/json" },
  })

function client(fetchImplementation: typeof fetch) {
  const auth = new InMemoryAuthSession()
  auth.setAccessToken(token)
  return createCanonicalClient({
    baseUrl: "/api/v1/canonical/",
    auth,
    fetch: fetchImplementation,
    defaultTimeoutMs: 50,
  })
}

function workspaceFetch(paths: string[]) {
  return client(async (input) => {
    const path = String(input)
    paths.push(path)
    if (path.endsWith(`/quotations/${quotation.id}/`))
      return response(quotation)
    if (path.includes("/lines/")) return response(page([line]))
    if (path.includes("/approval-decisions/")) return response(page([approval]))
    if (path.includes("/customer-decisions/")) {
      return response(page([customerDecision]))
    }
    if (path.includes("/revisions/")) return response(page([quotation]))
    return response(family)
  })
}

test("Phase 5D constructs only bounded canonical quotation read paths", async () => {
  assert.deepEqual(quotationIndexPaths(), {
    families: "quotation-families/?limit=20&ordering=quotation_family_number",
    quotations:
      "quotations/?data_contract=MVP_V1&limit=20&ordering=-created_at",
  })
  assert.deepEqual(quotationReadPaths(101, "QT-2026-0001"), {
    detail: "quotations/101/",
    lines: "quotations/101/lines/?limit=100&ordering=line_number",
    approvals:
      "quotations/101/approval-decisions/?limit=100&ordering=decided_at",
    customerDecisions:
      "quotations/101/customer-decisions/?limit=100&ordering=decided_at",
    family: "quotation-families/QT-2026-0001/",
    revisions:
      "quotation-families/QT-2026-0001/revisions/?limit=100&ordering=revision",
  })

  const paths: string[] = []
  const result = await fetchQuotationWorkspace(
    workspaceFetch(paths),
    quotation.id,
    quotation.quotation_family_number,
  )
  assert.equal(result.quotation.id, quotation.id)
  assert.equal(result.lines.length, 1)
  assert.equal(paths.length, 6)
  assert.equal(
    paths.some((path) => path.includes("/api/v1/sales/")),
    false,
  )
})

test("quotation index loads canonical family and revision pages", async () => {
  const paths: string[] = []
  const result = await fetchQuotationIndex(
    client(async (input) => {
      paths.push(String(input))
      return String(input).includes("quotation-families")
        ? response(page([family]))
        : response(page([quotation]))
    }),
  )
  assert.equal(result.families.count, 1)
  assert.equal(result.quotations.count, 1)
  assert.equal(paths.length, 2)
})

test("initial and revision creation use exact POST endpoints and idempotency keys", async () => {
  const calls: CreateCall[] = []
  const api = client(async (input, init) => {
    calls.push({
      path: String(input),
      method: init?.method,
      key: new Headers(init?.headers).get("idempotency-key"),
    })
    return response(quotation, 201)
  })
  await createQuotation(
    api,
    { kind: "initial", rfqId: 41 },
    payload,
    "create-key",
  )
  await createQuotation(
    api,
    { kind: "revision", quotationId: 101 },
    payload,
    "revision-key",
  )
  assert.deepEqual(calls, [
    {
      path: "/api/v1/canonical/rfqs/41/quotations/commands/create/",
      method: "POST",
      key: "create-key",
    },
    {
      path: "/api/v1/canonical/quotations/101/commands/create-revision/",
      method: "POST",
      key: "revision-key",
    },
  ])
})

test("every non-create quotation action uses its exact POST command and payload", async () => {
  const calls: CommandCall[] = []
  const api = client(async (input, init) => {
    const path = String(input)
    calls.push({ path, body: JSON.parse(String(init?.body)) })
    assert.equal(init?.method, "POST")
    if (path.endsWith("/approve/") || path.endsWith("/reject/")) {
      return response({ quotation, decision: approval })
    }
    if (path.endsWith("/accept/") || path.endsWith("/decline/")) {
      return response({ quotation, decision: customerDecision })
    }
    return response(quotation)
  })
  await updateQuotation(api, 101, { terms: "Updated" })
  await archiveQuotation(api, 101)
  await submitQuotation(api, 101)
  await decideQuotation(api, 101, "approve", { notes: "ok" })
  await decideQuotation(api, 101, "reject", { reason: "rework", notes: "x" })
  await sendQuotation(api, 101, { sent_to: "Buyer", evidence: "CRM-1" })
  await recordQuotationCustomerDecision(api, 101, "accept", {
    contact_snapshot: "Buyer",
    evidence: "Signed",
  })
  await recordQuotationCustomerDecision(api, 101, "decline", {
    contact_snapshot: "Buyer",
    evidence: "Email",
    reason: "Budget",
  })
  assert.deepEqual(
    calls.map((item) => item.path),
    [
      "quotations/101/commands/update/",
      "quotations/101/commands/archive/",
      "quotations/101/commands/submit/",
      "quotations/101/commands/approve/",
      "quotations/101/commands/reject/",
      "quotations/101/commands/send/",
      "quotations/101/commands/accept/",
      "quotations/101/commands/decline/",
    ].map((path) => `/api/v1/canonical/${path}`),
  )
  assert.deepEqual(calls[1]!.body, {})
  assert.deepEqual(calls[2]!.body, {})
})

test("commercial payload validators allowlist exact backend fields", () => {
  assert.deepEqual(validateQuotationCreatePayload(payload), payload)
  assert.deepEqual(validateQuotationUpdatePayload({ terms: " Revised " }), {
    terms: "Revised",
  })
  assert.throws(
    () => validateQuotationCreatePayload({ ...payload, total: "1" }),
    { code: "client_validation_error" },
  )
  assert.throws(
    () => validateQuotationUpdatePayload({ workflow_status: "APPROVED" }),
    { code: "client_validation_error" },
  )
})

test("commercial decimals enforce the backend max_digits and decimal_places contract", () => {
  assert.equal(
    validateQuotationUpdatePayload({ tax_amount: "1234567890123456.1234" })
      .tax_amount,
    "1234567890123456.1234",
  )
  assert.throws(
    () => validateQuotationUpdatePayload({ tax_amount: "12345678901234567" }),
    { code: "client_validation_error" },
  )
  assert.throws(
    () => validateQuotationUpdatePayload({ tax_amount: "0.00001" }),
    { code: "client_validation_error" },
  )
})

test("send, rejection, acceptance, and decline payloads enforce exact evidence", () => {
  assert.deepEqual(
    validateQuotationSendPayload({ sent_to: " Buyer ", evidence: " CRM-1 " }),
    { sent_to: "Buyer", evidence: "CRM-1" },
  )
  assert.throws(() => validateQuotationRejectionPayload({ notes: "x" }), {
    code: "client_validation_error",
  })
  assert.throws(
    () =>
      validateQuotationDecisionPayload(
        { contact_snapshot: "Buyer", evidence: "Email" },
        "DECLINED",
      ),
    { code: "client_validation_error" },
  )
  assert.deepEqual(
    validateQuotationDecisionPayload(
      { contact_snapshot: "Buyer", evidence: "Signed" },
      "ACCEPTED",
    ),
    { contact_snapshot: "Buyer", evidence: "Signed" },
  )
})

test("approval and rejection command boundaries enforce their distinct serializers", async () => {
  let requests = 0
  const api = client(async () => {
    requests += 1
    return response({ quotation, decision: approval })
  })
  const invalidApproval = { notes: "ok", reason: "unsupported" }
  await assert.rejects(decideQuotation(api, 101, "approve", invalidApproval), {
    code: "client_validation_error",
  })
  await assert.rejects(decideQuotation(api, 101, "reject", {}), {
    code: "client_validation_error",
  })
  assert.equal(requests, 0)
})

test("same logical initial create retry retains original key and payload", async () => {
  const manager = createQuotationAttemptManager(() => "retained-key")
  const bodies: unknown[] = []
  const keys: Array<string | null> = []
  let calls = 0
  const api = client(async (_input, init) => {
    calls += 1
    bodies.push(JSON.parse(String(init?.body)))
    keys.push(new Headers(init?.headers).get("idempotency-key"))
    if (calls === 1) {
      throw new CanonicalClientError({
        kind: "network",
        code: "network_error",
        message: "private",
      })
    }
    return response(quotation)
  })
  const reconcile = async () => workspaceData
  await assert.rejects(
    executeQuotationCreateAttempt(
      api,
      manager,
      { kind: "initial", rfqId: 41 },
      payload,
      reconcile,
    ),
    { code: "network_error" },
  )
  await executeQuotationCreateAttempt(
    api,
    manager,
    { kind: "initial", rfqId: 99 },
    { ...payload, terms: "Changed" },
    reconcile,
  )
  assert.deepEqual(keys, ["retained-key", "retained-key"])
  assert.deepEqual(bodies, [payload, payload])
})

test("revision create retains created id and reconciles without duplicate POST", async () => {
  const manager = createQuotationAttemptManager(() => "revision-key")
  let posts = 0
  let reconciles = 0
  const api = client(async () => {
    posts += 1
    return response({ ...quotation, revision: 1 })
  })
  const reconcile = async () => {
    reconciles += 1
    if (reconciles === 1) {
      throw new CanonicalClientError({
        kind: "timeout",
        code: "request_timeout",
        message: "private",
      })
    }
    return workspaceData
  }
  await assert.rejects(
    executeQuotationCreateAttempt(
      api,
      manager,
      { kind: "revision", quotationId: 101 },
      payload,
      reconcile,
    ),
  )
  assert.equal(manager.hasCreatedQuotation(), true)
  await executeQuotationCreateAttempt(
    api,
    manager,
    { kind: "revision", quotationId: 101 },
    payload,
    reconcile,
  )
  assert.equal(posts, 1)
  assert.equal(reconciles, 2)
  assert.equal(manager.hasActiveAttempt(), false)
})

test("changed-payload retry is prevented and active payload is defensively copied", () => {
  const manager = createQuotationAttemptManager(() => "fixed-key")
  manager.begin({ kind: "initial", rfqId: 41 }, payload)
  const changed = manager.begin({ kind: "initial", rfqId: 99 }, {
    ...payload,
    terms: "Changed",
    lines: [{ ...payload.lines[0]!, unit_price: "99" }],
  })
  assert.equal(changed.target.kind, "initial")
  assert.deepEqual(manager.activePayload(), payload)
  const copy = manager.activePayload()!
  copy.lines[0]!.unit_price = "777"
  assert.deepEqual(manager.activePayload(), payload)
})

test("active create attempt locks every retained-payload field in the workspace", async () => {
  const manager = createQuotationAttemptManager(() => "fixed-key")
  manager.begin({ kind: "initial", rfqId: 41 }, payload)
  assert.equal(manager.hasActiveAttempt(), true)
  const source = await readFile(
    new URL("../components/QuotationWorkspace.tsx", import.meta.url),
    "utf8",
  )
  assert.match(
    source,
    /const locked = pending \|\| needsReconciliation \|\| activeAttempt/,
  )
  assert.match(
    source,
    /const formEditable = workspace[\s\S]*canCreateInitialQuotation/,
  )
  assert.match(source, /disabled=\{!formEditable\}/)
  assert.match(source, /disabled=\{pending \|\| activeAttempt\}/)
})

test("lifecycle permissions expose only exact Sales/Admin or Manager actions", () => {
  assert.deepEqual(quotationLifecyclePermissions("Sales", "DRAFT", false), {
    update: true,
    archive: true,
    submit: true,
    createRevision: false,
    send: false,
    accept: false,
    decline: false,
    approve: false,
    reject: false,
  })
  assert.equal(
    quotationLifecyclePermissions("Manager", "PENDING_APPROVAL", false).approve,
    true,
  )
  assert.equal(
    quotationLifecyclePermissions("Admin", "PENDING_APPROVAL", false).approve,
    false,
  )
  assert.equal(
    quotationLifecyclePermissions("Sales", "PENDING_APPROVAL", false).reject,
    false,
  )
  assert.equal(
    quotationLifecyclePermissions("Manager", "PENDING_APPROVAL", true).approve,
    false,
  )
})

test("initial creation visibility requires Sales/Admin and READY_TO_QUOTE", () => {
  assert.equal(
    canCreateInitialQuotation("Sales", "READY_TO_QUOTE", false),
    true,
  )
  assert.equal(
    canCreateInitialQuotation("Admin", "READY_TO_QUOTE", false),
    true,
  )
  assert.equal(
    canCreateInitialQuotation("Manager", "READY_TO_QUOTE", false),
    false,
  )
  assert.equal(canCreateInitialQuotation("Sales", "SUBMITTED", false), false)
  assert.equal(
    canCreateInitialQuotation("Sales", "READY_TO_QUOTE", true),
    false,
  )
})

test("maker-checker, ownership, lifecycle, and server outcomes are deterministic and sanitized", () => {
  const maker = quotationCommandStateFromError(
    new CanonicalClientError({
      kind: "validation",
      code: "validation_error",
      message: "private backend text",
      details: { reviewer: ["creator cannot decide"] },
    }),
    "approve",
  )
  assert.equal(maker.status, "maker_checker_denied")
  assert.equal(maker.message.includes("private"), false)
  const owner = quotationCommandStateFromError(
    new CanonicalClientError({
      kind: "permission",
      code: "permission_denied",
      message: "private owner text",
    }),
    "update",
  )
  assert.equal(owner.status, "ownership_denied")
  const lifecycle = quotationCommandStateFromError(
    new CanonicalClientError({
      kind: "conflict",
      code: "invalid_state",
      message: "private state",
    }),
  )
  assert.equal(lifecycle.status, "lifecycle_conflict")
  const server = quotationCommandStateFromError(
    new CanonicalClientError({
      kind: "server",
      code: "internal_error",
      message: "private stack",
    }),
  )
  assert.equal(server.status, "server")
  assert.equal(server.message.includes("private"), false)
})

test("request guards suppress stale index, workspace, and RFQ-line responses independently", () => {
  const guards = createQuotationRequestGuards()
  const oldIndex = guards.index.next()
  const workspace = guards.workspace.next()
  const rfqLines = guards.rfqLines.next()
  assert.equal(guards.index.isLatest(oldIndex), true)
  assert.equal(guards.workspace.isLatest(workspace), true)
  assert.equal(guards.rfqLines.isLatest(rfqLines), true)
  guards.index.next()
  assert.equal(guards.index.isLatest(oldIndex), false)
  assert.equal(guards.workspace.isLatest(workspace), true)
})

test("tab deactivation releases pending UI state after obsolete requests are invalidated", () => {
  const pending = {
    status: "pending" as const,
    message: "Đang gửi lệnh báo giá...",
  }
  assert.deepEqual(settleQuotationCommandOnDeactivate(pending), {
    status: "cancelled",
    message:
      "Yêu cầu đang chờ đã bị hủy; hãy đồng bộ hoặc thử lại khi quay lại.",
  })

  const ready = { status: "ready" as const, message: "Đã đồng bộ." }
  assert.equal(settleQuotationCommandOnDeactivate(ready), ready)
})

test("quotation reads honor caller cancellation during navigation", async () => {
  const controller = new AbortController()
  controller.abort()
  await assert.rejects(
    fetchQuotationIndex(
      client(async () => response(page([]))),
      controller.signal,
    ),
    { code: "request_cancelled" },
  )
})

test("successful command output is reconciled with backend-authoritative reads", async () => {
  const paths: string[] = []
  const data = await fetchQuotationWorkspace(
    workspaceFetch(paths),
    quotation.id,
    quotation.quotation_family_number,
  )
  assert.equal(data.quotation.total, "105.0000")
  assert.equal(data.lines[0]!.line_total, "100.0000")
  assert.equal(data.approvals[0]!.decision, "APPROVED")
  assert.equal(data.customerDecisions[0]!.contact_evidence_recorded, true)
})

test("Phase 5D source excludes conversion, legacy API, persistence, key rendering, and mock quotation data", async () => {
  const sources = await Promise.all([
    readFile(new URL("./quotationCommands.ts", import.meta.url), "utf8"),
    readFile(
      new URL("../components/QuotationWorkspace.tsx", import.meta.url),
      "utf8",
    ),
  ])
  const source = sources.join("\n")
  assert.equal(source.includes("convert-to-order"), false)
  assert.equal(source.includes("/api/v1/sales/quotations/"), false)
  assert.equal(
    /localStorage|sessionStorage|indexedDB|document\.cookie/.test(source),
    false,
  )
  assert.equal(/console\.(log|warn|error|debug|info)/.test(source), false)
  assert.equal(/Samsung SDI|QT-2026-082|phase5d-test-token/.test(source), false)
  assert.equal(/attempt\.key|idempotencyKey\}/.test(sources[1]), false)
})

test("sales-quotes keeps RFQ and quotation workspaces mounted and passes authenticated role", async () => {
  const source = await readFile(new URL("../App.tsx", import.meta.url), "utf8")
  const start = source.indexOf('route === "sales-quotes"')
  const end = source.indexOf('route === "sales-ai"')
  const slice = source.slice(start, end)
  assert.match(slice, /<RfqWorkspace/)
  assert.match(slice, /<QuotationWorkspace/)
  assert.match(slice, /active=\{quoteWorkspace === "quotation"\}/)
  assert.match(source, /role=\{session\.status === "authenticated"/)
})

test("full frontend script preserves Phase 5A, 5B, and 5C suites", async () => {
  const packageSource = JSON.parse(
    await readFile(new URL("../../package.json", import.meta.url), "utf8"),
  ) as { scripts: Record<string, string> }
  assert.match(packageSource.scripts.test, /canonical\.test\.ts/)
  assert.match(packageSource.scripts.test, /phase5b\.test\.ts/)
  assert.match(packageSource.scripts.test, /phase5c\.test\.ts/)
  assert.match(packageSource.scripts.test, /phase5d\.test\.ts/)
})
