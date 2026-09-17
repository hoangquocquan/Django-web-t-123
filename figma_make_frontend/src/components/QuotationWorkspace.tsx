import { useEffect, useMemo, useRef, useState } from "react"

import { CanonicalClientError } from "../api/canonical.ts"
import {
  archiveQuotation,
  canCreateInitialQuotation,
  createQuotationAttemptManager,
  createQuotationCommandGate,
  createQuotationRequestGuards,
  decideQuotation,
  executeQuotationCreateAttempt,
  fetchQuotationIndex,
  fetchQuotationWorkspace,
  quotationCommandStateFromError,
  quotationLifecyclePermissions,
  recordQuotationCustomerDecision,
  sendQuotation,
  settleQuotationCommandOnDeactivate,
  submitQuotation,
  updateQuotation,
  validateQuotationCreatePayload,
  validateQuotationDecisionPayload,
  validateQuotationRejectionPayload,
  validateQuotationSendPayload,
  validateQuotationUpdatePayload,
  type CanonicalClient,
  type CanonicalQuotation,
  type CanonicalQuotationLine,
  type QuotationAction,
  type QuotationCommandState,
  type QuotationCreatePayload,
  type QuotationIndex,
  type QuotationWorkspaceData,
} from "../api/quotationCommands.ts"
import { fetchRfqLines, type CanonicalRfqLine } from "../api/rfqCommands.ts"
import type { CanonicalRfq, RfqViewState } from "../api/rfq.ts"

type CommercialForm = {
  currency: "VND" | "USD"
  validFrom: string
  validUntil: string
  discountTotal: string
  taxAmount: string
  terms: string
  lines: Array<{
    sourceRfqLineId: number
    unitPrice: string
    discount: string
  }>
}

const emptyForm: CommercialForm = {
  currency: "VND",
  validFrom: "",
  validUntil: "",
  discountTotal: "0",
  taxAmount: "0",
  terms: "",
  lines: [],
}

const inputClass =
  "w-full border border-white/10 bg-zinc-950 px-3 py-2 text-sm outline-none focus:border-orange-500 focus-visible:ring-2 focus-visible:ring-orange-400 disabled:cursor-not-allowed disabled:opacity-50"
const buttonClass =
  "bg-orange-600 px-4 py-2 text-xs font-semibold uppercase tracking-widest text-white hover:bg-orange-500 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-400 focus-visible:ring-offset-2 focus-visible:ring-offset-zinc-950 disabled:cursor-not-allowed disabled:opacity-50"
const ghostButtonClass =
  "border border-white/20 px-4 py-2 text-xs uppercase tracking-widest hover:border-orange-500 hover:text-orange-400 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-400 focus-visible:ring-offset-2 focus-visible:ring-offset-zinc-950 disabled:cursor-not-allowed disabled:opacity-50"

function formFromWorkspace(data: QuotationWorkspaceData): CommercialForm {
  return {
    currency: data.quotation.currency === "USD" ? "USD" : "VND",
    validFrom: data.quotation.valid_from ?? "",
    validUntil: data.quotation.valid_until ?? "",
    discountTotal: data.quotation.discount_total,
    taxAmount: data.quotation.tax_amount,
    terms: data.quotation.terms,
    lines: data.lines.map((line) => ({
      sourceRfqLineId: line.source_rfq_line_id,
      unitPrice: line.unit_price,
      discount: line.discount,
    })),
  }
}

function formFromRfqLines(lines: CanonicalRfqLine[]): CommercialForm {
  const today = new Date().toISOString().slice(0, 10)
  return {
    ...emptyForm,
    validFrom: today,
    lines: lines.map((line) => ({
      sourceRfqLineId: line.id,
      unitPrice: "",
      discount: "0",
    })),
  }
}

function formPayload(form: CommercialForm): QuotationCreatePayload {
  return validateQuotationCreatePayload({
    currency: form.currency,
    valid_from: form.validFrom,
    valid_until: form.validUntil,
    discount_total: form.discountTotal,
    tax_amount: form.taxAmount,
    terms: form.terms,
    lines: form.lines.map((line) => ({
      source_rfq_line_id: line.sourceRfqLineId,
      unit_price: line.unitPrice,
      discount: line.discount,
    })),
  })
}

function FieldError({
  state,
  name,
}: {
  state: QuotationCommandState
  name: string
}) {
  const message = state.fieldErrors?.[name]
  return message ? (
    <p className="text-xs text-orange-400" role="alert">
      {message}
    </p>
  ) : null
}

function sourceLineLabel(
  sourceId: number,
  quotationLines: CanonicalQuotationLine[],
  rfqLines: CanonicalRfqLine[],
) {
  const quotationLine = quotationLines.find(
    (line) => line.source_rfq_line_id === sourceId,
  )
  if (quotationLine) {
    return `#${quotationLine.line_number} · ${quotationLine.description} · ${quotationLine.quantity} ${quotationLine.unit} · total ${quotationLine.line_total}`
  }
  const rfqLine = rfqLines.find((line) => line.id === sourceId)
  return rfqLine
    ? `RFQ #${rfqLine.line_number} · ${rfqLine.description} · ${rfqLine.quantity} ${rfqLine.unit}`
    : `RFQ line #${sourceId}`
}

function safeEvidence(value: string) {
  return value.trim().slice(0, 500)
}

export default function QuotationWorkspace({
  client,
  authenticated,
  role,
  active,
  rfqState,
  reloadRfqs,
  goToLogin,
  onAuthenticationFailure,
}: {
  client: CanonicalClient
  authenticated: boolean
  role: string | null
  active: boolean
  rfqState: RfqViewState
  reloadRfqs: () => void
  goToLogin: () => void
  onAuthenticationFailure: () => void
}) {
  const [index, setIndex] = useState<QuotationIndex | null>(null)
  const [indexState, setIndexState] = useState<QuotationCommandState>({
    status: "initial",
    message: "Chưa tải danh sách báo giá.",
  })
  const [command, setCommand] = useState<QuotationCommandState>({
    status: "initial",
    message: "Chọn quotation family hoặc RFQ đủ điều kiện.",
  })
  const [workspace, setWorkspace] = useState<QuotationWorkspaceData | null>(
    null,
  )
  const [selectedRfqId, setSelectedRfqId] = useState("")
  const [rfqLines, setRfqLines] = useState<CanonicalRfqLine[]>([])
  const [form, setForm] = useState<CommercialForm>(emptyForm)
  const [approvalNotes, setApprovalNotes] = useState("")
  const [rejectionReason, setRejectionReason] = useState("")
  const [rejectionNotes, setRejectionNotes] = useState("")
  const [sentTo, setSentTo] = useState("")
  const [sendEvidence, setSendEvidence] = useState("")
  const [customerContact, setCustomerContact] = useState("")
  const [customerEvidence, setCustomerEvidence] = useState("")
  const [declineReason, setDeclineReason] = useState("")
  const gate = useMemo(() => createQuotationCommandGate(), [])
  const attempt = useMemo(() => createQuotationAttemptManager(), [])
  const guards = useMemo(() => createQuotationRequestGuards(), [])
  const indexAbort = useRef<AbortController | null>(null)
  const workspaceAbort = useRef<AbortController | null>(null)
  const rfqLinesAbort = useRef<AbortController | null>(null)
  const pending = command.status === "pending"
  const needsReconciliation = [
    "timeout",
    "network",
    "protocol",
    "server",
    "cancelled",
  ].includes(command.status)
  const activeAttempt = attempt.hasActiveAttempt()
  const locked = pending || needsReconciliation || activeAttempt
  const selectedRfq =
    rfqState.status === "populated"
      ? (rfqState.page.results.find(
          (rfq) => String(rfq.id) === selectedRfqId,
        ) ?? null)
      : null
  const permissions = quotationLifecyclePermissions(
    role,
    workspace?.quotation.workflow_status ?? null,
    pending || needsReconciliation || activeAttempt,
  )
  const formEditable = workspace
    ? permissions.update || permissions.createRevision
    : canCreateInitialQuotation(role, selectedRfq?.status ?? null, locked)

  const handleError = (error: unknown, action?: QuotationAction) => {
    const next = quotationCommandStateFromError(error, action)
    setCommand(next)
    if (next.status === "authentication_failure") onAuthenticationFailure()
  }

  const loadIndex = () => {
    if (!authenticated || !active) return
    indexAbort.current?.abort()
    const controller = new AbortController()
    indexAbort.current = controller
    const requestId = guards.index.next()
    setIndexState({
      status: "loading",
      message: "Đang tải quotation families...",
    })
    void fetchQuotationIndex(client, controller.signal)
      .then((result) => {
        if (!guards.index.isLatest(requestId)) return
        setIndex(result)
        setIndexState({
          status: "ready",
          message:
            result.quotations.results.length === 0
              ? "Chưa có báo giá canonical."
              : `${result.families.count} quotation families`,
        })
      })
      .catch((error) => {
        if (!guards.index.isLatest(requestId)) return
        const next = quotationCommandStateFromError(error)
        setIndexState(next)
        if (next.status === "authentication_failure") onAuthenticationFailure()
      })
  }

  useEffect(() => {
    if (!authenticated) {
      indexAbort.current?.abort()
      workspaceAbort.current?.abort()
      rfqLinesAbort.current?.abort()
      guards.index.next()
      guards.workspace.next()
      guards.rfqLines.next()
      gate.finish()
      attempt.reset()
      setIndex(null)
      setWorkspace(null)
      setSelectedRfqId("")
      setRfqLines([])
      setForm(emptyForm)
      setApprovalNotes("")
      setRejectionReason("")
      setRejectionNotes("")
      setSentTo("")
      setSendEvidence("")
      setCustomerContact("")
      setCustomerEvidence("")
      setDeclineReason("")
      setIndexState({
        status: "initial",
        message: "Chưa tải danh sách báo giá.",
      })
      setCommand({
        status: "initial",
        message: "Chọn quotation family hoặc RFQ đủ điều kiện.",
      })
      return
    }
    if (!active) {
      indexAbort.current?.abort()
      workspaceAbort.current?.abort()
      rfqLinesAbort.current?.abort()
      guards.index.next()
      guards.workspace.next()
      guards.rfqLines.next()
      setCommand(settleQuotationCommandOnDeactivate)
      return
    }
    loadIndex()
  }, [active, authenticated, client])

  useEffect(
    () => () => {
      indexAbort.current?.abort()
      workspaceAbort.current?.abort()
      rfqLinesAbort.current?.abort()
      guards.index.next()
      guards.workspace.next()
      guards.rfqLines.next()
    },
    [],
  )

  const applyWorkspace = (data: QuotationWorkspaceData) => {
    setWorkspace(data)
    setSelectedRfqId("")
    setRfqLines([])
    setForm(formFromWorkspace(data))
    setApprovalNotes("")
    setRejectionReason("")
    setRejectionNotes("")
    setSentTo("")
    setSendEvidence("")
    setCustomerContact("")
    setCustomerEvidence("")
    setDeclineReason("")
  }

  const selectQuotation = (
    quotation: Pick<CanonicalQuotation, "id" | "quotation_family_number">,
  ) => {
    if (pending || activeAttempt) return
    workspaceAbort.current?.abort()
    const controller = new AbortController()
    workspaceAbort.current = controller
    const requestId = guards.workspace.next()
    setCommand({ status: "pending", message: "Đang tải chi tiết báo giá..." })
    void fetchQuotationWorkspace(
      client,
      quotation.id,
      quotation.quotation_family_number,
      controller.signal,
    )
      .then((data) => {
        if (!guards.workspace.isLatest(requestId)) return
        applyWorkspace(data)
        setCommand({ status: "ready", message: "Đã đồng bộ dữ liệu báo giá." })
      })
      .catch((error) => {
        if (guards.workspace.isLatest(requestId)) handleError(error)
      })
  }

  const selectSummary = (quotationId: number, familyNumber: string | null) => {
    selectQuotation({ id: quotationId, quotation_family_number: familyNumber })
  }

  const chooseRfq = (rfq: CanonicalRfq | null) => {
    if (pending || activeAttempt) return
    rfqLinesAbort.current?.abort()
    workspaceAbort.current?.abort()
    guards.workspace.next()
    setWorkspace(null)
    setSelectedRfqId(rfq ? String(rfq.id) : "")
    setRfqLines([])
    setForm(emptyForm)
    if (!rfq) return
    const controller = new AbortController()
    rfqLinesAbort.current = controller
    const requestId = guards.rfqLines.next()
    setCommand({ status: "pending", message: "Đang tải dòng RFQ nguồn..." })
    void fetchRfqLines(client, rfq.id, controller.signal)
      .then((lines) => {
        if (!guards.rfqLines.isLatest(requestId)) return
        setRfqLines(lines)
        setForm(formFromRfqLines(lines))
        setCommand({ status: "ready", message: "Sẵn sàng tạo quotation R0." })
      })
      .catch((error) => {
        if (guards.rfqLines.isLatest(requestId)) handleError(error, "create")
      })
  }

  const reconcile = (
    quotationId: number,
    familyNumber: string,
    signal?: AbortSignal,
  ) => fetchQuotationWorkspace(client, quotationId, familyNumber, signal)

  const finishAccepted = (data: QuotationWorkspaceData) => {
    applyWorkspace(data)
    setCommand({
      status: "accepted",
      message: "Lệnh đã được chấp nhận và đồng bộ.",
    })
    loadIndex()
    reloadRfqs()
  }

  const runCreate = () => {
    let payload = attempt.activePayload()
    let target = attempt.activeTarget()
    if (payload === null || target === null) {
      try {
        payload = formPayload(form)
        target = workspace
          ? { kind: "revision", quotationId: workspace.quotation.id }
          : { kind: "initial", rfqId: Number(selectedRfqId) }
      } catch (error) {
        handleError(error, workspace ? "create_revision" : "create")
        return
      }
    }
    if (!gate.tryStart()) return
    workspaceAbort.current?.abort()
    const controller = new AbortController()
    workspaceAbort.current = controller
    const requestId = guards.workspace.next()
    setCommand({ status: "pending", message: "Đang tạo revision báo giá..." })
    void executeQuotationCreateAttempt(
      client,
      attempt,
      target,
      payload,
      reconcile,
      controller.signal,
    )
      .then((data) => {
        if (!guards.workspace.isLatest(requestId)) return
        finishAccepted(data)
      })
      .catch((error) => {
        if (guards.workspace.isLatest(requestId)) {
          handleError(
            error,
            target.kind === "initial" ? "create" : "create_revision",
          )
        }
      })
      .finally(() => gate.finish())
  }

  const runCommand = (
    action: QuotationAction,
    operation: (signal: AbortSignal) => Promise<CanonicalQuotation>,
  ) => {
    if (!workspace || !gate.tryStart()) return
    workspaceAbort.current?.abort()
    const controller = new AbortController()
    workspaceAbort.current = controller
    const requestId = guards.workspace.next()
    setCommand({ status: "pending", message: "Đang gửi lệnh báo giá..." })
    void operation(controller.signal)
      .then((quotation) =>
        fetchQuotationWorkspace(
          client,
          quotation.id,
          quotation.quotation_family_number,
          controller.signal,
        ),
      )
      .then((data) => {
        if (!guards.workspace.isLatest(requestId)) return
        finishAccepted(data)
      })
      .catch((error) => {
        if (guards.workspace.isLatest(requestId)) handleError(error, action)
      })
      .finally(() => gate.finish())
  }

  const updateDraft = () => {
    if (!workspace || !permissions.update) return
    try {
      const payload = validateQuotationUpdatePayload({
        currency: form.currency,
        valid_from: form.validFrom,
        valid_until: form.validUntil,
        discount_total: form.discountTotal,
        tax_amount: form.taxAmount,
        terms: form.terms,
        lines: form.lines.map((line) => ({
          source_rfq_line_id: line.sourceRfqLineId,
          unit_price: line.unitPrice,
          discount: line.discount,
        })),
      })
      runCommand("update", (signal) =>
        updateQuotation(client, workspace.quotation.id, payload, signal),
      )
    } catch (error) {
      handleError(error, "update")
    }
  }

  const simpleAction = (action: "archive" | "submit") => {
    if (!workspace || !permissions[action]) return
    runCommand(action, (signal) =>
      action === "archive"
        ? archiveQuotation(client, workspace.quotation.id, signal)
        : submitQuotation(client, workspace.quotation.id, signal),
    )
  }

  const approvalAction = (decision: "approve" | "reject") => {
    if (!workspace || !permissions[decision]) return
    try {
      const payload =
        decision === "reject"
          ? validateQuotationRejectionPayload({
              reason: rejectionReason,
              notes: rejectionNotes,
            })
          : { notes: approvalNotes.trim() }
      runCommand(decision, (signal) =>
        decideQuotation(
          client,
          workspace.quotation.id,
          decision,
          payload,
          signal,
        ).then((result) => result.quotation),
      )
    } catch (error) {
      handleError(error, decision)
    }
  }

  const send = () => {
    if (!workspace || !permissions.send) return
    try {
      const payload = validateQuotationSendPayload({
        sent_to: sentTo,
        evidence: sendEvidence,
      })
      runCommand("send", (signal) =>
        sendQuotation(client, workspace.quotation.id, payload, signal),
      )
    } catch (error) {
      handleError(error, "send")
    }
  }

  const customerDecision = (decision: "accept" | "decline") => {
    if (!workspace || !permissions[decision]) return
    try {
      const payload = validateQuotationDecisionPayload(
        {
          contact_snapshot: customerContact,
          evidence: customerEvidence,
          reason: decision === "decline" ? declineReason : undefined,
        },
        decision === "accept" ? "ACCEPTED" : "DECLINED",
      )
      runCommand(decision, (signal) =>
        recordQuotationCustomerDecision(
          client,
          workspace.quotation.id,
          decision,
          payload,
          signal,
        ).then((result) => result.quotation),
      )
    } catch (error) {
      handleError(error, decision)
    }
  }

  if (!authenticated) {
    return (
      <div className="grid min-h-64 place-items-center border border-white/10 p-8 text-center">
        <div>
          <p>Đăng nhập để quản lý quotation lifecycle.</p>
          <button className={`${buttonClass} mt-5`} onClick={goToLogin}>
            Đăng nhập
          </button>
        </div>
      </div>
    )
  }

  const eligibleRfqs =
    rfqState.status === "populated"
      ? rfqState.page.results.filter((rfq) => rfq.status === "READY_TO_QUOTE")
      : []
  const quotationLines = workspace?.lines ?? []

  return (
    <div className="grid gap-6">
      <div className="flex flex-wrap items-center justify-between gap-3 border border-white/10 bg-zinc-900/30 p-4">
        <div>
          <div className="text-xs uppercase tracking-widest text-orange-500">
            Canonical quotation lifecycle · {role ?? "Chưa xác định role"}
          </div>
          <p
            aria-atomic="true"
            aria-live="polite"
            className="mt-1 text-sm text-zinc-400"
            role="status"
          >
            {command.message}
          </p>
        </div>
        <button
          className={ghostButtonClass}
          disabled={pending}
          onClick={loadIndex}
        >
          Tải lại quotation families
        </button>
      </div>

      {needsReconciliation && workspace && (
        <button
          className={buttonClass}
          disabled={pending}
          onClick={() => selectQuotation(workspace.quotation)}
        >
          Đồng bộ lại dữ liệu authoritative
        </button>
      )}

      <div className="grid gap-6 xl:grid-cols-[minmax(300px,.7fr)_minmax(0,1.3fr)]">
        <div className="grid content-start gap-5">
          <div className="border border-white/10 p-5">
            <h3 className="font-serif text-2xl">Tạo từ RFQ</h3>
            <select
              aria-label="RFQ sẵn sàng tạo quotation"
              data-testid="quotation-rfq-selector"
              className={`${inputClass} mt-4`}
              disabled={pending || activeAttempt}
              value={selectedRfqId}
              onChange={(event) => {
                const rfq = eligibleRfqs.find(
                  (item) => String(item.id) === event.currentTarget.value,
                )
                chooseRfq(rfq ?? null)
              }}
            >
              <option value="">Chọn RFQ READY_TO_QUOTE</option>
              {eligibleRfqs.map((rfq) => (
                <option key={rfq.id} value={rfq.id}>
                  {rfq.rfq_number} · {rfq.project_name || "Không tên"}
                </option>
              ))}
            </select>
            {eligibleRfqs.length === 0 && (
              <p className="mt-3 text-xs text-zinc-500">
                Không có RFQ READY_TO_QUOTE trong trang canonical hiện tại.
              </p>
            )}
          </div>

          <div className="border border-white/10 p-5">
            <h3 className="font-serif text-2xl">Quotation families</h3>
            <p className="mt-2 text-sm text-zinc-500">{indexState.message}</p>
            <div className="mt-4 grid gap-3">
              {index?.families.results.map((family) => (
                <div
                  className="border border-white/10 p-3"
                  data-rfq-number={family.rfq_number}
                  key={family.quotation_family_number}
                >
                  <div className="text-sm font-semibold">
                    {family.quotation_family_number}
                  </div>
                  <div className="mt-1 text-xs text-zinc-500">
                    {family.rfq_number} · {family.revision_count} revision
                  </div>
                  <div className="mt-3 flex flex-wrap gap-2">
                    {family.revisions.map((revision) => (
                      <button
                        className={ghostButtonClass}
                        data-quotation-id={revision.id}
                        data-quotation-status={revision.workflow_status}
                        disabled={pending || activeAttempt}
                        key={revision.id}
                        onClick={() =>
                          selectSummary(
                            revision.id,
                            revision.quotation_family_number,
                          )
                        }
                      >
                        R{revision.revision} · {revision.workflow_status}
                      </button>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="grid content-start gap-5">
          {workspace && (
            <div
              className="border border-white/10 bg-[#0b0d0f] p-5"
              data-quotation-status={workspace.quotation.workflow_status}
              data-testid="quotation-workspace-detail"
            >
              <div className="flex flex-wrap justify-between gap-4">
                <div>
                  <div className="text-xs uppercase tracking-widest text-orange-500">
                    {workspace.family.quotation_family_number} · R
                    {workspace.quotation.revision}
                  </div>
                  <h3 className="mt-2 font-serif text-3xl">
                    {workspace.quotation.quotation_number}
                  </h3>
                </div>
                <div className="text-right">
                  <div className="text-sm text-orange-400">
                    {workspace.quotation.workflow_status}
                  </div>
                  <div className="mt-2 text-2xl font-semibold">
                    {workspace.quotation.total} {workspace.quotation.currency}
                  </div>
                </div>
              </div>
              <div className="mt-4 grid gap-2 text-sm text-zinc-400 sm:grid-cols-3">
                <span>Subtotal: {workspace.quotation.subtotal}</span>
                <span>Discount: {workspace.quotation.discount_total}</span>
                <span>Tax: {workspace.quotation.tax_amount}</span>
              </div>
              <div className="mt-5 flex flex-wrap gap-2">
                {workspace.revisions.map((revision) => (
                  <button
                    className={ghostButtonClass}
                    disabled={pending || activeAttempt}
                    key={revision.id}
                    onClick={() =>
                      selectSummary(
                        revision.id,
                        revision.quotation_family_number,
                      )
                    }
                  >
                    R{revision.revision} · {revision.workflow_status}
                  </button>
                ))}
              </div>
            </div>
          )}

          {(selectedRfq || workspace) && (
            <div className="border border-white/10 bg-[#0b0d0f] p-5">
              <h3 className="font-serif text-2xl">
                {workspace
                  ? permissions.createRevision
                    ? "Tạo revision kế tiếp"
                    : "Commercial snapshot"
                  : "Tạo quotation R0"}
              </h3>
              <div className="mt-5 grid gap-4">
                <div className="grid gap-4 sm:grid-cols-3">
                  <select
                    aria-label="Tiền tệ"
                    className={inputClass}
                    disabled={!formEditable}
                    value={form.currency}
                    onChange={(event) =>
                      setForm({
                        ...form,
                        currency: event.currentTarget.value as "VND" | "USD",
                      })
                    }
                  >
                    <option>VND</option>
                    <option>USD</option>
                  </select>
                  <input
                    aria-label="Ngày hiệu lực"
                    className={inputClass}
                    data-testid="quotation-valid-from"
                    disabled={!formEditable}
                    type="date"
                    value={form.validFrom}
                    onChange={(event) =>
                      setForm({ ...form, validFrom: event.currentTarget.value })
                    }
                  />
                  <input
                    aria-label="Ngày hết hạn"
                    className={inputClass}
                    data-testid="quotation-valid-until"
                    disabled={!formEditable}
                    type="date"
                    value={form.validUntil}
                    onChange={(event) =>
                      setForm({
                        ...form,
                        validUntil: event.currentTarget.value,
                      })
                    }
                  />
                </div>
                <div className="grid gap-4 sm:grid-cols-2">
                  <input
                    aria-label="Tổng chiết khấu"
                    className={inputClass}
                    disabled={!formEditable}
                    inputMode="decimal"
                    placeholder="Tổng chiết khấu"
                    value={form.discountTotal}
                    onChange={(event) =>
                      setForm({
                        ...form,
                        discountTotal: event.currentTarget.value,
                      })
                    }
                  />
                  <input
                    aria-label="Thuế"
                    className={inputClass}
                    disabled={!formEditable}
                    inputMode="decimal"
                    placeholder="Thuế"
                    value={form.taxAmount}
                    onChange={(event) =>
                      setForm({ ...form, taxAmount: event.currentTarget.value })
                    }
                  />
                </div>
                <textarea
                  aria-label="Điều khoản"
                  className={inputClass}
                  disabled={!formEditable}
                  placeholder="Điều khoản"
                  value={form.terms}
                  onChange={(event) =>
                    setForm({ ...form, terms: event.currentTarget.value })
                  }
                />
                <div className="grid gap-3">
                  {form.lines.map((line, index) => (
                    <div
                      className="grid gap-3 border border-white/10 p-3 sm:grid-cols-[1fr_160px_160px]"
                      key={line.sourceRfqLineId}
                    >
                      <span className="text-sm text-zinc-400">
                        {sourceLineLabel(
                          line.sourceRfqLineId,
                          quotationLines,
                          rfqLines,
                        )}
                      </span>
                      <input
                        aria-label={`Đơn giá dòng ${index + 1}`}
                        className={inputClass}
                        data-testid="quotation-unit-price"
                        disabled={!formEditable}
                        inputMode="decimal"
                        placeholder="Đơn giá"
                        value={line.unitPrice}
                        onChange={(event) => {
                          const lines = form.lines.map((item, itemIndex) =>
                            itemIndex === index
                              ? {
                                  ...item,
                                  unitPrice: event.currentTarget.value,
                                }
                              : item,
                          )
                          setForm({ ...form, lines })
                        }}
                      />
                      <input
                        aria-label={`Chiết khấu dòng ${index + 1}`}
                        className={inputClass}
                        disabled={!formEditable}
                        inputMode="decimal"
                        placeholder="Chiết khấu"
                        value={line.discount}
                        onChange={(event) => {
                          const lines = form.lines.map((item, itemIndex) =>
                            itemIndex === index
                              ? { ...item, discount: event.currentTarget.value }
                              : item,
                          )
                          setForm({ ...form, lines })
                        }}
                      />
                    </div>
                  ))}
                </div>
                <FieldError state={command} name="lines" />
                <FieldError state={command} name="valid_until" />
                <div className="flex flex-wrap gap-3">
                  {!workspace && (
                    <button
                      className={buttonClass}
                      disabled={
                        pending ||
                        (!activeAttempt &&
                          (!formEditable || form.lines.length === 0))
                      }
                      onClick={runCreate}
                    >
                      {activeAttempt ? "Thử lại tạo R0" : "Tạo quotation R0"}
                    </button>
                  )}
                  {workspace && permissions.update && (
                    <button className={buttonClass} onClick={updateDraft}>
                      Lưu DRAFT
                    </button>
                  )}
                  {workspace && permissions.createRevision && (
                    <button
                      className={buttonClass}
                      disabled={!formEditable}
                      onClick={runCreate}
                    >
                      {activeAttempt ? "Thử lại revision" : "Tạo revision mới"}
                    </button>
                  )}
                  {workspace && activeAttempt && (
                    <button
                      className={buttonClass}
                      disabled={pending}
                      onClick={runCreate}
                    >
                      Thử lại revision
                    </button>
                  )}
                  {workspace && permissions.archive && (
                    <button
                      className={ghostButtonClass}
                      onClick={() => simpleAction("archive")}
                    >
                      Archive DRAFT
                    </button>
                  )}
                  {workspace && permissions.submit && (
                    <button
                      className={buttonClass}
                      onClick={() => simpleAction("submit")}
                    >
                      Gửi phê duyệt
                    </button>
                  )}
                </div>
              </div>
            </div>
          )}

          {workspace && (permissions.approve || permissions.reject) && (
            <div className="grid gap-4 border border-white/10 p-5">
              <h3 className="font-serif text-2xl">Manager decision</h3>
              <textarea
                aria-label="Ghi chú phê duyệt"
                className={inputClass}
                disabled={pending}
                placeholder="Ghi chú phê duyệt"
                value={approvalNotes}
                onChange={(event) =>
                  setApprovalNotes(event.currentTarget.value)
                }
              />
              <button
                className={buttonClass}
                disabled={!permissions.approve}
                onClick={() => approvalAction("approve")}
              >
                Phê duyệt
              </button>
              <textarea
                aria-label="Lý do từ chối"
                className={inputClass}
                disabled={pending}
                placeholder="Lý do từ chối bắt buộc"
                value={rejectionReason}
                onChange={(event) =>
                  setRejectionReason(event.currentTarget.value)
                }
              />
              <textarea
                aria-label="Ghi chú từ chối"
                className={inputClass}
                disabled={pending}
                placeholder="Ghi chú từ chối"
                value={rejectionNotes}
                onChange={(event) =>
                  setRejectionNotes(event.currentTarget.value)
                }
              />
              <FieldError state={command} name="reason" />
              <FieldError state={command} name="reviewer" />
              <button
                className={ghostButtonClass}
                disabled={!permissions.reject}
                onClick={() => approvalAction("reject")}
              >
                Từ chối
              </button>
            </div>
          )}

          {workspace && permissions.send && (
            <div className="grid gap-4 border border-white/10 p-5">
              <h3 className="font-serif text-2xl">
                Ghi nhận đã gửi khách hàng
              </h3>
              <input
                aria-label="Người nhận quotation"
                className={inputClass}
                disabled={pending}
                placeholder="Người nhận"
                value={sentTo}
                onChange={(event) => setSentTo(event.currentTarget.value)}
              />
              <textarea
                aria-label="Bằng chứng gửi quotation"
                className={inputClass}
                disabled={pending}
                placeholder="Bằng chứng gửi"
                value={sendEvidence}
                onChange={(event) => setSendEvidence(event.currentTarget.value)}
              />
              <button className={buttonClass} onClick={send}>
                Ghi nhận SENT
              </button>
            </div>
          )}

          {workspace && (permissions.accept || permissions.decline) && (
            <div className="grid gap-4 border border-white/10 p-5">
              <h3 className="font-serif text-2xl">Quyết định khách hàng</h3>
              <input
                aria-label="Thông tin liên hệ khách hàng"
                className={inputClass}
                disabled={pending}
                placeholder="Contact snapshot"
                value={customerContact}
                onChange={(event) =>
                  setCustomerContact(event.currentTarget.value)
                }
              />
              <textarea
                aria-label="Bằng chứng quyết định khách hàng"
                className={inputClass}
                disabled={pending}
                placeholder="Decision evidence"
                value={customerEvidence}
                onChange={(event) =>
                  setCustomerEvidence(event.currentTarget.value)
                }
              />
              <div className="flex flex-wrap gap-3">
                <button
                  className={buttonClass}
                  disabled={!permissions.accept}
                  onClick={() => customerDecision("accept")}
                >
                  Khách hàng chấp nhận
                </button>
              </div>
              <textarea
                aria-label="Lý do khách hàng từ chối"
                className={inputClass}
                disabled={pending}
                placeholder="Lý do decline bắt buộc"
                value={declineReason}
                onChange={(event) =>
                  setDeclineReason(event.currentTarget.value)
                }
              />
              <FieldError state={command} name="reason" />
              <button
                className={ghostButtonClass}
                disabled={!permissions.decline}
                onClick={() => customerDecision("decline")}
              >
                Khách hàng từ chối
              </button>
            </div>
          )}

          {workspace && (
            <div className="grid gap-5 border border-white/10 p-5 lg:grid-cols-2">
              <div>
                <h3 className="font-serif text-xl">Approval evidence</h3>
                {workspace.approvals.length === 0 ? (
                  <p className="mt-3 text-sm text-zinc-500">
                    Chưa có quyết định.
                  </p>
                ) : (
                  workspace.approvals.map((decision) => (
                    <div
                      className="mt-3 border border-white/10 p-3 text-sm"
                      key={decision.id}
                    >
                      <b>{decision.decision}</b> · reviewer #
                      {decision.reviewer_id ?? "—"}
                      {decision.reason && (
                        <p className="mt-1 text-zinc-400">
                          {safeEvidence(decision.reason)}
                        </p>
                      )}
                      {decision.notes && (
                        <p className="mt-1 text-zinc-500">
                          {safeEvidence(decision.notes)}
                        </p>
                      )}
                    </div>
                  ))
                )}
              </div>
              <div>
                <h3 className="font-serif text-xl">
                  Customer decision evidence
                </h3>
                {workspace.customerDecisions.length === 0 ? (
                  <p className="mt-3 text-sm text-zinc-500">
                    Chưa có quyết định.
                  </p>
                ) : (
                  workspace.customerDecisions.map((decision) => (
                    <div
                      className="mt-3 border border-white/10 p-3 text-sm"
                      key={decision.id}
                    >
                      <b>{decision.decision}</b> · evidence{" "}
                      {decision.decision_evidence_recorded
                        ? "đã ghi"
                        : "chưa có"}
                      {decision.reason && (
                        <p className="mt-1 text-zinc-400">
                          {safeEvidence(decision.reason)}
                        </p>
                      )}
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
