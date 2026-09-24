import {
  CanonicalClientError,
  type CanonicalErrorKind,
  type createCanonicalClient,
} from "./canonical.ts"
import { createLatestRequestGuard, type CanonicalPage } from "./rfq.ts"

const DATE_PATTERN = /^\d{4}-\d{2}-\d{2}$/
const DECIMAL_PATTERN = /^\d+(?:\.\d{1,4})?$/
const FAMILY_PATTERN = /^[A-Za-z0-9._:-]{1,100}$/
const IDEMPOTENCY_KEY_PATTERN = /^[A-Za-z0-9._:-]{1,64}$/

export const QUOTATION_STATES = [
  "DRAFT",
  "PENDING_APPROVAL",
  "APPROVED",
  "REJECTED",
  "SUPERSEDED",
  "SENT",
  "ACCEPTED",
  "DECLINED",
] as const

export type QuotationWorkflowStatus = typeof QUOTATION_STATES[number]
export type CanonicalClient = ReturnType<typeof createCanonicalClient>

export type CanonicalQuotationSummary = {
  id: number
  data_contract: string
  quotation_family_number: string | null
  quotation_number: string
  revision: number | null
  rfq_id: number | null
  customer_id: number | null
  workflow_status: QuotationWorkflowStatus | null
  currency: string
  valid_from: string | null
  valid_until: string | null
  subtotal: string
  discount_total: string
  tax_amount: string
  total: string
  sent_at: string | null
  created_by_id: number | null
  created_at: string | null
  updated_at: string | null
  compatibility: Record<string, unknown> | null
}

export type CanonicalQuotation = CanonicalQuotationSummary & {
  terms: string
  customer_snapshot: Record<string, unknown>
  rfq_snapshot: Record<string, unknown>
  updated_by_id: number | null
}

export type CanonicalQuotationFamily = {
  quotation_family_number: string
  rfq_id: number
  rfq_number: string
  customer_id: number
  revision_count: number
  revisions: CanonicalQuotationSummary[]
}

export type CanonicalQuotationLine = {
  id: number
  quotation_id: number
  data_contract: string
  line_number: number
  source_rfq_line_id: number
  part_id: number | null
  description: string
  part_code_snapshot: string
  material_snapshot: string
  unit: string
  quantity: string
  unit_price: string
  discount: string
  line_subtotal: string
  line_total: string
  created_at: string | null
}

export type CanonicalApprovalDecision = {
  id: number
  quotation_id: number
  reviewer_id: number | null
  decision: "APPROVED" | "REJECTED"
  reason: string
  notes: string
  decided_at: string | null
}

export type CanonicalCustomerDecision = {
  id: number
  quotation_id: number
  recorded_by_id: number | null
  decision: "ACCEPTED" | "DECLINED"
  reason: string
  contact_evidence_recorded: boolean
  decision_evidence_recorded: boolean
  decided_at: string | null
}

export type QuotationPricingLinePayload = {
  source_rfq_line_id: number
  unit_price: string
  discount?: string
}

export type QuotationCreatePayload = {
  currency: "VND" | "USD"
  valid_from: string
  valid_until: string
  discount_total?: string
  tax_amount?: string
  terms?: string
  lines: QuotationPricingLinePayload[]
}

export type QuotationUpdatePayload = Partial<QuotationCreatePayload>

export type QuotationSendPayload = {
  sent_to: string
  evidence: string
}

export type QuotationCustomerDecisionPayload = {
  contact_snapshot: string
  evidence: string
  reason?: string
}

type InitialQuotationTarget = {
  kind: "initial"
  rfqId: number
}

type RevisionQuotationTarget = {
  kind: "revision"
  quotationId: number
}

export type QuotationCreateTarget = InitialQuotationTarget | RevisionQuotationTarget

export type QuotationWorkspaceData = {
  quotation: CanonicalQuotation
  lines: CanonicalQuotationLine[]
  family: CanonicalQuotationFamily
  revisions: CanonicalQuotationSummary[]
  approvals: CanonicalApprovalDecision[]
  customerDecisions: CanonicalCustomerDecision[]
}

export type QuotationIndex = {
  families: CanonicalPage<CanonicalQuotationFamily>
  quotations: CanonicalPage<CanonicalQuotationSummary>
}

export type QuotationAction = "create" | "create_revision" | "update" | "archive" | "submit" | "approve" | "reject" | "send" | "accept" | "decline"

export type QuotationCommandStatus = "initial" | "loading" | "ready" | "pending" | "accepted" | "field_validation" | "authentication_failure" | "permission_denied" | "ownership_denied" | "maker_checker_denied" | "lifecycle_conflict" | "idempotency_conflict" | "timeout" | "network" | "protocol" | "server" | "cancelled"

export type QuotationCommandState = {
  status: QuotationCommandStatus
  message: string
  fieldErrors?: Record<string, string>
}

type CreateAttempt = {
  target: QuotationCreateTarget
  key: string
  payload: QuotationCreatePayload
  createdQuotationId: number | null
  familyNumber: string | null
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value)
}

function isPage<T>(
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

function isNullableString(value: unknown): value is string | null {
  return typeof value === "string" || value === null
}

function isNullableNumber(value: unknown): value is number | null {
  return typeof value === "number" || value === null
}

function isWorkflowStatus(
  value: unknown,
): value is QuotationWorkflowStatus | null {
  return (
    value === null ||
    (typeof value === "string" &&
      QUOTATION_STATES.includes(value as QuotationWorkflowStatus))
  )
}

export function isQuotationSummary(
  value: unknown,
): value is CanonicalQuotationSummary {
  return (
    isRecord(value) &&
    typeof value.id === "number" &&
    typeof value.data_contract === "string" &&
    isNullableString(value.quotation_family_number) &&
    typeof value.quotation_number === "string" &&
    isNullableNumber(value.revision) &&
    isNullableNumber(value.rfq_id) &&
    isNullableNumber(value.customer_id) &&
    isWorkflowStatus(value.workflow_status) &&
    typeof value.currency === "string" &&
    isNullableString(value.valid_from) &&
    isNullableString(value.valid_until) &&
    typeof value.subtotal === "string" &&
    typeof value.discount_total === "string" &&
    typeof value.tax_amount === "string" &&
    typeof value.total === "string" &&
    isNullableString(value.sent_at) &&
    isNullableNumber(value.created_by_id) &&
    isNullableString(value.created_at) &&
    isNullableString(value.updated_at) &&
    (value.compatibility === null || isRecord(value.compatibility))
  )
}

export function isQuotation(value: unknown): value is CanonicalQuotation {
  return (
    isQuotationSummary(value) &&
    "terms" in value &&
    typeof value.terms === "string" &&
    "customer_snapshot" in value &&
    isRecord(value.customer_snapshot) &&
    "rfq_snapshot" in value &&
    isRecord(value.rfq_snapshot) &&
    "updated_by_id" in value &&
    isNullableNumber(value.updated_by_id)
  )
}

function isQuotationFamily(value: unknown): value is CanonicalQuotationFamily {
  return (
    isRecord(value) &&
    typeof value.quotation_family_number === "string" &&
    typeof value.rfq_id === "number" &&
    typeof value.rfq_number === "string" &&
    typeof value.customer_id === "number" &&
    typeof value.revision_count === "number" &&
    Array.isArray(value.revisions) &&
    value.revisions.every(isQuotationSummary)
  )
}

function isQuotationLine(value: unknown): value is CanonicalQuotationLine {
  return (
    isRecord(value) &&
    typeof value.id === "number" &&
    typeof value.quotation_id === "number" &&
    typeof value.data_contract === "string" &&
    typeof value.line_number === "number" &&
    typeof value.source_rfq_line_id === "number" &&
    isNullableNumber(value.part_id) &&
    typeof value.description === "string" &&
    typeof value.part_code_snapshot === "string" &&
    typeof value.material_snapshot === "string" &&
    typeof value.unit === "string" &&
    typeof value.quantity === "string" &&
    typeof value.unit_price === "string" &&
    typeof value.discount === "string" &&
    typeof value.line_subtotal === "string" &&
    typeof value.line_total === "string" &&
    isNullableString(value.created_at)
  )
}

function isApprovalDecision(
  value: unknown,
): value is CanonicalApprovalDecision {
  return (
    isRecord(value) &&
    typeof value.id === "number" &&
    typeof value.quotation_id === "number" &&
    isNullableNumber(value.reviewer_id) &&
    (value.decision === "APPROVED" || value.decision === "REJECTED") &&
    typeof value.reason === "string" &&
    typeof value.notes === "string" &&
    isNullableString(value.decided_at)
  )
}

function isCustomerDecision(
  value: unknown,
): value is CanonicalCustomerDecision {
  return (
    isRecord(value) &&
    typeof value.id === "number" &&
    typeof value.quotation_id === "number" &&
    isNullableNumber(value.recorded_by_id) &&
    (value.decision === "ACCEPTED" || value.decision === "DECLINED") &&
    typeof value.reason === "string" &&
    typeof value.contact_evidence_recorded === "boolean" &&
    typeof value.decision_evidence_recorded === "boolean" &&
    isNullableString(value.decided_at)
  )
}

function protocolError(code: string): never {
  throw new CanonicalClientError({
    kind: "protocol",
    code,
    message: "The server returned an invalid canonical quotation response.",
  })
}

function positiveInteger(value: unknown, field: string): number {
  if (!Number.isInteger(value) || Number(value) < 1) {
    validationError({ [field]: "Phải chọn bản ghi hợp lệ." })
  }
  return Number(value)
}

function familySegment(value: string): string {
  if (!FAMILY_PATTERN.test(value)) protocolError("invalid_quotation_family")
  return encodeURIComponent(value)
}

export function quotationReadPaths(quotationId: number, familyNumber: string) {
  const id = positiveInteger(quotationId, "quotation_id")
  const family = familySegment(familyNumber)
  return {
    detail: `quotations/${id}/`,
    lines: `quotations/${id}/lines/?limit=100&ordering=line_number`,
    approvals: `quotations/${id}/approval-decisions/?limit=100&ordering=decided_at`,
    customerDecisions: `quotations/${id}/customer-decisions/?limit=100&ordering=decided_at`,
    family: `quotation-families/${family}/`,
    revisions: `quotation-families/${family}/revisions/?limit=100&ordering=revision`,
  }
}

export function quotationIndexPaths() {
  return {
    families: "quotation-families/?limit=20&ordering=quotation_family_number",
    quotations:
      "quotations/?data_contract=MVP_V1&limit=20&ordering=-created_at",
  }
}

export async function fetchQuotationIndex(
  client: CanonicalClient,
  signal?: AbortSignal,
): Promise<QuotationIndex> {
  const paths = quotationIndexPaths()
  const [families, quotations] = await Promise.all([
    client.request<CanonicalPage<CanonicalQuotationFamily>>(paths.families, {
      signal,
    }),
    client.request<CanonicalPage<CanonicalQuotationSummary>>(paths.quotations, {
      signal,
    }),
  ])
  if (!isPage(families, isQuotationFamily)) {
    protocolError("invalid_quotation_family_page")
  }
  if (!isPage(quotations, isQuotationSummary)) {
    protocolError("invalid_quotation_page")
  }
  return { families, quotations }
}

export async function fetchQuotationWorkspace(
  client: CanonicalClient,
  quotationId: number,
  familyNumber?: string | null,
  signal?: AbortSignal,
): Promise<QuotationWorkspaceData> {
  const id = positiveInteger(quotationId, "quotation_id")
  const quotation = await client.request<CanonicalQuotation>(
    `quotations/${id}/`,
    { signal },
  )
  if (!isQuotation(quotation) || quotation.data_contract !== "MVP_V1") {
    protocolError("invalid_quotation_detail")
  }
  const authoritativeFamily = quotation.quotation_family_number
  if (
    authoritativeFamily === null ||
    (familyNumber !== undefined &&
      familyNumber !== null &&
      familyNumber !== authoritativeFamily)
  ) {
    protocolError("invalid_quotation_family")
  }
  const paths = quotationReadPaths(id, authoritativeFamily)
  const [lines, family, revisions, approvals, customerDecisions] =
    await Promise.all([
      client.request<CanonicalPage<CanonicalQuotationLine>>(paths.lines, {
        signal,
      }),
      client.request<CanonicalQuotationFamily>(paths.family, { signal }),
      client.request<CanonicalPage<CanonicalQuotationSummary>>(
        paths.revisions,
        { signal },
      ),
      client.request<CanonicalPage<CanonicalApprovalDecision>>(
        paths.approvals,
        { signal },
      ),
      client.request<CanonicalPage<CanonicalCustomerDecision>>(
        paths.customerDecisions,
        { signal },
      ),
    ])
  if (!isPage(lines, isQuotationLine)) protocolError("invalid_quotation_lines")
  if (!isQuotationFamily(family)) protocolError("invalid_quotation_family")
  if (!isPage(revisions, isQuotationSummary)) {
    protocolError("invalid_quotation_revisions")
  }
  if (!isPage(approvals, isApprovalDecision)) {
    protocolError("invalid_quotation_approvals")
  }
  if (!isPage(customerDecisions, isCustomerDecision)) {
    protocolError("invalid_quotation_customer_decisions")
  }
  return {
    quotation,
    lines: lines.results,
    family,
    revisions: revisions.results,
    approvals: approvals.results,
    customerDecisions: customerDecisions.results,
  }
}

function validationError(fieldErrors: Record<string, string>): never {
  throw new CanonicalClientError({
    kind: "validation",
    code: "client_validation_error",
    message: "Quotation input validation failed.",
    details: fieldErrors,
  })
}

function rejectUnknownFields(
  value: Record<string, unknown>,
  allowed: readonly string[],
): void {
  const unknown = Object.keys(value).filter((key) => !allowed.includes(key))
  if (unknown.length > 0) {
    validationError({ unknown_fields: "Có trường dữ liệu không hỗ trợ." })
  }
}

type TextOptions = {
  required?: boolean
  maxLength?: number
}

function text(
  value: unknown,
  field: string,
  options: TextOptions = {},
): string {
  if (typeof value !== "string") {
    validationError({ [field]: "Giá trị văn bản không hợp lệ." })
  }
  const normalized = value.trim()
  if (options.required && !normalized) {
    validationError({ [field]: "Trường này là bắt buộc." })
  }
  if (
    options.maxLength !== undefined &&
    normalized.length > options.maxLength
  ) {
    validationError({ [field]: `Không vượt quá ${options.maxLength} ký tự.` })
  }
  return normalized
}

function dateValue(value: unknown, field: string): string {
  if (typeof value !== "string" || !DATE_PATTERN.test(value)) {
    validationError({ [field]: "Ngày không hợp lệ." })
  }
  const parsed = new Date(`${value}T00:00:00Z`)
  if (
    Number.isNaN(parsed.getTime()) ||
    parsed.toISOString().slice(0, 10) !== value
  ) {
    validationError({ [field]: "Ngày không hợp lệ." })
  }
  return value
}

function decimalValue(value: unknown, field: string, positive = false): string {
  if (typeof value !== "string" || !DECIMAL_PATTERN.test(value)) {
    validationError({ [field]: "Phải là chuỗi số thập phân hợp lệ." })
  }
  const [whole, fraction = ""] = value.split(".")
  const wholeDigits = whole.replace(/^0+/, "").length
  if (wholeDigits > 16 || wholeDigits + fraction.length > 20) {
    validationError({ [field]: "Không vượt quá 20 chữ số và 4 số lẻ." })
  }
  const numeric = Number(value)
  if (!Number.isFinite(numeric) || numeric < 0 || (positive && numeric <= 0)) {
    validationError({ [field]: "Giá trị số không hợp lệ." })
  }
  return value
}

function pricingLines(value: unknown): QuotationPricingLinePayload[] {
  if (!Array.isArray(value) || value.length === 0) {
    validationError({ lines: "Cần ít nhất một dòng báo giá." })
  }
  const seen = new Set<number>()
  return value.map((item, index) => {
    if (!isRecord(item)) validationError({ lines: "Dòng giá không hợp lệ." })
    rejectUnknownFields(item, ["source_rfq_line_id", "unit_price", "discount"])
    const sourceId = positiveInteger(
      item.source_rfq_line_id,
      `lines.${index}.source_rfq_line_id`,
    )
    if (seen.has(sourceId)) {
      validationError({ lines: "Mỗi dòng RFQ chỉ được định giá một lần." })
    }
    seen.add(sourceId)
    const result: QuotationPricingLinePayload = {
      source_rfq_line_id: sourceId,
      unit_price: decimalValue(
        item.unit_price,
        `lines.${index}.unit_price`,
        true,
      ),
    }
    if (item.discount !== undefined) {
      result.discount = decimalValue(item.discount, `lines.${index}.discount`)
    }
    return result
  })
}

function commercialPayload(
  input: unknown,
  partial: boolean,
): QuotationCreatePayload | QuotationUpdatePayload {
  if (!isRecord(input)) validationError({ form: "Dữ liệu không hợp lệ." })
  rejectUnknownFields(input, [
    "currency",
    "valid_from",
    "valid_until",
    "discount_total",
    "tax_amount",
    "terms",
    "lines",
  ])
  if (partial && Object.keys(input).length === 0) {
    validationError({ form: "Cần ít nhất một trường để cập nhật." })
  }
  const result: QuotationUpdatePayload = {}
  if (!partial || input.currency !== undefined) {
    if (input.currency !== "VND" && input.currency !== "USD") {
      validationError({ currency: "Tiền tệ phải là VND hoặc USD." })
    }
    result.currency = input.currency
  }
  if (!partial || input.valid_from !== undefined) {
    result.valid_from = dateValue(input.valid_from, "valid_from")
  }
  if (!partial || input.valid_until !== undefined) {
    result.valid_until = dateValue(input.valid_until, "valid_until")
  }
  if (
    result.valid_from !== undefined &&
    result.valid_until !== undefined &&
    result.valid_until < result.valid_from
  ) {
    validationError({ valid_until: "Ngày hết hạn không trước ngày hiệu lực." })
  }
  if (input.discount_total !== undefined) {
    result.discount_total = decimalValue(input.discount_total, "discount_total")
  }
  if (input.tax_amount !== undefined) {
    result.tax_amount = decimalValue(input.tax_amount, "tax_amount")
  }
  if (input.terms !== undefined) result.terms = text(input.terms, "terms")
  if (!partial || input.lines !== undefined)
    result.lines = pricingLines(input.lines)
  return result
}

export function validateQuotationCreatePayload(
  input: unknown,
): QuotationCreatePayload {
  return commercialPayload(input, false) as QuotationCreatePayload
}

export function validateQuotationUpdatePayload(
  input: unknown,
): QuotationUpdatePayload {
  return commercialPayload(input, true)
}

export function validateQuotationSendPayload(
  input: unknown,
): QuotationSendPayload {
  if (!isRecord(input)) validationError({ form: "Dữ liệu gửi không hợp lệ." })
  rejectUnknownFields(input, ["sent_to", "evidence"])
  return {
    sent_to: text(input.sent_to, "sent_to", { required: true, maxLength: 254 }),
    evidence: text(input.evidence, "evidence", { required: true }),
  }
}

export function validateQuotationDecisionPayload(
  input: unknown,
  decision: "ACCEPTED" | "DECLINED",
): QuotationCustomerDecisionPayload {
  if (!isRecord(input)) validationError({ form: "Quyết định không hợp lệ." })
  rejectUnknownFields(input, ["contact_snapshot", "evidence", "reason"])
  const result: QuotationCustomerDecisionPayload = {
    contact_snapshot: text(input.contact_snapshot, "contact_snapshot", {
      required: true,
      maxLength: 254,
    }),
    evidence: text(input.evidence, "evidence", { required: true }),
  }
  const reason = text(input.reason ?? "", "reason", {
    required: decision === "DECLINED",
  })
  if (reason || input.reason !== undefined) result.reason = reason
  return result
}

export function validateQuotationRejectionPayload(input: unknown) {
  if (!isRecord(input)) validationError({ form: "Quyết định không hợp lệ." })
  rejectUnknownFields(input, ["reason", "notes"])
  return {
    reason: text(input.reason, "reason", { required: true }),
    notes: text(input.notes ?? "", "notes"),
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

export async function createQuotation(
  client: CanonicalClient,
  target: QuotationCreateTarget,
  payload: QuotationCreatePayload,
  idempotencyKey: string,
  signal?: AbortSignal,
): Promise<CanonicalQuotation> {
  const path =
    target.kind === "initial"
      ? `rfqs/${positiveInteger(target.rfqId, "rfq_id")}/quotations/commands/create/`
      : `quotations/${positiveInteger(target.quotationId, "quotation_id")}/commands/create-revision/`
  const quotation = await post<CanonicalQuotation>(
    client,
    path,
    payload,
    signal,
    idempotencyKey,
  )
  if (!isQuotation(quotation)) protocolError("invalid_quotation_command")
  return quotation
}

export async function updateQuotation(
  client: CanonicalClient,
  quotationId: number,
  payload: QuotationUpdatePayload,
  signal?: AbortSignal,
) {
  const quotation = await post<CanonicalQuotation>(
    client,
    `quotations/${positiveInteger(quotationId, "quotation_id")}/commands/update/`,
    payload,
    signal,
  )
  if (!isQuotation(quotation)) protocolError("invalid_quotation_command")
  return quotation
}

async function simpleQuotationCommand(
  client: CanonicalClient,
  quotationId: number,
  action: "archive" | "submit" | "send",
  payload: object,
  signal?: AbortSignal,
) {
  const quotation = await post<CanonicalQuotation>(
    client,
    `quotations/${positiveInteger(quotationId, "quotation_id")}/commands/${action}/`,
    payload,
    signal,
  )
  if (!isQuotation(quotation)) protocolError("invalid_quotation_command")
  return quotation
}

export const archiveQuotation = (
  client: CanonicalClient,
  quotationId: number,
  signal?: AbortSignal,
) => simpleQuotationCommand(client, quotationId, "archive", {}, signal)

export const submitQuotation = (
  client: CanonicalClient,
  quotationId: number,
  signal?: AbortSignal,
) => simpleQuotationCommand(client, quotationId, "submit", {}, signal)

export const sendQuotation = (
  client: CanonicalClient,
  quotationId: number,
  payload: QuotationSendPayload,
  signal?: AbortSignal,
) => simpleQuotationCommand(client, quotationId, "send", payload, signal)

function isDecisionResult(
  value: unknown,
  decisionGuard: (item: unknown) => boolean,
): value is DecisionCommandResult {
  return (
    isRecord(value) &&
    isQuotation(value.quotation) &&
    decisionGuard(value.decision)
  )
}

type DecisionCommandResult = {
  quotation: CanonicalQuotation
  decision: unknown
}

type ApprovalCommandPayload = {
  notes?: string
}

type RejectionCommandPayload = ApprovalCommandPayload & { reason: string }

function validateQuotationApprovalPayload(input: unknown) {
  if (!isRecord(input)) validationError({ form: "Quyết định không hợp lệ." })
  rejectUnknownFields(input, ["notes"])
  return { notes: text(input.notes ?? "", "notes") }
}

export async function decideQuotation(
  client: CanonicalClient,
  quotationId: number,
  decision: "approve" | "reject",
  payload: ApprovalCommandPayload | RejectionCommandPayload,
  signal?: AbortSignal,
) {
  const validatedPayload =
    decision === "approve"
      ? validateQuotationApprovalPayload(payload)
      : validateQuotationRejectionPayload(payload)
  const result = await post<unknown>(
    client,
    `quotations/${positiveInteger(quotationId, "quotation_id")}/commands/${decision}/`,
    validatedPayload,
    signal,
  )
  if (!isDecisionResult(result, isApprovalDecision)) {
    protocolError("invalid_quotation_decision")
  }
  return result as {
    quotation: CanonicalQuotation
    decision: CanonicalApprovalDecision
  }
}

export async function recordQuotationCustomerDecision(
  client: CanonicalClient,
  quotationId: number,
  decision: "accept" | "decline",
  payload: QuotationCustomerDecisionPayload,
  signal?: AbortSignal,
) {
  const result = await post<unknown>(
    client,
    `quotations/${positiveInteger(quotationId, "quotation_id")}/commands/${decision}/`,
    payload,
    signal,
  )
  if (!isDecisionResult(result, isCustomerDecision)) {
    protocolError("invalid_customer_decision")
  }
  return result as {
    quotation: CanonicalQuotation
    decision: CanonicalCustomerDecision
  }
}

function clonePayload(payload: QuotationCreatePayload): QuotationCreatePayload {
  return {
    ...payload,
    lines: payload.lines.map((line) => ({ ...line })),
  }
}

export function shouldRetainQuotationAttempt(error: unknown): boolean {
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

export function createQuotationAttemptManager(
  keyFactory: () => string = () => crypto.randomUUID(),
) {
  let active: CreateAttempt | null = null
  return {
    begin(
      target: QuotationCreateTarget,
      payload: QuotationCreatePayload,
    ): CreateAttempt {
      if (active !== null) return active
      const key = keyFactory()
      if (!IDEMPOTENCY_KEY_PATTERN.test(key)) {
        protocolError("invalid_idempotency_key_factory")
      }
      active = {
        target: { ...target },
        key,
        payload: clonePayload(payload),
        createdQuotationId: null,
        familyNumber: null,
      }
      return active
    },
    markCreated(
      attempt: CreateAttempt,
      quotationId: number,
      familyNumber: string | null,
    ) {
      if (active !== attempt) return
      if (familyNumber === null) protocolError("invalid_quotation_family")
      active.createdQuotationId = positiveInteger(quotationId, "quotation_id")
      active.familyNumber = familyNumber
    },
    fail(attempt: CreateAttempt, error: unknown) {
      if (
        active === attempt &&
        active.createdQuotationId === null &&
        !shouldRetainQuotationAttempt(error)
      ) {
        active = null
      }
    },
    complete(attempt: CreateAttempt) {
      if (active === attempt) active = null
    },
    reset() {
      active = null
    },
    hasActiveAttempt() {
      return active !== null
    },
    hasCreatedQuotation() {
      return active?.createdQuotationId !== null && active !== null
    },
    activePayload() {
      return active === null ? null : clonePayload(active.payload)
    },
    activeTarget() {
      return active === null ? null : { ...active.target }
    },
  }
}

export async function executeQuotationCreateAttempt(
  client: CanonicalClient,
  manager: ReturnType<typeof createQuotationAttemptManager>,
  target: QuotationCreateTarget,
  payload: QuotationCreatePayload,
  reconcile: (
    quotationId: number,
    familyNumber: string,
    signal?: AbortSignal,
  ) => Promise<QuotationWorkspaceData>,
  signal?: AbortSignal,
) {
  const attempt = manager.begin(target, payload)
  try {
    if (attempt.createdQuotationId === null) {
      const quotation = await createQuotation(
        client,
        attempt.target,
        attempt.payload,
        attempt.key,
        signal,
      )
      manager.markCreated(
        attempt,
        quotation.id,
        quotation.quotation_family_number,
      )
    }
    const result = await reconcile(
      attempt.createdQuotationId!,
      attempt.familyNumber!,
      signal,
    )
    manager.complete(attempt)
    return result
  } catch (error) {
    manager.fail(attempt, error)
    throw error
  }
}

export function quotationLifecyclePermissions(
  role: string | null,
  status: QuotationWorkflowStatus | null,
  locked: boolean,
) {
  const salesActor = role === "Admin" || role === "Sales"
  const manager = role === "Manager"
  return {
    update: salesActor && status === "DRAFT" && !locked,
    archive: salesActor && status === "DRAFT" && !locked,
    submit: salesActor && status === "DRAFT" && !locked,
    createRevision: salesActor && status === "REJECTED" && !locked,
    send: salesActor && status === "APPROVED" && !locked,
    accept: salesActor && status === "SENT" && !locked,
    decline: salesActor && status === "SENT" && !locked,
    approve: manager && status === "PENDING_APPROVAL" && !locked,
    reject: manager && status === "PENDING_APPROVAL" && !locked,
  }
}

export function canCreateInitialQuotation(
  role: string | null,
  rfqStatus: string | null,
  locked: boolean,
) {
  return (
    (role === "Admin" || role === "Sales") &&
    rfqStatus === "READY_TO_QUOTE" &&
    !locked
  )
}

const OWNER_ACTIONS = new Set<QuotationAction>([
  "create",
  "create_revision",
  "update",
  "archive",
  "submit",
  "send",
  "accept",
  "decline",
])

const ALLOWED_ERROR_FIELDS = new Set([
  "form",
  "non_field_errors",
  "unknown_fields",
  "currency",
  "valid_from",
  "valid_until",
  "discount_total",
  "tax_amount",
  "terms",
  "lines",
  "sent_to",
  "sent_evidence",
  "evidence",
  "contact_snapshot",
  "reason",
  "notes",
  "quotation",
  "reviewer",
])

function safeFieldErrors(details: unknown) {
  if (!isRecord(details)) return undefined
  const result: Record<string, string> = {}
  for (const key of Object.keys(details)) {
    if (ALLOWED_ERROR_FIELDS.has(key)) {
      result[key] = "Giá trị không được máy chủ chấp nhận."
    }
  }
  return Object.keys(result).length > 0 ? result : undefined
}

export function quotationCommandStateFromError(
  error: unknown,
  action?: QuotationAction,
): QuotationCommandState {
  if (!(error instanceof CanonicalClientError)) {
    return { status: "protocol", message: "Phản hồi báo giá không hợp lệ." }
  }
  if (error.kind === "authentication") {
    return {
      status: "authentication_failure",
      message: "Phiên đăng nhập đã hết hạn.",
    }
  }
  if (error.kind === "permission") {
    if (action !== undefined && OWNER_ACTIONS.has(action)) {
      return {
        status: "ownership_denied",
        message: "Bạn không có quyền hoặc không sở hữu báo giá này.",
      }
    }
    return {
      status: "permission_denied",
      message: "Bạn không có quyền thực hiện thao tác này.",
    }
  }
  if (error.kind === "validation") {
    const errors = safeFieldErrors(error.details)
    if (errors?.reviewer) {
      return {
        status: "maker_checker_denied",
        message: "Người tạo báo giá không thể tự phê duyệt hoặc từ chối.",
        fieldErrors: errors,
      }
    }
    return {
      status: "field_validation",
      message: "Kiểm tra lại dữ liệu báo giá.",
      fieldErrors: errors,
    }
  }
  if (error.kind === "conflict") {
    return error.code === "idempotency_conflict"
      ? {
          status: "idempotency_conflict",
          message: "Retry xung đột với logical attempt trước.",
        }
      : {
          status: "lifecycle_conflict",
          message: "Trạng thái báo giá không cho phép thao tác này.",
        }
  }
  if (error.kind === "timeout") {
    return {
      status: "timeout",
      message: "Không xác định được kết quả; hãy đồng bộ lại báo giá.",
    }
  }
  if (error.kind === "network") {
    return {
      status: "network",
      message: "Mất kết nối; hãy đồng bộ lại báo giá.",
    }
  }
  if (error.kind === "cancelled") {
    return { status: "cancelled", message: "Yêu cầu báo giá đã bị hủy." }
  }
  if (error.kind === "server") {
    return { status: "server", message: "Máy chủ chưa thể xử lý lệnh báo giá." }
  }
  return { status: "protocol", message: "Phản hồi báo giá không hợp lệ." }
}

export function settleQuotationCommandOnDeactivate(
  state: QuotationCommandState,
): QuotationCommandState {
  return state.status === "pending"
    ? {
        status: "cancelled",
        message:
          "Yêu cầu đang chờ đã bị hủy; hãy đồng bộ hoặc thử lại khi quay lại.",
      }
    : state
}

export function createQuotationCommandGate() {
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

export function createQuotationRequestGuards() {
  return {
    index: createLatestRequestGuard(),
    workspace: createLatestRequestGuard(),
    rfqLines: createLatestRequestGuard(),
  }
}
