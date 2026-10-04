import {
  CanonicalClientError,
  MAX_REQUEST_TIMEOUT_MS,
  type AuthSession,
} from "../api/canonical.ts"
import {
  ADMIN_QUERY_CONTRACTS,
  clampAdminPageSize,
} from "../hooks/useAdminTableQuery.ts"
import type {
  AdminCollection,
  AdminCustomer,
  AdminInventoryItem,
  AdminOrder,
  AdminProduct,
  AdminResource,
  AdminResourceResultMap,
  AdminTableQuery,
  AdminTransaction,
  AdminWorkflow,
} from "../types/admin.ts"

const DEFAULT_ADMIN_API_BASE_URL = "/api/v1/admin/"
const RESOURCE_PATHS: Record<AdminResource, string> = {
  products: "products/",
  customers: "customers/",
  inventory: "inventory/items/",
  orders: "orders/",
  workflows: "workflows/",
  transactions: "transactions/",
}
type Options = {
  auth: AuthSession
  baseUrl?: string
  fetch?: typeof fetch
  timeoutMs?: number
}
type ApiPage = {
  count: number
  limit: number
  offset: number
  next_offset: number | null
  results: unknown[]
}
function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value)
}
function invalid(field = "response") {
  return new CanonicalClientError({
    kind: "protocol",
    code: "invalid_admin_response",
    message: `The server returned an invalid admin ${field}.`,
  })
}
function string(value: unknown, field: string) {
  if (typeof value !== "string") throw invalid(field)
  return value
}
function number(value: unknown, field: string) {
  if (typeof value !== "number" || !Number.isFinite(value)) throw invalid(field)
  return value
}
function nullableString(value: unknown, field: string) {
  return value === null ? null : string(value, field)
}
function baseUrl(configured?: string): string {
  const value = configured?.trim() || DEFAULT_ADMIN_API_BASE_URL
  if (/\s|\\|[?#]/.test(value) || value.startsWith("//"))
    throw new CanonicalClientError({
      kind: "protocol",
      code: "invalid_admin_api_base_url",
      message: "The admin API base URL is invalid.",
    })
  if (/^https?:\/\//i.test(value)) {
    const url = new URL(value)
    if (
      url.username ||
      url.password ||
      url.pathname.replace(/\/+$/, "") !== "/api/v1/admin"
    )
      throw new CanonicalClientError({
        kind: "protocol",
        code: "invalid_admin_api_base_url",
        message: "The admin API base URL must target /api/v1/admin/.",
      })
    url.pathname = "/api/v1/admin/"
    return url.toString()
  }
  if (value.replace(/\/+$/, "") !== "/api/v1/admin")
    throw new CanonicalClientError({
      kind: "protocol",
      code: "invalid_admin_api_base_url",
      message: "The admin API base URL must target /api/v1/admin/.",
    })
  return DEFAULT_ADMIN_API_BASE_URL
}
function page(value: unknown): ApiPage {
  if (!isRecord(value) || value.success !== true || !isRecord(value.data))
    throw invalid()
  const p = value.data
  if (
    typeof p.count !== "number" ||
    typeof p.limit !== "number" ||
    typeof p.offset !== "number" ||
    (p.next_offset !== null && typeof p.next_offset !== "number") ||
    !Array.isArray(p.results)
  )
    throw invalid("page")
  return p as unknown as ApiPage
}
function product(value: unknown): AdminProduct {
  if (!isRecord(value)) throw invalid("product")
  return {
    id: number(value.id, "product"),
    sku: string(value.sku, "product"),
    name: string(value.name, "product"),
    status: string(value.status, "product"),
    price: string(value.price, "product"),
    categoryName: string(value.category_name, "product"),
  }
}
function customer(value: unknown): AdminCustomer {
  if (!isRecord(value)) throw invalid("customer")
  return {
    id: number(value.id, "customer"),
    companyName: string(value.company_name, "customer"),
    contactName: string(value.contact_name, "customer"),
    country: string(value.country, "customer"),
    status: string(value.status, "customer"),
  }
}
function inventory(value: unknown): AdminInventoryItem {
  if (
    !isRecord(value) ||
    !isRecord(value.product) ||
    !isRecord(value.warehouse)
  )
    throw invalid("inventory item")
  return {
    id: number(value.id, "inventory item"),
    productName: string(value.product.name, "inventory item"),
    warehouseName: string(value.warehouse.name, "inventory item"),
    quantity: string(value.quantity, "inventory item"),
    reservedQuantity: string(value.reserved_quantity, "inventory item"),
    reorderPoint: string(value.reorder_point, "inventory item"),
  }
}
function order(value: unknown): AdminOrder {
  if (!isRecord(value)) throw invalid("order")
  return {
    id: number(value.id, "order"),
    orderNumber: string(value.order_number, "order"),
    customerName: string(value.customer_name, "order"),
    projectName: string(value.project_name, "order"),
    status: string(value.status, "order"),
    totalAmount: string(value.total_amount, "order"),
  }
}
function workflow(value: unknown): AdminWorkflow {
  if (!isRecord(value)) throw invalid("workflow")
  return {
    id: number(value.id, "workflow"),
    orderId: number(value.order_id, "workflow"),
    requestedStatus: string(value.requested_status, "workflow"),
    decision: string(value.decision, "workflow"),
    requestedBy: string(value.requested_by, "workflow"),
    reviewedBy: string(value.reviewed_by, "workflow"),
  }
}
function transaction(value: unknown): AdminTransaction {
  if (!isRecord(value)) throw invalid("transaction")
  return {
    id: number(value.id, "transaction"),
    entityType: string(value.entity_type, "transaction"),
    entityId: string(value.entity_id, "transaction"),
    action: string(value.action, "transaction"),
    actor: string(value.actor, "transaction"),
    createdAt: nullableString(value.created_at, "transaction"),
  }
}
const PARSERS: {
  [R in AdminResource]: (value: unknown) => AdminResourceResultMap[R]
} = {
  products: product,
  customers: customer,
  inventory,
  orders: order,
  workflows: workflow,
  transactions: transaction,
}

export function serializeAdminQuery<R extends AdminResource>(
  resource: R,
  query: AdminTableQuery<R>,
): string {
  const currentPage = Math.max(1, Math.trunc(query.page) || 1)
  const size = clampAdminPageSize(query.pageSize)
  const params = new URLSearchParams({
    limit: String(size),
    offset: String((currentPage - 1) * size),
  })
  if (query.search.trim()) params.set("search", query.search.trim())
  const orderField = query.ordering.startsWith("-")
    ? query.ordering.slice(1)
    : query.ordering
  if (
    orderField &&
    (ADMIN_QUERY_CONTRACTS[resource].ordering as readonly string[]).includes(
      orderField,
    )
  )
    params.set("ordering", query.ordering)
  for (const key of ADMIN_QUERY_CONTRACTS[resource].filters) {
    const value = (query.filters as Record<string, string | undefined>)[
      key
    ]?.trim()
    if (value) params.set(key, value)
  }
  return params.toString()
}
function httpError(status: number, payload: unknown) {
  const error =
    isRecord(payload) && isRecord(payload.error) ? payload.error : null
  const code =
    error && typeof error.code === "string"
      ? error.code
      : "admin_request_failed"
  const kind =
    status === 400
      ? "validation"
      : status === 401
        ? "authentication"
        : status === 403
          ? "permission"
          : "server"
  return new CanonicalClientError({
    kind,
    code,
    message:
      status === 400
        ? "The admin query is invalid."
        : status === 401
          ? "The admin session is not authenticated."
          : status === 403
            ? "The admin request is not permitted."
            : "The admin service is unavailable.",
    status,
  })
}

export function createAdminApi(options: Options) {
  const fetcher = options.fetch ?? globalThis.fetch
  const root = baseUrl(options.baseUrl)
  const timeoutMs = options.timeoutMs ?? 10_000
  if (
    !Number.isFinite(timeoutMs) ||
    timeoutMs < 1 ||
    timeoutMs > MAX_REQUEST_TIMEOUT_MS
  )
    throw new CanonicalClientError({
      kind: "protocol",
      code: "invalid_timeout",
      message: `Request timeout must be between 1 and ${MAX_REQUEST_TIMEOUT_MS} milliseconds.`,
    })
  async function list<R extends AdminResource>(
    resource: R,
    query: AdminTableQuery<R>,
    signal?: AbortSignal,
  ): Promise<AdminCollection<AdminResourceResultMap[R]>> {
    const token = options.auth.getAccessToken()
    if (!token)
      throw new CanonicalClientError({
        kind: "authentication",
        code: "missing_access_token",
        message: "An authenticated admin session is required.",
      })
    if (signal?.aborted)
      throw new CanonicalClientError({
        kind: "cancelled",
        code: "request_cancelled",
        message: "The request was cancelled.",
      })
    const controller = new AbortController()
    const reason: { current: "cancelled" | "timeout" } = {
      current: "cancelled",
    }
    const cancel = () => {
      reason.current = "cancelled"
      controller.abort()
    }
    signal?.addEventListener("abort", cancel, { once: true })
    const timer = setTimeout(() => {
      reason.current = "timeout"
      controller.abort()
    }, timeoutMs)
    try {
      const response = await fetcher(
        `${root}${RESOURCE_PATHS[resource]}?${serializeAdminQuery(resource, query)}`,
        {
          headers: { authorization: `Bearer ${token}` },
          signal: controller.signal,
        },
      )
      let payload: unknown
      try {
        payload = await response.json()
      } catch {
        throw invalid()
      }
      if (!response.ok) throw httpError(response.status, payload)
      const parsed = page(payload)
      const parser = PARSERS[resource]
      return {
        count: parsed.count,
        limit: parsed.limit,
        offset: parsed.offset,
        nextOffset: parsed.next_offset,
        results: parsed.results.map(parser),
      }
    } catch (error) {
      if (error instanceof CanonicalClientError) throw error
      if (controller.signal.aborted)
        throw new CanonicalClientError({
          kind: reason.current,
          code:
            reason.current === "timeout"
              ? "request_timeout"
              : "request_cancelled",
          message:
            reason.current === "timeout"
              ? "The request timed out."
              : "The request was cancelled.",
        })
      throw new CanonicalClientError({
        kind: "network",
        code: "network_error",
        message: "The server could not be reached.",
      })
    } finally {
      clearTimeout(timer)
      signal?.removeEventListener("abort", cancel)
    }
  }
  return {
    list,
    getProducts: (q: AdminTableQuery<"products">, s?: AbortSignal) =>
      list("products", q, s),
    getCustomers: (q: AdminTableQuery<"customers">, s?: AbortSignal) =>
      list("customers", q, s),
    getInventory: (q: AdminTableQuery<"inventory">, s?: AbortSignal) =>
      list("inventory", q, s),
    getOrders: (q: AdminTableQuery<"orders">, s?: AbortSignal) =>
      list("orders", q, s),
    getWorkflows: (q: AdminTableQuery<"workflows">, s?: AbortSignal) =>
      list("workflows", q, s),
    getTransactions: (q: AdminTableQuery<"transactions">, s?: AbortSignal) =>
      list("transactions", q, s),
  }
}
export type AdminApi = ReturnType<typeof createAdminApi>
