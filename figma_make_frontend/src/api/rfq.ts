import {
  CanonicalClientError,
  type createCanonicalClient,
} from "./canonical.ts"

export type CanonicalPage<T,> = {
  count: number
  limit: number
  offset: number
  next_offset: number | null
  previous_offset: number | null
  results: T[]
}

export type CanonicalRfq = {
  id: number
  data_contract: string
  rfq_number: string
  quotation_family_number: string | null
  customer_id: number
  status: string | null
  project_name: string
  notes: string
  quote_due_at: string | null
  required_delivery_date: string | null
  assigned_to_id: number | null
  closure_reason: string
  created_by_id: number | null
  updated_by_id: number | null
  created_at: string | null
  updated_at: string | null
  compatibility: Record<string, unknown> | null
}

export type CanonicalRfqPage = CanonicalPage<CanonicalRfq>

export type RfqTableRow = [string, string, string, string, string]

type SimpleRfqViewStatus = "unauthenticated" | "loading" | "permission_denied" | "timeout" | "network" | "protocol" | "server"

type SimpleRfqViewState = {
  status: SimpleRfqViewStatus
}

type LoadedRfqViewState = {
  status: "populated" | "empty"
  page: CanonicalRfqPage
}

export type RfqViewState = SimpleRfqViewState | LoadedRfqViewState

export type RfqClient = ReturnType<typeof createCanonicalClient>

export function rfqListPath(): string {
  return "rfqs/?limit=20&ordering=-created_at"
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value)
}

export function isCanonicalRfq(value: unknown): value is CanonicalRfq {
  return (
    isRecord(value) &&
    typeof value.id === "number" &&
    typeof value.data_contract === "string" &&
    typeof value.rfq_number === "string" &&
    (typeof value.quotation_family_number === "string" ||
      value.quotation_family_number === null) &&
    typeof value.customer_id === "number" &&
    (typeof value.status === "string" || value.status === null) &&
    typeof value.project_name === "string" &&
    typeof value.notes === "string" &&
    (typeof value.quote_due_at === "string" || value.quote_due_at === null) &&
    (typeof value.required_delivery_date === "string" ||
      value.required_delivery_date === null) &&
    (typeof value.assigned_to_id === "number" ||
      value.assigned_to_id === null) &&
    typeof value.closure_reason === "string" &&
    (typeof value.created_by_id === "number" || value.created_by_id === null) &&
    (typeof value.updated_by_id === "number" || value.updated_by_id === null) &&
    (typeof value.created_at === "string" || value.created_at === null) &&
    (typeof value.updated_at === "string" || value.updated_at === null) &&
    (value.compatibility === null || isRecord(value.compatibility))
  )
}

export function isCanonicalRfqPage(value: unknown): value is CanonicalRfqPage {
  return (
    isRecord(value) &&
    typeof value.count === "number" &&
    typeof value.limit === "number" &&
    typeof value.offset === "number" &&
    (typeof value.next_offset === "number" || value.next_offset === null) &&
    (typeof value.previous_offset === "number" ||
      value.previous_offset === null) &&
    Array.isArray(value.results) &&
    value.results.every(isCanonicalRfq)
  )
}

export async function fetchRfqPage(
  client: RfqClient,
  signal?: AbortSignal,
): Promise<CanonicalRfqPage> {
  const page = await client.request<CanonicalRfqPage>(rfqListPath(), { signal })
  if (!isCanonicalRfqPage(page)) {
    throw new CanonicalClientError({
      kind: "protocol",
      code: "invalid_rfq_page",
      message: "The server returned an invalid RFQ page.",
    })
  }
  return page
}

export function rfqRows(page: CanonicalRfqPage): RfqTableRow[] {
  return page.results.map((rfq) => [
    rfq.rfq_number,
    `Customer #${rfq.customer_id}`,
    rfq.quote_due_at ?? "Chưa có hạn",
    rfq.project_name || "Không tên",
    rfq.status ?? "LEGACY",
  ])
}

export function rfqStateFromError(error: CanonicalClientError): RfqViewState {
  if (error.kind === "authentication") return { status: "unauthenticated" }
  if (error.kind === "permission") return { status: "permission_denied" }
  if (error.kind === "timeout") return { status: "timeout" }
  if (error.kind === "network") return { status: "network" }
  if (error.kind === "protocol") return { status: "protocol" }
  return { status: "server" }
}

export function rfqStatusText(state: RfqViewState): string {
  switch (state.status) {
    case "unauthenticated":
      return "Đăng nhập để xem RFQ canonical."
    case "loading":
      return "Đang tải RFQ..."
    case "empty":
      return "Chưa có RFQ canonical."
    case "permission_denied":
      return "Bạn không có quyền xem RFQ."
    case "timeout":
      return "Yêu cầu RFQ đã hết thời gian chờ."
    case "network":
      return "Không thể kết nối máy chủ RFQ."
    case "protocol":
      return "Phản hồi RFQ không đúng hợp đồng canonical."
    case "server":
      return "Máy chủ chưa thể trả danh sách RFQ."
    case "populated":
      return `${state.page.count} RFQ canonical`
  }
}

export function createLatestRequestGuard() {
  let latest = 0
  return {
    next() {
      latest += 1
      return latest
    },
    isLatest(requestId: number) {
      return requestId === latest
    },
  }
}
