import { CanonicalClientError, type CanonicalErrorKind } from "./canonical.ts"
import {
  isCanonicalRfq,
  isCanonicalRfqPage,
  createLatestRequestGuard,
  type CanonicalPage,
  type CanonicalRfq,
  type RfqClient,
} from "./rfq.ts"

const IDEMPOTENCY_KEY_PATTERN = /^[A-Za-z0-9._:-]{1,64}$/
const DATE_PATTERN = /^\d{4}-\d{2}-\d{2}$/
const UNITS = ["PCS", "KG", "M", "MM"] as const
const BUSINESS_TIME_ZONE = "Asia/Tokyo"

export type RfqUnit = typeof UNITS[number]

export type CanonicalCustomer = {
  id: number
  data_contract: string
  customer_code: string
  company_name: string
  status: string | null
}

export type CanonicalPart = {
  id: number
  data_contract: string
  part_code: string
  name: string
  revision: string
  unit: string
  default_material_id: number | null
  tolerance: string
  technical_requirements: string
  is_active: boolean
}

export type CanonicalMaterial = {
  id: number
  data_contract: string
  material_code: string
  name: string
  standard: string
  grade: string
  is_active: boolean
}

export type CanonicalRfqLine = {
  id: number
  rfq_id: number
  line_number: number
  part_id: number | null
  material_id: number | null
  description: string
  quantity: string
  unit: RfqUnit
  required_delivery_date: string
  tolerance: string
  technical_notes: string
  drawing_required: boolean
  created_at: string | null
  updated_at: string | null
}

export type RfqSelectors = {
  customers: CanonicalCustomer[]
  parts: CanonicalPart[]
  materials: CanonicalMaterial[]
}

export type RfqCreatePayload = {
  customer_id: number
  project_name?: string
  notes?: string
  quote_due_at: string
  required_delivery_date: string
  assigned_to_id?: number | null
}

export type RfqUpdatePayload = Partial<Pick<RfqCreatePayload, "project_name" | "notes" | "quote_due_at" | "required_delivery_date" | "assigned_to_id">>

export type RfqLineCreatePayload = {
  part_id?: number | null
  material_id?: number | null
  description: string
  quantity: string
  unit: RfqUnit
  required_delivery_date: string
  tolerance?: string
  technical_notes?: string
  drawing_required?: boolean
}

export type RfqLineUpdatePayload = Partial<RfqLineCreatePayload>

export type RfqReviewCompletePayload = {
  feasible_line_ids: number[]
  drawing_not_required_line_ids: number[]
  notes?: string
}

export type ClientFieldErrors = Record<string, string>

export type RfqCommandStatus = "initial" | "loading_selectors" | "ready" | "submitting" | "accepted" | "field_validation" | "authentication_failure" | "permission_denied" | "lifecycle_conflict" | "idempotency_conflict" | "timeout" | "network" | "protocol" | "server" | "cancelled"

export type RfqCommandViewState = {
  status: RfqCommandStatus
  message: string
  fieldErrors?: ClientFieldErrors
}

type CreateAttempt = {
  key: string
  payload: RfqCreatePayload
  createdRfqId: number | null
}

type EffectiveRfqDates = {
  quote_due_at: string | null
  required_delivery_date: string | null
}

function clientValidation(fieldErrors: ClientFieldErrors): never {
  throw new CanonicalClientError({
    kind: "validation",
    code: "client_validation_error",
    message: "RFQ input validation failed.",
    details: fieldErrors,
  })
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value)
}

function rejectUnknownFields(
  value: Record<string, unknown>,
  allowed: readonly string[],
): void {
  const unknown = Object.keys(value).filter((key) => !allowed.includes(key))
  if (unknown.length > 0) {
    clientValidation({ unknown_fields: "Có trường dữ liệu không được hỗ trợ." })
  }
}

function positiveInteger(value: unknown, field: string): number {
  if (!Number.isInteger(value) || Number(value) < 1) {
    clientValidation({ [field]: "Phải chọn một bản ghi hợp lệ." })
  }
  return Number(value)
}

function optionalPositiveInteger(
  value: unknown,
  field: string,
): number | null | undefined {
  if (value === undefined) return undefined
  if (value === null) return null
  return positiveInteger(value, field)
}

function text(value: unknown, field: string, maxLength?: number): string {
  if (typeof value !== "string") {
    clientValidation({ [field]: "Giá trị văn bản không hợp lệ." })
  }
  const normalized = value.trim()
  if (maxLength !== undefined && normalized.length > maxLength) {
    clientValidation({ [field]: `Không được vượt quá ${maxLength} ký tự.` })
  }
  return normalized
}

function dateValue(value: unknown, field: string): string {
  if (typeof value !== "string" || !DATE_PATTERN.test(value)) {
    clientValidation({ [field]: "Ngày không hợp lệ." })
  }
  const parsed = new Date(`${value}T00:00:00Z`)
  if (
    Number.isNaN(parsed.getTime()) ||
    parsed.toISOString().slice(0, 10) !== value
  ) {
    clientValidation({ [field]: "Ngày không hợp lệ." })
  }
  return value
}

function decimalQuantity(value: unknown): string {
  if (typeof value !== "string" || !/^\d+(?:\.\d{1,4})?$/.test(value)) {
    clientValidation({ quantity: "Số lượng phải là số thập phân dương." })
  }
  const numeric = Number(value)
  if (
    !Number.isFinite(numeric) ||
    numeric <= 0 ||
    value.split(".")[0]!.length > 12
  ) {
    clientValidation({ quantity: "Số lượng phải là số thập phân dương." })
  }
  return value
}

function unitValue(value: unknown): RfqUnit {
  if (!isRfqUnit(value)) {
    clientValidation({ unit: "Đơn vị phải là PCS, KG, M hoặc MM." })
  }
  return value
}

function isRfqUnit(value: unknown): value is RfqUnit {
  return typeof value === "string" && UNITS.includes(value as RfqUnit)
}

export function businessCalendarDate(
  instant: Date = new Date(),
  timeZone = BUSINESS_TIME_ZONE,
): string {
  const parts = new Intl.DateTimeFormat("en-US", {
    timeZone,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).formatToParts(instant)
  const calendar = Object.fromEntries(
    parts
      .filter((part) => ["year", "month", "day"].includes(part.type))
      .map((part) => [part.type, part.value]),
  )
  return `${calendar.year}-${calendar.month}-${calendar.day}`
}

export function validateRfqCreatePayload(
  input: unknown,
  today = businessCalendarDate(),
): RfqCreatePayload {
  if (!isRecord(input)) clientValidation({ form: "Dữ liệu RFQ không hợp lệ." })
  rejectUnknownFields(input, [
    "customer_id",
    "project_name",
    "notes",
    "quote_due_at",
    "required_delivery_date",
    "assigned_to_id",
  ])
  const quoteDueAt = dateValue(input.quote_due_at, "quote_due_at")
  const deliveryDate = dateValue(
    input.required_delivery_date,
    "required_delivery_date",
  )
  if (deliveryDate < today) {
    clientValidation({
      required_delivery_date: "Ngày giao hàng không thể ở quá khứ.",
    })
  }
  if (quoteDueAt > deliveryDate) {
    clientValidation({
      quote_due_at: "Hạn báo giá phải trước hoặc bằng ngày giao hàng.",
    })
  }
  const payload: RfqCreatePayload = {
    customer_id: positiveInteger(input.customer_id, "customer_id"),
    quote_due_at: quoteDueAt,
    required_delivery_date: deliveryDate,
  }
  if (input.project_name !== undefined) {
    payload.project_name = text(input.project_name, "project_name", 220)
  }
  if (input.notes !== undefined) payload.notes = text(input.notes, "notes")
  const assignedTo = optionalPositiveInteger(
    input.assigned_to_id,
    "assigned_to_id",
  )
  if (assignedTo !== undefined) payload.assigned_to_id = assignedTo
  return payload
}

export function validateRfqUpdatePayload(
  input: unknown,
  current: EffectiveRfqDates = {
    quote_due_at: null,
    required_delivery_date: null,
  },
  today = businessCalendarDate(),
): RfqUpdatePayload {
  if (!isRecord(input)) clientValidation({ form: "Dữ liệu RFQ không hợp lệ." })
  rejectUnknownFields(input, [
    "project_name",
    "notes",
    "quote_due_at",
    "required_delivery_date",
    "assigned_to_id",
  ])
  if (Object.keys(input).length === 0) {
    clientValidation({ form: "Cần ít nhất một trường RFQ để cập nhật." })
  }
  const payload: RfqUpdatePayload = {}
  if (input.project_name !== undefined) {
    payload.project_name = text(input.project_name, "project_name", 220)
  }
  if (input.notes !== undefined) payload.notes = text(input.notes, "notes")
  if (input.quote_due_at !== undefined) {
    payload.quote_due_at = dateValue(input.quote_due_at, "quote_due_at")
  }
  if (input.required_delivery_date !== undefined) {
    payload.required_delivery_date = dateValue(
      input.required_delivery_date,
      "required_delivery_date",
    )
  }
  const effectiveQuoteDueAt = payload.quote_due_at ?? current.quote_due_at
  const effectiveDeliveryDate =
    payload.required_delivery_date ?? current.required_delivery_date
  if (effectiveDeliveryDate !== null && effectiveDeliveryDate < today) {
    clientValidation({
      required_delivery_date: "Ngày giao hàng không thể ở quá khứ.",
    })
  }
  if (
    effectiveQuoteDueAt !== null &&
    effectiveDeliveryDate !== null &&
    effectiveQuoteDueAt > effectiveDeliveryDate
  ) {
    clientValidation({
      quote_due_at: "Hạn báo giá phải trước hoặc bằng ngày giao hàng.",
    })
  }
  const assignedTo = optionalPositiveInteger(
    input.assigned_to_id,
    "assigned_to_id",
  )
  if (assignedTo !== undefined) payload.assigned_to_id = assignedTo
  return payload
}

export function validateRfqLineCreatePayload(
  input: unknown,
): RfqLineCreatePayload {
  if (!isRecord(input))
    clientValidation({ form: "Dữ liệu dòng RFQ không hợp lệ." })
  rejectUnknownFields(input, [
    "part_id",
    "material_id",
    "description",
    "quantity",
    "unit",
    "required_delivery_date",
    "tolerance",
    "technical_notes",
    "drawing_required",
  ])
  const description = text(input.description, "description")
  const tolerance = text(input.tolerance ?? "", "tolerance", 120)
  const technicalNotes = text(input.technical_notes ?? "", "technical_notes")
  if (!description)
    clientValidation({ description: "Mô tả chi tiết là bắt buộc." })
  if (!tolerance)
    clientValidation({ tolerance: "Dung sai là bắt buộc để gửi RFQ." })
  if (!technicalNotes) {
    clientValidation({
      technical_notes: "Ghi chú kỹ thuật là bắt buộc để gửi RFQ.",
    })
  }
  if (input.drawing_required === true) {
    clientValidation({
      drawing_required:
        "Phase 5C không hỗ trợ tải bản vẽ; không thể yêu cầu bản vẽ.",
    })
  }
  const payload: RfqLineCreatePayload = {
    description,
    quantity: decimalQuantity(input.quantity),
    unit: unitValue(input.unit),
    required_delivery_date: dateValue(
      input.required_delivery_date,
      "required_delivery_date",
    ),
    tolerance,
    technical_notes: technicalNotes,
    drawing_required: false,
  }
  const partId = optionalPositiveInteger(input.part_id, "part_id")
  const materialId = optionalPositiveInteger(input.material_id, "material_id")
  if (partId !== undefined) payload.part_id = partId
  if (materialId !== undefined) payload.material_id = materialId
  return payload
}

export function validateRfqLineUpdatePayload(
  input: unknown,
): RfqLineUpdatePayload {
  if (!isRecord(input))
    clientValidation({ form: "Dữ liệu dòng RFQ không hợp lệ." })
  rejectUnknownFields(input, [
    "part_id",
    "material_id",
    "description",
    "quantity",
    "unit",
    "required_delivery_date",
    "tolerance",
    "technical_notes",
    "drawing_required",
  ])
  if (Object.keys(input).length === 0) {
    clientValidation({ form: "Cần ít nhất một trường dòng để cập nhật." })
  }
  const payload: RfqLineUpdatePayload = {}
  if (input.description !== undefined) {
    const description = text(input.description, "description")
    if (!description)
      clientValidation({ description: "Mô tả chi tiết là bắt buộc." })
    payload.description = description
  }
  if (input.quantity !== undefined)
    payload.quantity = decimalQuantity(input.quantity)
  if (input.unit !== undefined) payload.unit = unitValue(input.unit)
  if (input.required_delivery_date !== undefined) {
    payload.required_delivery_date = dateValue(
      input.required_delivery_date,
      "required_delivery_date",
    )
  }
  if (input.tolerance !== undefined) {
    const tolerance = text(input.tolerance, "tolerance", 120)
    if (!tolerance)
      clientValidation({ tolerance: "Dung sai không được để trống." })
    payload.tolerance = tolerance
  }
  if (input.technical_notes !== undefined) {
    const notes = text(input.technical_notes, "technical_notes")
    if (!notes)
      clientValidation({
        technical_notes: "Ghi chú kỹ thuật không được để trống.",
      })
    payload.technical_notes = notes
  }
  if (input.drawing_required !== undefined) {
    if (input.drawing_required !== false) {
      clientValidation({
        drawing_required:
          "Phase 5C không hỗ trợ tải bản vẽ; không thể yêu cầu bản vẽ.",
      })
    }
    payload.drawing_required = false
  }
  const partId = optionalPositiveInteger(input.part_id, "part_id")
  const materialId = optionalPositiveInteger(input.material_id, "material_id")
  if (partId !== undefined) payload.part_id = partId
  if (materialId !== undefined) payload.material_id = materialId
  return payload
}

function isCanonicalPage<T>(
  value: unknown,
  itemGuard: (item: unknown) => item is T,
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
    value.results.every(itemGuard)
  )
}

function isCustomer(value: unknown): value is CanonicalCustomer {
  return (
    isRecord(value) &&
    typeof value.id === "number" &&
    typeof value.data_contract === "string" &&
    typeof value.customer_code === "string" &&
    typeof value.company_name === "string" &&
    (typeof value.status === "string" || value.status === null)
  )
}

function isPart(value: unknown): value is CanonicalPart {
  return (
    isRecord(value) &&
    typeof value.id === "number" &&
    typeof value.data_contract === "string" &&
    typeof value.part_code === "string" &&
    typeof value.name === "string" &&
    typeof value.revision === "string" &&
    typeof value.unit === "string" &&
    (typeof value.default_material_id === "number" ||
      value.default_material_id === null) &&
    typeof value.tolerance === "string" &&
    typeof value.technical_requirements === "string" &&
    typeof value.is_active === "boolean"
  )
}

function isMaterial(value: unknown): value is CanonicalMaterial {
  return (
    isRecord(value) &&
    typeof value.id === "number" &&
    typeof value.data_contract === "string" &&
    typeof value.material_code === "string" &&
    typeof value.name === "string" &&
    typeof value.standard === "string" &&
    typeof value.grade === "string" &&
    typeof value.is_active === "boolean"
  )
}

export function isCanonicalRfqLine(value: unknown): value is CanonicalRfqLine {
  return (
    isRecord(value) &&
    typeof value.id === "number" &&
    typeof value.rfq_id === "number" &&
    typeof value.line_number === "number" &&
    (typeof value.part_id === "number" || value.part_id === null) &&
    (typeof value.material_id === "number" || value.material_id === null) &&
    typeof value.description === "string" &&
    typeof value.quantity === "string" &&
    isRfqUnit(value.unit) &&
    typeof value.required_delivery_date === "string" &&
    typeof value.tolerance === "string" &&
    typeof value.technical_notes === "string" &&
    typeof value.drawing_required === "boolean" &&
    (typeof value.created_at === "string" || value.created_at === null) &&
    (typeof value.updated_at === "string" || value.updated_at === null)
  )
}

function protocolError(code: string): never {
  throw new CanonicalClientError({
    kind: "protocol",
    code,
    message: "The server returned an invalid canonical RFQ response.",
  })
}

async function postCommand<T>(
  client: RfqClient,
  path: string,
  payload: object,
  signal?: AbortSignal,
  headers?: HeadersInit,
): Promise<T> {
  return client.request<T>(path, {
    method: "POST",
    headers: { "content-type": "application/json", ...headers },
    body: JSON.stringify(payload),
    signal,
  })
}

export async function loadRfqSelectors(
  client: RfqClient,
  signal?: AbortSignal,
): Promise<RfqSelectors> {
  const [customers, parts, materials] = await Promise.all([
    client.request<CanonicalPage<CanonicalCustomer>>(
      "customers/?data_contract=MVP_V1&status=ACTIVE&limit=100&ordering=company_name",
      { signal },
    ),
    client.request<CanonicalPage<CanonicalPart>>(
      "parts/?data_contract=MVP_V1&is_active=true&limit=100&ordering=part_code",
      { signal },
    ),
    client.request<CanonicalPage<CanonicalMaterial>>(
      "materials/?data_contract=MVP_V1&is_active=true&limit=100&ordering=material_code",
      { signal },
    ),
  ])
  if (!isCanonicalPage(customers, isCustomer))
    protocolError("invalid_customer_page")
  if (!isCanonicalPage(parts, isPart)) protocolError("invalid_part_page")
  if (!isCanonicalPage(materials, isMaterial))
    protocolError("invalid_material_page")
  return {
    customers: customers.results,
    parts: parts.results,
    materials: materials.results,
  }
}

export async function createRfqDraft(
  client: RfqClient,
  payload: RfqCreatePayload,
  idempotencyKey: string,
  signal?: AbortSignal,
): Promise<CanonicalRfq> {
  if (!IDEMPOTENCY_KEY_PATTERN.test(idempotencyKey)) {
    clientValidation({ idempotency_key: "Khóa thao tác không hợp lệ." })
  }
  const result = await postCommand<CanonicalRfq>(
    client,
    "rfqs/commands/create/",
    payload,
    signal,
    { "Idempotency-Key": idempotencyKey },
  )
  if (!isCanonicalRfq(result) || result.data_contract !== "MVP_V1") {
    protocolError("invalid_rfq_command_response")
  }
  return result
}

export async function updateRfqDraft(
  client: RfqClient,
  rfqId: number,
  payload: RfqUpdatePayload,
  signal?: AbortSignal,
): Promise<CanonicalRfq> {
  const result = await postCommand<CanonicalRfq>(
    client,
    `rfqs/${positiveInteger(rfqId, "rfq_id")}/commands/update/`,
    payload,
    signal,
  )
  if (!isCanonicalRfq(result)) protocolError("invalid_rfq_command_response")
  return result
}

export async function addRfqLine(
  client: RfqClient,
  rfqId: number,
  payload: RfqLineCreatePayload,
  signal?: AbortSignal,
): Promise<CanonicalRfqLine> {
  const result = await postCommand<CanonicalRfqLine>(
    client,
    `rfqs/${positiveInteger(rfqId, "rfq_id")}/lines/commands/add/`,
    payload,
    signal,
  )
  if (!isCanonicalRfqLine(result)) protocolError("invalid_rfq_line_response")
  return result
}

export async function updateRfqLine(
  client: RfqClient,
  rfqId: number,
  lineId: number,
  payload: RfqLineUpdatePayload,
  signal?: AbortSignal,
): Promise<CanonicalRfqLine> {
  const result = await postCommand<CanonicalRfqLine>(
    client,
    `rfqs/${positiveInteger(rfqId, "rfq_id")}/lines/${positiveInteger(lineId, "line_id")}/commands/update/`,
    payload,
    signal,
  )
  if (!isCanonicalRfqLine(result)) protocolError("invalid_rfq_line_response")
  return result
}

export async function removeRfqLine(
  client: RfqClient,
  rfqId: number,
  lineId: number,
  signal?: AbortSignal,
): Promise<void> {
  const expectedLineId = positiveInteger(lineId, "line_id")
  const result = await postCommand<unknown>(
    client,
    `rfqs/${positiveInteger(rfqId, "rfq_id")}/lines/${expectedLineId}/commands/remove/`,
    {},
    signal,
  )
  if (
    !isRecord(result) ||
    result.id !== expectedLineId ||
    result.removed !== true
  ) {
    protocolError("invalid_rfq_line_remove_response")
  }
}

export async function submitRfq(
  client: RfqClient,
  rfqId: number,
  signal?: AbortSignal,
): Promise<CanonicalRfq> {
  const result = await postCommand<CanonicalRfq>(
    client,
    `rfqs/${positiveInteger(rfqId, "rfq_id")}/commands/submit/`,
    {},
    signal,
  )
  if (!isCanonicalRfq(result) || result.status !== "SUBMITTED") {
    protocolError("invalid_rfq_submit_response")
  }
  return result
}

function reviewRfqFromResponse(
  value: unknown,
  expectedStatus: string,
): CanonicalRfq {
  if (
    !isRecord(value) ||
    !isCanonicalRfq(value.rfq) ||
    value.rfq.status !== expectedStatus
  ) {
    protocolError("invalid_rfq_review_response")
  }
  return value.rfq
}

export async function startRfqReview(
  client: RfqClient,
  rfqId: number,
  signal?: AbortSignal,
): Promise<CanonicalRfq> {
  const result = await postCommand<unknown>(
    client,
    `rfqs/${positiveInteger(rfqId, "rfq_id")}/review/commands/start/`,
    {},
    signal,
  )
  return reviewRfqFromResponse(result, "UNDER_REVIEW")
}

export function validateRfqReviewCompletePayload(
  input: RfqReviewCompletePayload,
): RfqReviewCompletePayload {
  if (!isRecord(input))
    clientValidation({ form: "Dữ liệu review không hợp lệ." })
  rejectUnknownFields(input, [
    "feasible_line_ids",
    "drawing_not_required_line_ids",
    "notes",
  ])
  const feasible = Array.isArray(input.feasible_line_ids)
    ? input.feasible_line_ids.map((id) =>
        positiveInteger(id, "feasible_line_ids"),
      )
    : clientValidation({ feasible_line_ids: "Phải xác nhận mọi dòng RFQ." })
  const noDrawing = Array.isArray(input.drawing_not_required_line_ids)
    ? input.drawing_not_required_line_ids.map((id) =>
        positiveInteger(id, "drawing_not_required_line_ids"),
      )
    : clientValidation({
        drawing_not_required_line_ids: "Xác nhận bản vẽ không hợp lệ.",
      })
  if (feasible.length === 0 || new Set(feasible).size !== feasible.length) {
    clientValidation({
      feasible_line_ids: "Phải xác nhận riêng từng dòng RFQ.",
    })
  }
  if (new Set(noDrawing).size !== noDrawing.length) {
    clientValidation({
      drawing_not_required_line_ids: "Dòng xác nhận bản vẽ bị trùng.",
    })
  }
  return {
    feasible_line_ids: feasible,
    drawing_not_required_line_ids: noDrawing,
    notes: text(input.notes ?? "", "notes", 2000),
  }
}

export async function completeRfqReview(
  client: RfqClient,
  rfqId: number,
  payload: RfqReviewCompletePayload,
  signal?: AbortSignal,
): Promise<CanonicalRfq> {
  const result = await postCommand<unknown>(
    client,
    `rfqs/${positiveInteger(rfqId, "rfq_id")}/review/commands/complete/`,
    validateRfqReviewCompletePayload(payload),
    signal,
  )
  return reviewRfqFromResponse(result, "READY_TO_QUOTE")
}

export function rfqReviewPermissions(
  role: string | null,
  status: string | null,
  locked: boolean,
) {
  const manager = role === "Manager" && !locked
  return {
    start: manager && status === "SUBMITTED",
    complete: manager && status === "UNDER_REVIEW",
  }
}

export async function fetchRfqDetail(
  client: RfqClient,
  rfqId: number,
  signal?: AbortSignal,
): Promise<CanonicalRfq> {
  const result = await client.request<CanonicalRfq>(
    `rfqs/${positiveInteger(rfqId, "rfq_id")}/`,
    { signal },
  )
  if (!isCanonicalRfq(result)) protocolError("invalid_rfq_detail")
  return result
}

export async function fetchRfqLines(
  client: RfqClient,
  rfqId: number,
  signal?: AbortSignal,
): Promise<CanonicalRfqLine[]> {
  const result = await client.request<CanonicalPage<CanonicalRfqLine>>(
    `rfqs/${positiveInteger(rfqId, "rfq_id")}/lines/?limit=100&ordering=line_number`,
    { signal },
  )
  if (!isCanonicalPage(result, isCanonicalRfqLine)) {
    protocolError("invalid_rfq_line_page")
  }
  return result.results
}

function fieldErrors(details: unknown): ClientFieldErrors | undefined {
  if (!isRecord(details)) return undefined
  const allowed = new Set([
    "form",
    "non_field_errors",
    "unknown_fields",
    "customer",
    "customer_id",
    "project_name",
    "notes",
    "quote_due_at",
    "required_delivery_date",
    "assigned_to_id",
    "lines",
    "part_id",
    "material_id",
    "description",
    "quantity",
    "unit",
    "tolerance",
    "technical_notes",
    "drawing_required",
  ])
  const mapped: ClientFieldErrors = {}
  for (const key of Object.keys(details)) {
    if (allowed.has(key)) mapped[key] = "Giá trị không được máy chủ chấp nhận."
  }
  return Object.keys(mapped).length > 0 ? mapped : undefined
}

const STATE_MESSAGES: Record<RfqCommandStatus, string> = {
  initial: "Khởi tạo biểu mẫu RFQ.",
  loading_selectors: "Đang tải danh mục canonical...",
  ready: "Sẵn sàng chỉnh sửa RFQ.",
  submitting: "Đang gửi lệnh RFQ...",
  accepted: "Lệnh đã được chấp nhận và dữ liệu đã được đồng bộ.",
  field_validation: "Kiểm tra lại các trường RFQ.",
  authentication_failure: "Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.",
  permission_denied: "Bạn không có quyền thực hiện lệnh RFQ này.",
  lifecycle_conflict: "RFQ không còn ở trạng thái cho phép thao tác này.",
  idempotency_conflict: "Lệnh tạo RFQ xung đột với một thao tác trước đó.",
  timeout:
    "Không xác định được lệnh RFQ đã được xử lý hay chưa. Hãy tải lại trạng thái RFQ trước khi thử lại.",
  network:
    "Không xác định được lệnh RFQ đã được xử lý hay chưa. Hãy tải lại trạng thái RFQ trước khi thử lại.",
  protocol: "Phản hồi RFQ không đúng hợp đồng canonical.",
  server: "Máy chủ chưa thể xử lý lệnh RFQ.",
  cancelled: "Thao tác RFQ đã được hủy.",
}

export function commandState(
  status: RfqCommandStatus,
  errors?: ClientFieldErrors,
): RfqCommandViewState {
  return { status, message: STATE_MESSAGES[status], fieldErrors: errors }
}

export function commandStateFromError(error: unknown): RfqCommandViewState {
  if (!(error instanceof CanonicalClientError)) return commandState("protocol")
  if (error.kind === "authentication")
    return commandState("authentication_failure")
  if (error.kind === "permission") return commandState("permission_denied")
  if (error.kind === "validation") {
    return commandState("field_validation", fieldErrors(error.details))
  }
  if (error.kind === "conflict") {
    return commandState(
      error.code === "idempotency_conflict"
        ? "idempotency_conflict"
        : "lifecycle_conflict",
    )
  }
  if (error.kind === "timeout") return commandState("timeout")
  if (error.kind === "network") return commandState("network")
  if (error.kind === "cancelled") return commandState("cancelled")
  if (error.kind === "server") return commandState("server")
  return commandState("protocol")
}

export function shouldRetainCreateAttempt(error: unknown): boolean {
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

export function createRfqCreateAttemptManager(
  keyFactory: () => string = () => crypto.randomUUID(),
) {
  let active: CreateAttempt | null = null
  return {
    begin(payload: RfqCreatePayload): CreateAttempt {
      if (active !== null) return active
      const key = keyFactory()
      if (!IDEMPOTENCY_KEY_PATTERN.test(key)) {
        throw new CanonicalClientError({
          kind: "protocol",
          code: "invalid_idempotency_key_factory",
          message: "Unable to prepare a safe RFQ command.",
        })
      }
      active = { key, payload: { ...payload }, createdRfqId: null }
      return active
    },
    markCreated(attempt: CreateAttempt, rfqId: number): void {
      if (active === attempt) {
        active.createdRfqId = positiveInteger(rfqId, "rfq_id")
      }
    },
    fail(attempt: CreateAttempt, error: unknown): void {
      if (
        active === attempt &&
        active.createdRfqId === null &&
        !shouldRetainCreateAttempt(error)
      ) {
        active = null
      }
    },
    complete(attempt: CreateAttempt): void {
      if (active === attempt) active = null
    },
    hasUnreconciledCreate(): boolean {
      return active !== null && active.createdRfqId !== null
    },
    hasActiveAttempt(): boolean {
      return active !== null
    },
    activePayload(): RfqCreatePayload | null {
      return active === null ? null : { ...active.payload }
    },
    clear(): void {
      active = null
    },
  }
}

export async function executeRfqCreateAttempt<T>(
  client: RfqClient,
  manager: ReturnType<typeof createRfqCreateAttemptManager>,
  payload: RfqCreatePayload,
  reconcile: (rfqId: number, signal?: AbortSignal) => Promise<T>,
  signal?: AbortSignal,
): Promise<T> {
  const attempt = manager.begin(payload)
  try {
    if (attempt.createdRfqId === null) {
      const created = await createRfqDraft(
        client,
        attempt.payload,
        attempt.key,
        signal,
      )
      manager.markCreated(attempt, created.id)
    }
    const result = await reconcile(attempt.createdRfqId!, signal)
    manager.complete(attempt)
    return result
  } catch (error) {
    manager.fail(attempt, error)
    throw error
  }
}

export function createCommandGate() {
  let pending = false
  return {
    tryStart(): boolean {
      if (pending) return false
      pending = true
      return true
    },
    finish(): void {
      pending = false
    },
    isPending(): boolean {
      return pending
    },
  }
}

export function createRfqRequestGuards() {
  return {
    selectors: createLatestRequestGuard(),
    workspace: createLatestRequestGuard(),
  }
}

export function rfqLifecyclePermissions(
  status: string | null,
  pending: boolean,
) {
  const editable = status === "DRAFT" && !pending
  return {
    header: editable,
    lines: editable,
    submit: editable,
  }
}
