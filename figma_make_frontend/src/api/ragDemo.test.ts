import assert from "node:assert/strict"
import { readFile } from "node:fs/promises"
import { test } from "node:test"

import { askSyntheticRagDemo } from "./aiDemo.ts"

test("internal RAG demo sends the bearer token to the scoped endpoint", async () => {
  const originalFetch = globalThis.fetch
  let observedUrl = ""
  let observedHeaders = new Headers()
  globalThis.fetch = async (input, init) => {
    observedUrl = String(input)
    observedHeaders = new Headers(init?.headers)
    return new Response(
      JSON.stringify({
        success: true,
        data: {
          answer: "Grounded synthetic answer",
          status: "SUPPORTED",
          sources: [{
            title: "[SYNTHETIC DEMO] Product",
            product_code: "SYN-RAG-0001",
            citation: "synthetic://rag_synthetic_demo_v1/SYN-RAG-0001?revision=1",
            document_id: 206,
            version: 1,
            revision: "1",
            chunk_id: 1,
            relevance_score: 1,
          }],
          retrieval: {
            result_count: 1,
            candidate_chunks_considered: 1,
            provider: "development-hash-fallback",
            provider_mode: "development-hash-plus-lexical",
            dataset_id: "rag_synthetic_demo_v1",
            corpus_documents: 25,
          },
        },
      }),
      { status: 200, headers: { "content-type": "application/json" } },
    )
  }
  try {
    const result = await askSyntheticRagDemo("internal-token", "Find SYN-RAG-0001")
    assert.equal(result.status, "SUPPORTED")
    assert.equal(result.sources[0].product_code, "SYN-RAG-0001")
  } finally {
    globalThis.fetch = originalFetch
  }

  assert.equal(observedUrl, "/api/v1/internal/rag-demo/query/")
  assert.equal(observedHeaders.get("authorization"), "Bearer internal-token")
})

test("RAG demo page includes input loading answer citation unavailable and error states", async () => {
  const component = await readFile(
    new URL("../components/RagDemoPage.tsx", import.meta.url),
    "utf8",
  )
  const app = await readFile(new URL("../App.tsx", import.meta.url), "utf8")

  assert.match(app, /admin-rag-demo/)
  assert.match(app, /<RagDemoPage/)
  assert.match(component, /SYNTHETIC DEMO DATA — NOT REAL COMPANY DATA/)
  assert.match(component, /aria-label="RAG demo question"/)
  assert.match(component, /Đang truy xuất corpus synthetic/)
  assert.match(component, /<h2 className="font-semibold">Answer<\/h2>/)
  assert.match(component, /<h2 className="font-semibold">Sources<\/h2>/)
  assert.match(component, /Citation rendering failure/)
  assert.match(component, /UNAVAILABLE/)
  assert.match(component, /role="alert"/)
  assert.match(component, /What is the sales price of SYN-RAG-0001/)
  assert.match(component, /Which customer ordered the optical sensor housing/)
  assert.match(component, /development-hash-plus-lexical/)
})

