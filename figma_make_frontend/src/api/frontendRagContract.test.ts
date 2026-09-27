import assert from "node:assert/strict"
import { readFile } from "node:fs/promises"
import { test } from "node:test"

import { askSyntheticRagDemo } from "./aiDemo.ts"

test("production frontend exposes only authenticated internal RAG navigation", async () => {
  const app = await readFile(new URL("../App.tsx", import.meta.url), "utf8")
  const client = await readFile(new URL("./aiDemo.ts", import.meta.url), "utf8")

  assert.doesNotMatch(
    app,
    /\"chatbot\"|PublicChatbotPage|PublicComponentChatWidget|public\/ai\/assistant|public\/ai-component-demo/,
  )
  assert.doesNotMatch(app, /localStorage|sessionStorage/)
  assert.match(app, /admin-ai-chat/)
  assert.match(app, /admin-rag-demo/)
  assert.match(client, /internal\/rag-chat\//)
  assert.match(client, /internal\/rag-demo\/query\//)
  assert.doesNotMatch(
    client,
    /askPublicKnowledgeAssistant|askPublicComponentDemo|publicComponentDemoAvailable/,
  )
})

test("permission failures remain explicit instead of falling back to public access", async () => {
  const originalFetch = globalThis.fetch
  globalThis.fetch = async () =>
    new Response(
      JSON.stringify({
        success: false,
        error: { code: "forbidden", message: "Insufficient scope." },
      }),
      { status: 403, headers: { "content-type": "application/json" } },
    )
  try {
    await assert.rejects(
      () => askSyntheticRagDemo("scoped-token", "question"),
      (error: unknown) =>
        error instanceof Error &&
        "kind" in error &&
        error.kind === "permission",
    )
  } finally {
    globalThis.fetch = originalFetch
  }
})
