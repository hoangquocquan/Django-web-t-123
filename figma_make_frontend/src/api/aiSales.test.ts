import assert from "node:assert/strict"
import { readFileSync } from "node:fs"
import test from "node:test"

import { analyzeAiSales, type AiSalesAnalysis } from "./aiSales.ts"
import type { createCanonicalClient } from "./canonical.ts"

test("AI Sales client posts only to the internal analyze endpoint", async () => {
  const calls: Array<{ path: string; options: RequestInit & { timeoutMs?: number } }> = []
  const expected = { status: "SUPPORTED" } as AiSalesAnalysis
  const client = {
    request: async (path: string, options: RequestInit & { timeoutMs?: number }) => {
      calls.push({ path, options })
      return expected
    },
  } as unknown as ReturnType<typeof createCanonicalClient>

  const result = await analyzeAiSales(client, {
    request: "Need SUS316 electropolished component",
  })

  assert.equal(result, expected)
  assert.equal(calls[0].path, "internal/ai-sales/analyze/")
  assert.equal(calls[0].options.method, "POST")
  assert.match(String(calls[0].options.body), /SUS316/)
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
