import assert from "node:assert/strict"
import { readFile } from "node:fs/promises"
import { test } from "node:test"

import { askSyntheticRagChat } from "./aiDemo.ts"

test("RAG chat posts a bounded message with bearer auth", async () => {
  const originalFetch = globalThis.fetch
  let requestUrl = ""
  let requestBody = ""
  let authorization = ""
  globalThis.fetch = async (input, init) => {
    requestUrl = String(input)
    requestBody = String(init?.body)
    authorization = new Headers(init?.headers).get("authorization") ?? ""
    return new Response(JSON.stringify({
      success: true,
      data: {
        question: "Find SUS316",
        answer: "Housing 0011",
        status: "SUPPORTED",
        sources: [],
        retrieval: { dataset_id: "rag_synthetic_demo_v1" },
      },
    }), { status: 200, headers: { "content-type": "application/json" } })
  }
  try {
    const result = await askSyntheticRagChat("session-token", "Find SUS316")
    assert.equal(result.question, "Find SUS316")
  } finally {
    globalThis.fetch = originalFetch
  }

  assert.equal(requestUrl, "/api/v1/internal/rag-chat/")
  assert.equal(authorization, "Bearer session-token")
  assert.deepEqual(JSON.parse(requestBody), { message: "Find SUS316" })
})

test("chat page provides session history, loading, citations and unavailable state", async () => {
  const component = await readFile(new URL("../components/RagChatPage.tsx", import.meta.url), "utf8")
  const app = await readFile(new URL("../App.tsx", import.meta.url), "utf8")

  assert.match(app, /admin-ai-chat/)
  assert.match(app, /<RagChatPage/)
  assert.match(component, /AI Component Assistant/)
  assert.match(component, /aria-label="Chat message"/)
  assert.match(component, /Đang truy xuất context/)
  assert.match(component, /Nguồn tham khảo/)
  assert.match(component, /UNAVAILABLE/)
  assert.match(component, /MAX_MESSAGE_LENGTH = 1200/)
  assert.match(component, /Thời tiết Tokyo hôm nay thế nào/)
  assert.doesNotMatch(component, /dangerouslySetInnerHTML/)
})

