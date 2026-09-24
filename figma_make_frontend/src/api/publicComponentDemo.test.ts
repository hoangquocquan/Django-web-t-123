import assert from "node:assert/strict"
import { readFile } from "node:fs/promises"
import { test } from "node:test"

import { askPublicComponentDemo, publicComponentDemoAvailable } from "./aiDemo.ts"

test("public demo availability and chat requests never send an admin token", async () => {
  const originalFetch = globalThis.fetch
  const requests: Array<{ url: string; method: string; authorization: string | null; body: string | null }> = []
  globalThis.fetch = async (input, init) => {
    requests.push({
      url: String(input),
      method: init?.method ?? "GET",
      authorization: new Headers(init?.headers).get("authorization"),
      body: init?.body ? String(init.body) : null,
    })
    return new Response(JSON.stringify({
      success: true,
      data: requests.length === 1
        ? { enabled: true }
        : {
            answer: "Housing 0011 uses SUS316.",
            status: "SUPPORTED",
            sources: [{ title: "[SYNTHETIC DEMO] Housing 0011", product_code: "SYN-RAG-0011" }],
          },
    }), { status: 200, headers: { "content-type": "application/json" } })
  }
  try {
    assert.equal(await publicComponentDemoAvailable(), true)
    const answer = await askPublicComponentDemo("Which product uses SUS316?")
    assert.equal(answer.sources[0].product_code, "SYN-RAG-0011")
  } finally {
    globalThis.fetch = originalFetch
  }

  assert.deepEqual(requests.map(({ url, method, authorization }) => ({ url, method, authorization })), [
    { url: "/api/v1/public/ai-component-demo/", method: "GET", authorization: null },
    { url: "/api/v1/public/ai-component-demo/", method: "POST", authorization: null },
  ])
  assert.deepEqual(JSON.parse(requests[1].body ?? ""), { message: "Which product uses SUS316?" })
})

test("homepage mounts a gated responsive widget without exposing internal diagnostics", async () => {
  const app = await readFile(new URL("../App.tsx", import.meta.url), "utf8")
  const widget = await readFile(new URL("../components/PublicComponentChatWidget.tsx", import.meta.url), "utf8")

  assert.match(app, /function Home[\s\S]*<PublicComponentChatWidget \/>[\s\S]*function Products/)
  assert.match(widget, /publicComponentDemoAvailable/)
  assert.match(widget, /Mở AI Component Assistant/)
  assert.match(widget, /Đóng trợ lý AI/)
  assert.match(widget, /max-w-\[calc\(100vw-2rem\)\]/)
  assert.match(widget, /Nguồn tham khảo/)
  assert.match(widget, /UNAVAILABLE/)
  assert.match(widget, /maxLength=\{MAX_MESSAGE_LENGTH\}/)
  assert.doesNotMatch(widget, /dangerouslySetInnerHTML|document_id|chunk_id|provider_mode|internal\/rag-chat/)
})
