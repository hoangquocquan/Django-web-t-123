import assert from "node:assert/strict"
import { readFileSync } from "node:fs"
import test from "node:test"

import {
  analyzeAiSales,
  createAiSalesRequestGuards,
  listAiSalesRfqs,
  type AiSalesAnalysis,
} from "./aiSales.ts"
import { CanonicalClientError } from "./canonical.ts"

test("AI Sales client posts only to the internal analyze endpoint", async () => {
  const expected = { status: "SUPPORTED" } as AiSalesAnalysis
  const originalFetch = globalThis.fetch
  let requestUrl = ""
  let requestBody = ""
  let authorization = ""
  globalThis.fetch = async (input, init) => {
    requestUrl = String(input)
    requestBody = String(init?.body)
    authorization = new Headers(init?.headers).get("authorization") ?? ""
    return new Response(JSON.stringify({ success: true, data: expected }), {
      status: 200,
      headers: { "content-type": "application/json" },
    })
  }
  let result: AiSalesAnalysis
  try {
    result = await analyzeAiSales("session-token", {
      request: "Need SUS316 electropolished component",
    })
  } finally {
    globalThis.fetch = originalFetch
  }

  assert.deepEqual(result, expected)
  assert.equal(requestUrl, "/api/v1/internal/ai-sales/analyze/")
  assert.equal(authorization, "Bearer session-token")
  assert.match(requestBody, /SUS316/)
})

test("AI Sales RFQ selector uses the minimized internal list endpoint", async () => {
  const originalFetch = globalThis.fetch
  let requestUrl = ""
  let requestMethod = ""
  let requestBody: BodyInit | null | undefined
  globalThis.fetch = async (input, init) => {
    requestUrl = String(input)
    requestMethod = String(init?.method)
    requestBody = init?.body
    return new Response(
      JSON.stringify({
        success: true,
        data: {
          count: 1,
          results: [
            {
              id: 42,
              rfq_number: "RFQ-42",
              status: "DRAFT",
              project_name: "Fixture",
              customer_display: "Scoped Customer",
              quote_due_at: "2026-11-01",
              required_delivery_date: "2026-12-01",
            },
          ],
        },
      }),
      { status: 200, headers: { "content-type": "application/json" } },
    )
  }
  try {
    const result = await listAiSalesRfqs("session-token")
    assert.equal(result.results[0]?.rfq_number, "RFQ-42")
  } finally {
    globalThis.fetch = originalFetch
  }

  assert.equal(requestUrl, "/api/v1/internal/ai-sales/rfqs/")
  assert.equal(requestMethod, "GET")
  assert.equal(requestBody, undefined)
})

test("canonical RFQ analysis sends only rfq_id", async () => {
  const originalFetch = globalThis.fetch
  let requestBody = ""
  globalThis.fetch = async (_input, init) => {
    requestBody = String(init?.body)
    return new Response(
      JSON.stringify({ success: true, data: { status: "SUPPORTED" } }),
      { status: 200, headers: { "content-type": "application/json" } },
    )
  }
  try {
    await analyzeAiSales("session-token", { rfq_id: 42 })
  } finally {
    globalThis.fetch = originalFetch
  }

  assert.deepEqual(JSON.parse(requestBody), { rfq_id: 42 })
})

test("AI Sales caller cancellation is not misreported as a timeout", async () => {
  const originalFetch = globalThis.fetch
  globalThis.fetch = async (_input, init) =>
    await new Promise<Response>((_resolve, reject) => {
      init?.signal?.addEventListener(
        "abort",
        () => reject(new DOMException("Aborted", "AbortError")),
        { once: true },
      )
    })
  const controller = new AbortController()
  const request = listAiSalesRfqs("session-token", controller.signal)
  controller.abort()
  try {
    await assert.rejects(
      request,
      (error: unknown) =>
        error instanceof CanonicalClientError &&
        error.kind === "cancelled" &&
        error.code === "request_cancelled",
    )
  } finally {
    globalThis.fetch = originalFetch
  }
})

test("AI Sales request guards reject stale selector and analysis responses", () => {
  const guards = createAiSalesRequestGuards()
  const oldSelector = guards.selector.next()
  const latestSelector = guards.selector.next()
  const oldAnalysis = guards.analysis.next()
  const latestAnalysis = guards.analysis.next()

  assert.equal(guards.selector.isLatest(oldSelector), false)
  assert.equal(guards.selector.isLatest(latestSelector), true)
  assert.equal(guards.analysis.isLatest(oldAnalysis), false)
  assert.equal(guards.analysis.isLatest(latestAnalysis), true)
})

test("AI Sales page exposes human review, structured output, and three demo cases", () => {
  const source = readFileSync(new URL("../components/AiSalesPage.tsx", import.meta.url), "utf8")

  assert.match(source, /AI recommendation — human review required/)
  assert.match(source, /Matched components/)
  assert.match(source, /Missing information/)
  assert.match(source, /Draft response · review before use/)
  assert.match(source, /SUS316 supported case/)
  assert.match(source, /Unsupported weather case/)
  assert.match(source, /Incomplete request case/)
  assert.match(source, /REAL \/ CANONICAL RFQ/)
  assert.match(source, /SYNTHETIC DEMO/)
  assert.match(source, /listAiSalesRfqs/)
  assert.match(source, /run\(\{ rfq_id: selectedRfq\.id \}\)/)
  assert.match(source, /analysisGuard\.isLatest\(requestId\)/)
  assert.doesNotMatch(source, /send email automatically/i)
  assert.doesNotMatch(source, /<button[^>]*>[^<]*(Send|Gửi (email|tin nhắn|khách hàng))/i)
})
