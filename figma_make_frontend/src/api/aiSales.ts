import type { createCanonicalClient } from "./canonical.ts"

export type AiSalesStatus =
  | "SUPPORTED"
  | "NEEDS_MORE_INFORMATION"
  | "UNAVAILABLE"

export type AiSalesPriority = "HIGH" | "MEDIUM" | "LOW" | "NEEDS_REVIEW"

export type AiSalesAnalyzeInput = {
  rfq_id?: number
  customer_name?: string
  request?: string
  material?: string
  quantity?: number
  process?: string
  tolerance?: string
  surface_treatment?: string
  drawing_available?: boolean | null
  deadline?: string
}

export type AiSalesSource = {
  id: number | string
  title: string
  product_code: string
  citation: string
  version?: number | null
  revision?: string | null
  relevance_score: number
}

export type AiSalesAnalysis = {
  status: AiSalesStatus
  summary: string
  priority: AiSalesPriority
  priority_reasons: string[]
  matched_products: Array<{
    product_code: string
    title: string
    reason: string
    source_id: number | string
  }>
  recommended_next_action: string
  recommended_next_action_reason: string
  draft_response: string
  risks: string[]
  missing_information: string[]
  sources: AiSalesSource[]
  input_reference: string
  synthetic_input: boolean
  human_approval_required: true
  autonomous_action: false
  safety_note: string
  request_id: string
}

type CanonicalClient = ReturnType<typeof createCanonicalClient>

export function analyzeAiSales(
  client: CanonicalClient,
  input: AiSalesAnalyzeInput,
  signal?: AbortSignal,
) {
  return client.request<AiSalesAnalysis>("internal/ai-sales/analyze/", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(input),
    signal,
    timeoutMs: 180_000,
  })
}
