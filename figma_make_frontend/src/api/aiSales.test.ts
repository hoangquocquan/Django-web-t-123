import assert from "node:assert/strict"
import { readFileSync } from "node:fs"
import test from "node:test"

import { analyzeAiSales, type AiSalesAnalysis } from "./aiSales.ts"

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

test("AI Sales page exposes human review, structured output, and three demo cases", () => {
  const source = readFileSync(new URL("../components/AiSalesPage.tsx", import.meta.url), "utf8")

  assert.match(source, /AI recommendation — human review required/)
  assert.match(source, /Matched components/)
  assert.match(source, /Missing information/)
  assert.match(source, /Draft response · review before use/)
  assert.match(source, /SUS316 supported case/)
  assert.match(source, /Unsupported weather case/)
  assert.match(source, /Incomplete request case/)
  assert.doesNotMatch(source, /send email automatically/i)
})
