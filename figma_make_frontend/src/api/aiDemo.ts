import { CanonicalClientError } from "./canonical.ts"

const DEFAULT_AI_API_BASE_URL = "/api/v1/"
const DEFAULT_AI_REQUEST_TIMEOUT_MS = 180_000

type SuccessEnvelope<T,> = {
  success: true
  data: T
}

type ErrorEnvelope = {
  success: false
  error: {
    code: string
    message: string
    details?: unknown
  }
}

export type RagDemoSource = {
  title: string
  product_code: string
  citation: string
  document_id: number
  version: number
  revision: string
  chunk_id: number
  relevance_score: number
}

export type RagDemoResult = {
  answer: string
  status: "SUPPORTED" | "UNAVAILABLE"
  sources: RagDemoSource[]
  retrieval: {
    result_count: number
    candidate_chunks_considered: number
    provider: string
    provider_mode: "development-hash-plus-lexical" | "semantic-embedding" | string
    dataset_id: "rag_synthetic_demo_v1" | string
    corpus_documents: number
    confidence?: number
    generation_provider?: string
    generation_status?: string
    latency_ms?: number
    llm_success?: boolean
    fallback_used?: boolean
  }
}

export type AiRequestOptions = {
  signal?: AbortSignal
  timeoutMs?: number
}

function viteEnvValue(name: string): string | undefined {
  return (import.meta as { env?: Record<string, string | undefined> }).env?.[
    name
  ]
}

function aiApiBaseUrl(configured = viteEnvValue("VITE_API_BASE_URL")): string {
  const value = configured?.trim()
  if (!value) return DEFAULT_AI_API_BASE_URL
  if (/[\s\\]/.test(value) || value.startsWith("//") || /[?#]/.test(value)) {
    throw new CanonicalClientError({
      kind: "protocol",
      code: "invalid_ai_api_base_url",
      message: "The AI API root URL is invalid.",
    })
  }
  if (/^https?:\/\//i.test(value)) {
    const url = new URL(value)
    if (url.username || url.password) {
      throw new CanonicalClientError({
        kind: "protocol",
        code: "invalid_ai_api_base_url",
        message: "The AI API root URL is invalid.",
      })
    }
    url.pathname = `${url.pathname.replace(/\/+$/, "")}/api/v1/`
    return url.toString()
  }
  return `${value.replace(/\/+$/, "")}/api/v1/`
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value)
}

function isSuccessEnvelope<T,>(value: unknown): value is SuccessEnvelope<T> {
  return isRecord(value) && value.success === true && "data" in value
}

function isErrorEnvelope(value: unknown): value is ErrorEnvelope {
  return (
    isRecord(value) &&
    value.success === false &&
    isRecord(value.error) &&
    typeof value.error.code === "string" &&
    typeof value.error.message === "string"
  )
}

function errorKind(status: number) {
  if (status === 401) return "authentication"
  if (status === 403) return "permission"
  if (status === 400) return "validation"
  if (status === 404) return "not_found"
  return "server"
}

async function parseJson(response: Response): Promise<unknown> {
  try {
    return await response.json()
  } catch {
    throw new CanonicalClientError({
      kind: "protocol",
      code: "invalid_response_envelope",
      message: "The server returned an invalid response envelope.",
      status: response.status,
    })
  }
}

async function boundedFetch(
  fetchImplementation: typeof fetch,
  url: string,
  init: RequestInit,
  timeoutMs: number,
): Promise<Response> {
  const controller = new AbortController()
  let timeout: ReturnType<typeof setTimeout> | null = null
  const externalSignal = init.signal

  if (externalSignal?.aborted) {
    throw new CanonicalClientError({
      kind: "cancelled",
      code: "request_cancelled",
      message: "The request was cancelled.",
    })
  }

  const cancelFromCaller = () => controller.abort()
  externalSignal?.addEventListener("abort", cancelFromCaller, { once: true })
  try {
    timeout = setTimeout(() => controller.abort(), timeoutMs)
    return await fetchImplementation(url, {
      ...init,
      signal: controller.signal,
    })
  } catch (error) {
    if (error instanceof CanonicalClientError) throw error
    throw new CanonicalClientError({
      kind: controller.signal.aborted ? "timeout" : "network",
      code: controller.signal.aborted ? "request_timeout" : "network_error",
      message: controller.signal.aborted
        ? "The request timed out."
        : "The server could not be reached.",
    })
  } finally {
    if (timeout !== null) clearTimeout(timeout)
    externalSignal?.removeEventListener("abort", cancelFromCaller)
  }
}

async function postAi<T,>(
  path: string,
  token: string,
  body: unknown,
  options: AiRequestOptions = {},
): Promise<T> {
  const response = await boundedFetch(
    globalThis.fetch,
    `${aiApiBaseUrl()}${path}`,
    {
      method: "POST",
      headers: {
        authorization: `Bearer ${token}`,
        "content-type": "application/json",
      },
      body: JSON.stringify(body),
      signal: options.signal,
    },
    options.timeoutMs ?? DEFAULT_AI_REQUEST_TIMEOUT_MS,
  )
  const payload = await parseJson(response)
  if (response.ok && isSuccessEnvelope<T>(payload)) return payload.data
  if (!response.ok && isErrorEnvelope(payload)) {
    throw new CanonicalClientError({
      kind: errorKind(response.status),
      code: payload.error.code,
      message: payload.error.message,
      status: response.status,
      details: payload.error.details,
    })
  }
  throw new CanonicalClientError({
    kind: "protocol",
    code: "invalid_response_envelope",
    message: "The server returned an invalid response envelope.",
    status: response.status,
  })
}

export function postInternalAi<T,>(
  path: string,
  token: string,
  body: unknown,
  options?: AiRequestOptions,
) {
  return postAi<T>(path, token, body, options)
}

export function askSyntheticRagDemo(
  token: string,
  question: string,
  options?: AiRequestOptions,
) {
  return postAi<RagDemoResult>(
    "internal/rag-demo/query/",
    token,
    { question },
    options,
  )
}

export type RagChatResult = RagDemoResult & {
  question: string
}

export function askSyntheticRagChat(
  token: string,
  message: string,
  options?: AiRequestOptions,
) {
  return postAi<RagChatResult>(
    "internal/rag-chat/",
    token,
    { message },
    options,
  )
}

export type AiKnowledgeSource = {
  id?: number | string | null
  title?: string
  relevance_score?: number
}

export type KnowledgeChatResult = {
  answer: string
  sources: AiKnowledgeSource[]
  confidence: number
  warning: string
  model: string
  provider: "ollama-local" | "source-fallback" | string
  response_time_ms: number
  generation_status: string
  source_relevance_score: number
  hallucination_warning: string
  publication_state?: "isolated_demo_unapproved" | "public_sources_only" | string
}

export type PublicComponentDemoResult = {
  answer: string
  status: "SUPPORTED" | "UNAVAILABLE"
  sources: Array<{ title: string; product_code: string }>
}

async function postPublicAi<T,>(
  path: string,
  body: unknown,
  options: AiRequestOptions = {},
): Promise<T> {
  const response = await boundedFetch(
    globalThis.fetch,
    `${aiApiBaseUrl()}${path}`,
    {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(body),
      signal: options.signal,
    },
    options.timeoutMs ?? DEFAULT_AI_REQUEST_TIMEOUT_MS,
  )
  const payload = await parseJson(response)
  if (response.ok && isSuccessEnvelope<T>(payload)) return payload.data
  if (!response.ok && isErrorEnvelope(payload)) {
    throw new CanonicalClientError({
      kind: errorKind(response.status),
      code: payload.error.code,
      message: payload.error.message,
      status: response.status,
      details: payload.error.details,
    })
  }
  throw new CanonicalClientError({
    kind: "protocol",
    code: "invalid_response_envelope",
    message: "The server returned an invalid response envelope.",
    status: response.status,
  })
}

export async function publicComponentDemoAvailable(
  options: AiRequestOptions = {},
): Promise<boolean> {
  const response = await boundedFetch(
    globalThis.fetch,
    `${aiApiBaseUrl()}public/ai-component-demo/`,
    { method: "GET", signal: options.signal },
    options.timeoutMs ?? DEFAULT_AI_REQUEST_TIMEOUT_MS,
  )
  if (response.status === 404) return false
  const payload = await parseJson(response)
  if (response.ok && isSuccessEnvelope<{ enabled: boolean }>(payload)) {
    return payload.data.enabled === true
  }
  return false
}

export function askPublicComponentDemo(
  message: string,
  options?: AiRequestOptions,
) {
  return postPublicAi<PublicComponentDemoResult>(
    "public/ai-component-demo/",
    { message },
    options,
  )
}

export function askPublicKnowledgeAssistant(
  question: string,
  limit = 5,
  options?: AiRequestOptions,
) {
  return postPublicAi<KnowledgeChatResult>(
    "public/ai/assistant/",
    { question, limit },
    options,
  )
}
