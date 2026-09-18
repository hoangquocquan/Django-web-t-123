import {
  CanonicalClientError,
  type CanonicalSuccessEnvelope,
  type createCanonicalClient,
} from "./canonical.ts"

export type CanonicalClient = ReturnType<typeof createCanonicalClient>

export type SalesAiAction = "lead_analysis" | "email_draft" | "weekly_recommendation"

export type SalesAiResult = {
  action: string
  analysis?: string
  recommendations?: string[]
  draft?: {
    subject?: string
    body?: string
  }
  leads_to_contact?: Array<{
    id: number
    company: string
    contact_person: string
  }>
  human_approval_required: boolean
  autonomous_action: boolean
  safety_note?: string
}

export type KnowledgeSource = {
  id: number | null
  title: string
  description?: string
  category?: string | null
  relevance_score?: number
}

export type KnowledgeAiResult = {
  answer: string
  sources: KnowledgeSource[]
  confidence?: number
  warning?: string
  generation_status?: string
  scope?: "public_knowledge_only"
  contact_recommended?: boolean
}

export async function requestSalesAssistance(
  client: CanonicalClient,
  action: SalesAiAction,
  payload: Record<string, unknown>,
  signal?: AbortSignal,
): Promise<SalesAiResult> {
  return client.request<SalesAiResult>("ai/sales-assistant/", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ action, payload }),
    signal,
    timeoutMs: 30_000,
  })
}

export async function askInternalKnowledge(
  client: CanonicalClient,
  question: string,
  signal?: AbortSignal,
): Promise<KnowledgeAiResult> {
  return client.request<KnowledgeAiResult>("ai/knowledge-assistant/", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ question, limit: 5 }),
    signal,
    timeoutMs: 30_000,
  })
}

function isKnowledgeResult(value: unknown): value is KnowledgeAiResult {
  if (typeof value !== "object" || value === null) return false
  const item = value as Record<string, unknown>
  return (
    typeof item.answer === "string" &&
    Array.isArray(item.sources) &&
    item.scope === "public_knowledge_only"
  )
}

export async function askPublicAssistant(
  question: string,
  options: {
    fetch?: typeof globalThis.fetch
    signal?: AbortSignal
  } = {},
): Promise<KnowledgeAiResult> {
  const fetchImplementation = options.fetch ?? globalThis.fetch
  let response: Response
  try {
    response = await fetchImplementation("/api/v1/public/ai/assistant/", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ question }),
      signal: options.signal,
    })
  } catch {
    throw new CanonicalClientError({
      kind: options.signal?.aborted ? "cancelled" : "network",
      code: options.signal?.aborted ? "request_cancelled" : "network_error",
      message: "The public assistant is unavailable.",
    })
  }

  let payload: unknown
  try {
    payload = await response.json()
  } catch {
    throw new CanonicalClientError({
      kind: "protocol",
      code: "invalid_response_envelope",
      message: "The public assistant returned an invalid response.",
      status: response.status,
    })
  }
  const envelope = payload as CanonicalSuccessEnvelope<unknown>
  if (
    !response.ok ||
    envelope?.success !== true ||
    !isKnowledgeResult(envelope.data)
  ) {
    throw new CanonicalClientError({
      kind: response.status === 429 ? "server" : "protocol",
      code:
        response.status === 429
          ? "ai_rate_limited"
          : "invalid_response_envelope",
      message:
        response.status === 429
          ? "The public assistant is receiving too many requests."
          : "The public assistant returned an invalid response.",
      status: response.status,
    })
  }
  return envelope.data
}
