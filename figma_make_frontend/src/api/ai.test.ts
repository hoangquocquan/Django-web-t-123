import assert from "node:assert/strict"
import { readFile } from "node:fs/promises"
import { test } from "node:test"

import {
  askInternalKnowledge,
  askPublicAssistant,
  requestSalesAssistance,
} from "./ai.ts"
import { InMemoryAuthSession, createCanonicalClient } from "./canonical.ts"

function jsonResponse(data: unknown, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "content-type": "application/json" },
  })
}

test("Sales AI uses only the canonical advisory endpoint", async () => {
  const session = new InMemoryAuthSession()
  session.setAccessToken("test-ai-token")
  let observedUrl = ""
  let observedBody = ""
  const client = createCanonicalClient({
    baseUrl: "/api/v1/canonical/",
    auth: session,
    fetch: async (input, init) => {
      observedUrl = String(input)
      observedBody = String(init?.body)
      return jsonResponse({
        success: true,
        data: {
          action: "weekly_recommendation",
          human_approval_required: true,
          autonomous_action: false,
        },
      })
    },
  })

  const result = await requestSalesAssistance(
    client,
    "weekly_recommendation",
    {},
  )

  assert.equal(observedUrl, "/api/v1/canonical/ai/sales-assistant/")
  assert.deepEqual(JSON.parse(observedBody), {
    action: "weekly_recommendation",
    payload: {},
  })
  assert.equal(result.human_approval_required, true)
  assert.equal(result.autonomous_action, false)
})

test("internal knowledge questions stay in the canonical authenticated namespace", async () => {
  const session = new InMemoryAuthSession()
  session.setAccessToken("test-knowledge-token")
  let observedUrl = ""
  const client = createCanonicalClient({
    baseUrl: "/api/v1/canonical/",
    auth: session,
    fetch: async (input) => {
      observedUrl = String(input)
      return jsonResponse({
        success: true,
        data: { answer: "Grounded", sources: [] },
      })
    },
  })

  const result = await askInternalKnowledge(client, "Inspection process?")

  assert.equal(observedUrl, "/api/v1/canonical/ai/knowledge-assistant/")
  assert.equal(result.answer, "Grounded")
})

test("public assistant uses one exact root-relative endpoint and requires public scope", async () => {
  let observedUrl = ""
  const result = await askPublicAssistant("Can you machine SUS304?", {
    fetch: async (input) => {
      observedUrl = String(input)
      return jsonResponse({
        success: true,
        data: {
          answer: "Public answer",
          sources: [],
          scope: "public_knowledge_only",
          contact_recommended: true,
        },
      })
    },
  })

  assert.equal(observedUrl, "/api/v1/public/ai/assistant/")
  assert.equal(result.scope, "public_knowledge_only")
})

test("AI interface sources keep tokens memory-only and show human approval boundaries", async () => {
  const sources = await Promise.all(
    [
      new URL("../components/AiSalesWorkspace.tsx", import.meta.url),
      new URL("../components/KnowledgeAssistantWorkspace.tsx", import.meta.url),
      new URL("../components/PublicAiChat.tsx", import.meta.url),
    ].map((url) => readFile(url, "utf8")),
  )
  const combined = sources.join("\n")
  assert.doesNotMatch(
    combined,
    /localStorage|sessionStorage|indexedDB|document\.cookie/,
  )
  assert.match(
    combined,
    /Mọi email, thay đổi CRM và báo giá đều cần con\s+người duyệt/,
  )
  assert.match(combined, /Chỉ sử dụng thông tin công khai/)
})
