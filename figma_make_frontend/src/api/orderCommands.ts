import {
  CanonicalClientError,
  type CanonicalErrorKind,
  type createCanonicalClient,
} from "./canonical.ts"
import {
  isQuotationSummary,
  shouldRetainQuotationAttempt,
  type CanonicalQuotationSummary,
} from "./quotationCommands.ts"
import { createLatestRequestGuard, type CanonicalPage } from "./rfq.ts"

const IDEMPOTENCY_KEY_PATTERN = /^[A-Za-z0-9._:-]{1,64}$/

export const ORDER_STATES = [
  "CONFIRMED",
  "IN_PROGRESS",
  "ON_HOLD",
  "COMPLETED",
  "CANCELLED",
] as const

export type OrderWorkflowStatus = typeof ORDER_STATES[number]
export type CanonicalClient = ReturnType<typeof createCanonicalClient>

export type CanonicalOrder = {
  id: number
  data_contract: string
  order_number: string
  source_quotation_id: number | null
  source_rfq_id: number | null
  customer_id: number | null
  workflow_status: OrderWorkflowStatus | null
  currency: string
  subtotal: string
  discount_total: string
  tax_amount: string
  total_amount: string
  ordered_at: string | null
  expected_delivery_date: string | null
  progress_percent: number
  hold_reason: string
  cancel_reason: string
  source_quotation_sent_at: string | null
  completed_at: string | null
  created_by_id: number | null
  updated_by_id: number | null
  created_at: string | null
  updated_at: string | null
  compatibility: Record<string, unknown> | null
}

export type CanonicalOrderLine = {
  id: number
  order_id: number
  data_contract: string
  line_number: number
  source_quotation_line_id: number
  part_id: number | null
  description_snapshot: string
  part_code_snapshot: string
  material_snapshot: string
  quantity: string
  unit: string
  unit_price: string
  line_total: string
  compatibility: Record<string, unknown> | null
}

export type CanonicalOrderProgress = {
  id: number
  order_id: number
  from_status: OrderWorkflowStatus | null
  to_status: OrderWorkflowStatus
  progress_percent: number
  milestone_note: string
  reason: string
  actor_id: number | null
  created_at: string | null
}

export type CanonicalAuditEvent = {
  id: number
  actor_ref: string
  actor_display: string
  action: string
  entity_type: string
  entity_id: string
  old_status: string | null
  new_status: string | null
  reason: string
  metadata: Record<string, unknown>
  correlation_id: string
  created_at: string | null
}

export type OrderWorkspaceData = {
  order: CanonicalOrder
  lines: CanonicalOrderLine[]
  progress: CanonicalOrderProgress[]
  timeline: CanonicalAuditEvent[]
}

export type OrderConversionPayload = Record<string, never>

export type OrderProgressPayload = {
  progress_percent: number
  milestone_note?: string
}

export type OrderReasonPayload = OrderProgressPayload & {
  reason: string
}

export type OrderProgressAction = "progress" | "hold" | "resume" | "complete" | "cancel"

export type OrderCommandStatus = "initial" | "loading" | "ready" | "pending" | "accepted" | "not_applied" | "ambiguous" | "validation" | "authentication_failure" | "permission_denied" | "lifecycle_conflict" | "idempotency_conflict" | "timeout" | "network" | "protocol" | "server" | "cancelled"

export type OrderCommandState = {
  status: OrderCommandStatus
  message: string
  fieldErrors?: Record<string, string>
}

export type ConversionTarget = {
  quotationId: number
  familyNumber: string
}

type ConversionAttempt = {
  target: ConversionTarget
  payload: OrderConversionPayload
  key: string
  createdOrderId: number | null
}

export type ProgressReconciliation = "applied" | "not_applied" | "ambiguous"

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value)
}

function isNullableString(value: unknown): value is string | null {
  return typeof value === "string" || value === null
}

function isNullableNumber(value: unknown): value is number | null {
  return typeof value === "number" || value === null
}

function isOrderStatus(value: unknown): value is OrderWorkflowStatus | null {
  return (
    value === null ||
    (typeof value === "string" &&
      ORDER_STATES.includes(value as OrderWorkflowStatus))
  )
}

function isPage<T>(
  value: unknown,
  guard: (item: unknown) => item is T,
): value is CanonicalPage<T> {
  return (
    isRecord(value) &&
    typeof value.count === "number" &&
    typeof value.limit === "number" &&
    typeof value.offset === "number" &&
    (typeof value.next_offset === "number" || value.next_offset === null) &&
    (typeof value.previous_offset === "number" ||
      value.previous_offset === null) &&
    Array.isArray(value.results) &&
    value.results.every(guard)
  )
}

function protocolError(code: string): never {
  throw new CanonicalClientError({
    kind: "protocol",
    code,
    message: "The server returned an invalid canonical order response.",
  })
}

function validationError(fields: Record<string, string>): never {
  throw new CanonicalClientError({
    kind: "validation",
    code: "client_validation_error",
    message: "Order command validation failed.",
    details: fields,
  })
}

function positiveInteger(value: unknown, field: string): number {
  if (!Number.isInteger(value) || Number(value) < 1) {
    validationError({ [field]: "Phải chọn bản ghi hợp lệ." })
  }
  return Number(value)
}

function nonNegativeInteger(value: unknown, field: string): number {
  if (!Number.isInteger(value) || Number(value) < 0) {
    validationError({ [field]: "Giá trị phải là số nguyên không âm." })
  }
  return Number(value)
}

function text(
  value: unknown,
  field: string,
  required = false,
  maxLength?: number,
): string {
  if (typeof value !== "string") {
    validationError({ [field]: "Giá trị văn bản không hợp lệ." })
  }
  const normalized = value.trim()
  if (required && !normalized) {
    validationError({ [field]: "Trường này là bắt buộc." })
  }
  if (maxLength !== undefined && normalized.length > maxLength) {
    validationError({ [field]: `Không vượt quá ${maxLength} ký tự.` })
  }
  return normalized
}

function rejectUnknownFields(
  input: Record<string, unknown>,
  allowed: readonly string[],
) {
  if (Object.keys(input).some((key) => !allowed.includes(key))) {
    validationError({ unknown_fields: "Có trường dữ liệu không hỗ trợ." })
  }
}

export function isCanonicalOrder(value: unknown): value is CanonicalOrder {
  return (
    isRecord(value) &&
    typeof value.id === "number" &&
    typeof value.data_contract === "string" &&
    typeof value.order_number === "string" &&
    isNullableNumber(value.source_quotation_id) &&
    isNullableNumber(value.source_rfq_id) &&
    isNullableNumber(value.customer_id) &&
    isOrderStatus(value.workflow_status) &&
    typeof value.currency === "string" &&
    typeof value.subtotal === "string" &&
    typeof value.discount_total === "string" &&
    typeof value.tax_amount === "string" &&
    typeof value.total_amount === "string" &&
    isNullableString(value.ordered_at) &&
    isNullableString(value.expected_delivery_date) &&
    Number.isInteger(value.progress_percent) &&
    typeof value.hold_reason === "string" &&
    typeof value.cancel_reason === "string" &&
    isNullableString(value.source_quotation_sent_at) &&
    isNullableString(value.completed_at) &&
    isNullableNumber(value.created_by_id) &&
    isNullableNumber(value.updated_by_id) &&
    isNullableString(value.created_at) &&
    isNullableString(value.updated_at) &&
    (value.compatibility === null || isRecord(value.compatibility))
  )
}

function isOrderLine(value: unknown): value is CanonicalOrderLine {
  return (
    isRecord(value) &&
    typeof value.id === "number" &&
    typeof value.order_id === "number" &&
    typeof value.data_contract === "string" &&
    typeof value.line_number === "number" &&
    typeof value.source_quotation_line_id === "number" &&
    isNullableNumber(value.part_id) &&
    typeof value.description_snapshot === "string" &&
    typeof value.part_code_snapshot === "string" &&
    typeof value.material_snapshot === "string" &&
    typeof value.quantity === "string" &&
    typeof value.unit === "string" &&
    typeof value.unit_price === "string" &&
    typeof value.line_total === "string" &&
    (value.compatibility === null || isRecord(value.compatibility))
  )
}

function isProgress(value: unknown): value is CanonicalOrderProgress {
  return (
    isRecord(value) &&
    typeof value.id === "number" &&
    typeof value.order_id === "number" &&
    isOrderStatus(value.from_status) &&
    isOrderStatus(value.to_status) &&
    value.to_status !== null &&
    Number.isInteger(value.progress_percent) &&
    typeof value.milestone_note === "string" &&
    typeof value.reason === "string" &&
    isNullableNumber(value.actor_id) &&
    isNullableString(value.created_at)
  )
}

function isAudit(value: unknown): value is CanonicalAuditEvent {
  return (
    isRecord(value) &&
    typeof value.id === "number" &&
    typeof value.actor_ref === "string" &&
    typeof value.actor_display === "string" &&
    typeof value.action === "string" &&
    typeof value.entity_type === "string" &&
    typeof value.entity_id === "string" &&
    isNullableString(value.old_status) &&
    isNullableString(value.new_status) &&
    typeof value.reason === "string" &&
    isRecord(value.metadata) &&
    typeof value.correlation_id === "string" &&
    isNullableString(value.created_at)
  )
}

export function orderIndexPaths() {
  return {
    orders: "orders/?data_contract=MVP_V1&limit=20&ordering=-ordered_at",
    acceptedQuotations:
      "quotations/?data_contract=MVP_V1&workflow_status=ACCEPTED&limit=20&ordering=-created_at",
  }
}

export function orderReadPaths(orderId: number) {
  const id = positiveInteger(orderId, "order_id")
  return {
    detail: `orders/${id}/`,
    lines: `orders/${id}/lines/?limit=100&ordering=line_number`,
    progress: `orders/${id}/progress/?limit=100&ordering=created_at`,
    timeline: `timelines/order/${id}/?limit=100&ordering=created_at`,
  }
}

export function globalAuditPath(offset = 0) {
  return `audit-events/?limit=20&offset=${nonNegativeInteger(offset, "offset")}&ordering=-created_at`
}

export async function fetchOrderIndex(
  client: CanonicalClient,
  signal?: AbortSignal,
): Promise<CanonicalPage<CanonicalOrder>> {
  const orders = await client.request<CanonicalPage<CanonicalOrder>>(
    orderIndexPaths().orders,
    { signal },
  )
  if (!isPage(orders, isCanonicalOrder)) protocolError("invalid_order_page")
  return orders
}

export async function fetchAcceptedQuotations(
  client: CanonicalClient,
  signal?: AbortSignal,
): Promise<CanonicalPage<CanonicalQuotationSummary>> {
  const acceptedQuotations =
    await client.request<CanonicalPage<CanonicalQuotationSummary>>(
      orderIndexPaths().acceptedQuotations,
      { signal },
    )
  if (!isPage(acceptedQuotations, isQuotationSummary)) {
    protocolError("invalid_accepted_quotation_page")
  }
  return acceptedQuotations
}

export async function fetchOrderWorkspace(
  client: CanonicalClient,
  orderId: number,
  signal?: AbortSignal,
): Promise<OrderWorkspaceData> {
  const paths = orderReadPaths(orderId)
  const order = await client.request<CanonicalOrder>(paths.detail, { signal })
  if (!isCanonicalOrder(order) || order.data_contract !== "MVP_V1") {
    protocolError("invalid_order_detail")
  }
  const [lines, progress, timeline] = await Promise.all([
    client.request<CanonicalPage<CanonicalOrderLine>>(paths.lines, { signal }),
    client.request<CanonicalPage<CanonicalOrderProgress>>(paths.progress, {
      signal,
    }),
    client.request<CanonicalPage<CanonicalAuditEvent>>(paths.timeline, {
      signal,
    }),
  ])
  if (!isPage(lines, isOrderLine)) protocolError("invalid_order_lines")
  if (!isPage(progress, isProgress)) protocolError("invalid_order_progress")
  if (!isPage(timeline, isAudit)) protocolError("invalid_order_timeline")
  return {
    order,
    lines: lines.results,
    progress: progress.results,
    timeline: timeline.results,
  }
}

export async function fetchGlobalAudit(
  client: CanonicalClient,
  offset = 0,
  signal?: AbortSignal,
) {
  const page = await client.request<CanonicalPage<CanonicalAuditEvent>>(
    globalAuditPath(offset),
    { signal },
  )
  if (!isPage(page, isAudit)) protocolError("invalid_global_audit")
  return page
}

export function validateOrderConversionPayload(
  input: unknown,
): OrderConversionPayload {
  if (!isRecord(input)) validationError({ form: "Dữ liệu không hợp lệ." })
  rejectUnknownFields(input, [])
  return {}
}

function progressPercent(value: unknown) {
  if (!Number.isInteger(value) || Number(value) < 0 || Number(value) > 100) {
    validationError({
      progress_percent: "Tiến độ phải là số nguyên từ 0 đến 100.",
    })
  }
  return Number(value)
}

export function validateOrderProgressPayload(
  input: unknown,
  action: OrderProgressAction,
): OrderProgressPayload | OrderReasonPayload {
  if (!isRecord(input)) validationError({ form: "Dữ liệu không hợp lệ." })
  const reasonAction = action === "hold" || action === "cancel"
  rejectUnknownFields(
    input,
    reasonAction
      ? ["progress_percent", "milestone_note", "reason"]
      : ["progress_percent", "milestone_note"],
  )
  const percent =
    action === "complete" && input.progress_percent === undefined
      ? 100
      : progressPercent(input.progress_percent)
  if (action === "complete" && percent !== 100) {
    validationError({ progress_percent: "Hoàn thành yêu cầu đúng 100%." })
  }
  const result: OrderProgressPayload = { progress_percent: percent }
  if (input.milestone_note !== undefined) {
    result.milestone_note = text(
      input.milestone_note,
      "milestone_note",
      false,
      240,
    )
  }
  if (!reasonAction) return result
  return {
    ...result,
    reason: text(input.reason, "reason", true),
  }
}

async function post<T>(
  client: CanonicalClient,
  path: string,
  payload: object,
  signal?: AbortSignal,
  idempotencyKey?: string,
): Promise<T> {
  const headers: Record<string, string> = {
    "content-type": "application/json",
  }
  if (idempotencyKey !== undefined) {
    if (!IDEMPOTENCY_KEY_PATTERN.test(idempotencyKey)) {
      protocolError("invalid_idempotency_key")
    }
    headers["Idempotency-Key"] = idempotencyKey
  }
  return client.request<T>(path, {
    method: "POST",
    headers,
    body: JSON.stringify(payload),
    signal,
  })
}

export async function convertQuotationToOrder(
  client: CanonicalClient,
  quotationId: number,
  payload: OrderConversionPayload,
  idempotencyKey: string,
  signal?: AbortSignal,
) {
  const order = await post<CanonicalOrder>(
    client,
    `quotations/${positiveInteger(quotationId, "quotation_id")}/commands/convert-to-order/`,
    validateOrderConversionPayload(payload),
    signal,
    idempotencyKey,
  )
  if (!isCanonicalOrder(order) || order.data_contract !== "MVP_V1") {
    protocolError("invalid_conversion_response")
  }
  return order
}

export async function postOrderProgressCommand(
  client: CanonicalClient,
  orderId: number,
  action: OrderProgressAction,
  payload: OrderProgressPayload | OrderReasonPayload,
  signal?: AbortSignal,
) {
  const validated = validateOrderProgressPayload(payload, action)
  const order = await post<CanonicalOrder>(
    client,
    `orders/${positiveInteger(orderId, "order_id")}/commands/${action}/`,
    validated,
    signal,
  )
  if (!isCanonicalOrder(order) || order.data_contract !== "MVP_V1") {
    protocolError("invalid_order_command")
  }
  return order
}

export function createOrderConversionAttemptManager(
  keyFactory: () => string = () => crypto.randomUUID(),
) {
  let active: ConversionAttempt | null = null
  return {
    begin(
      target: ConversionTarget,
      payload: OrderConversionPayload,
    ): ConversionAttempt {
      if (active !== null) return active
      const key = keyFactory()
      if (!IDEMPOTENCY_KEY_PATTERN.test(key)) {
        protocolError("invalid_idempotency_key_factory")
      }
      active = {
        target: { ...target },
        payload: { ...payload },
        key,
        createdOrderId: null,
      }
      return active
    },
    markCreated(attempt: ConversionAttempt, orderId: number) {
      if (active === attempt) {
        active.createdOrderId = positiveInteger(orderId, "order_id")
      }
    },
    fail(attempt: ConversionAttempt, error: unknown) {
      if (
        active === attempt &&
        active.createdOrderId === null &&
        !shouldRetainQuotationAttempt(error)
      ) {
        active = null
      }
    },
    complete(attempt: ConversionAttempt) {
      if (active === attempt) active = null
    },
    hasActiveAttempt() {
      return active !== null
    },
    hasCreatedOrder() {
      return active !== null && active.createdOrderId !== null
    },
    activeTarget() {
      return active === null ? null : { ...active.target }
    },
    activePayload() {
      return active === null ? null : { ...active.payload }
    },
  }
}

export async function executeOrderConversionAttempt<T>(
  client: CanonicalClient,
  manager: ReturnType<typeof createOrderConversionAttemptManager>,
  target: ConversionTarget,
  payload: OrderConversionPayload,
  reconcile: (
    orderId: number,
    target: ConversionTarget,
    signal?: AbortSignal,
  ) => Promise<T>,
  signal?: AbortSignal,
): Promise<T> {
  const attempt = manager.begin(target, payload)
  try {
    if (attempt.createdOrderId === null) {
      const order = await convertQuotationToOrder(
        client,
        attempt.target.quotationId,
        attempt.payload,
        attempt.key,
        signal,
      )
      manager.markCreated(attempt, order.id)
    }
    const result = await reconcile(
      attempt.createdOrderId!,
      attempt.target,
      signal,
    )
    manager.complete(attempt)
    return result
  } catch (error) {
    manager.fail(attempt, error)
    throw error
  }
}

export function orderLifecyclePermissions(
  role: string | null,
  status: OrderWorkflowStatus | null,
  locked: boolean,
) {
  const operator = role === "Admin" || role === "Manager"
  return {
    progress:
      operator &&
      (status === "CONFIRMED" || status === "IN_PROGRESS") &&
      !locked,
    hold:
      operator &&
      (status === "CONFIRMED" || status === "IN_PROGRESS") &&
      !locked,
    resume: operator && status === "ON_HOLD" && !locked,
    complete: operator && status === "IN_PROGRESS" && !locked,
    cancel:
      operator &&
      (status === "CONFIRMED" ||
        status === "IN_PROGRESS" ||
        status === "ON_HOLD") &&
      !locked,
  }
}

export function canConvertQuotation(
  role: string | null,
  status: string | null,
  locked: boolean,
) {
  return (
    (role === "Admin" || role === "Sales") && status === "ACCEPTED" && !locked
  )
}

export function canViewGlobalAudit(role: string | null) {
  return role === "Admin" || role === "Manager"
}

function expectedProgress(
  action: OrderProgressAction,
  payload: OrderProgressPayload | OrderReasonPayload,
) {
  return {
    status:
      action === "hold"
        ? "ON_HOLD" as const
        : action === "complete"
          ? "COMPLETED" as const
          : action === "cancel"
            ? "CANCELLED" as const
            : "IN_PROGRESS" as const,
    percent: action === "complete" ? 100 : payload.progress_percent,
  }
}

export function classifyProgressReconciliation(
  before: OrderWorkspaceData,
  after: OrderWorkspaceData,
  action: OrderProgressAction,
  payload: OrderProgressPayload | OrderReasonPayload,
): ProgressReconciliation {
  const priorIds = new Set(before.progress.map((event) => event.id))
  const additions = after.progress.filter((event) => !priorIds.has(event.id))
  const expected = expectedProgress(action, payload)
  const expectedMilestone = payload.milestone_note ?? ""
  const expectedReason = "reason" in payload ? payload.reason : ""
  if (
    additions.length === 1 &&
    additions[0]!.order_id === before.order.id &&
    additions[0]!.from_status === before.order.workflow_status &&
    additions[0]!.to_status === expected.status &&
    additions[0]!.progress_percent === expected.percent &&
    additions[0]!.milestone_note === expectedMilestone &&
    additions[0]!.reason === expectedReason &&
    after.order.workflow_status === expected.status &&
    after.order.progress_percent === expected.percent
  ) {
    return "applied"
  }
  if (
    additions.length === 0 &&
    after.order.workflow_status === before.order.workflow_status &&
    after.order.progress_percent === before.order.progress_percent
  ) {
    return "not_applied"
  }
  return "ambiguous"
}

export function wouldDuplicateInProgressEvent(
  order: CanonicalOrder,
  action: OrderProgressAction,
  payload: OrderProgressPayload | OrderReasonPayload,
) {
  return (
    action === "progress" &&
    order.workflow_status === "IN_PROGRESS" &&
    order.progress_percent === payload.progress_percent
  )
}

export function isAmbiguousOrderError(error: unknown) {
  return (
    error instanceof CanonicalClientError &&
    ([
      "timeout",
      "network",
      "protocol",
      "server",
      "cancelled",
    ] as CanonicalErrorKind[]).includes(error.kind)
  )
}

const SAFE_ERROR_FIELDS = new Set([
  "form",
  "unknown_fields",
  "progress_percent",
  "milestone_note",
  "reason",
  "workflow_status",
  "expected_delivery_date",
  "quotation",
  "order",
])

function safeFields(details: unknown) {
  if (!isRecord(details)) return undefined
  const result: Record<string, string> = {}
  for (const key of Object.keys(details)) {
    if (SAFE_ERROR_FIELDS.has(key)) {
      result[key] = "Giá trị không được máy chủ chấp nhận."
    }
  }
  return Object.keys(result).length > 0 ? result : undefined
}

export function orderCommandStateFromError(error: unknown): OrderCommandState {
  if (!(error instanceof CanonicalClientError)) {
    return { status: "protocol", message: "Phản hồi Order không hợp lệ." }
  }
  if (error.kind === "authentication") {
    return {
      status: "authentication_failure",
      message: "Phiên đăng nhập đã hết hạn.",
    }
  }
  if (error.kind === "permission") {
    return {
      status: "permission_denied",
      message: "Bạn không có quyền canonical chính xác cho thao tác này.",
    }
  }
  if (error.kind === "validation") {
    return {
      status: "validation",
      message: "Kiểm tra lại dữ liệu Order.",
      fieldErrors: safeFields(error.details),
    }
  }
  if (error.kind === "conflict") {
    return error.code === "idempotency_conflict"
      ? {
          status: "idempotency_conflict",
          message: "Conversion retry xung đột với logical attempt trước.",
        }
      : {
          status: "lifecycle_conflict",
          message: "Trạng thái authoritative không cho phép thao tác.",
        }
  }
  if (error.kind === "timeout") {
    return { status: "timeout", message: "Yêu cầu Order đã quá thời gian." }
  }
  if (error.kind === "network") {
    return { status: "network", message: "Không thể kết nối dịch vụ Order." }
  }
  if (error.kind === "cancelled") {
    return { status: "cancelled", message: "Yêu cầu Order đã bị hủy." }
  }
  if (error.kind === "server") {
    return { status: "server", message: "Máy chủ chưa thể xử lý Order." }
  }
  return { status: "protocol", message: "Phản hồi Order không hợp lệ." }
}

export function createOrderCommandGate() {
  let pending = false
  return {
    tryStart() {
      if (pending) return false
      pending = true
      return true
    },
    finish() {
      pending = false
    },
    isPending() {
      return pending
    },
  }
}

export function createOrderRequestGuards() {
  return {
    index: createLatestRequestGuard(),
    conversion: createLatestRequestGuard(),
    workspace: createLatestRequestGuard(),
    audit: createLatestRequestGuard(),
  }
}

export function settleOrderCommandOnDeactivate(
  state: OrderCommandState,
  nonIdempotentCommandPending = false,
): OrderCommandState {
  return state.status === "pending"
    ? nonIdempotentCommandPending
      ? {
          status: "ambiguous",
          message:
            "Progress command đã bị gián đoạn; phải refresh authoritative trước lệnh khác.",
        }
      : {
          status: "cancelled",
          message:
            "Yêu cầu đang chờ đã bị hủy; hãy đồng bộ trước thao tác tiếp theo.",
        }
    : state
}
