import { postInternalAi } from "./aiDemo.ts"

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

export function analyzeAiSales(
  token: string,
  input: AiSalesAnalyzeInput,
  signal?: AbortSignal,
) {
  return postInternalAi<AiSalesAnalysis>(
    "internal/ai-sales/analyze/",
    token,
    input,
    { signal, timeoutMs: 30_000 },
  )
}
