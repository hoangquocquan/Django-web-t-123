import { useEffect, useMemo, useRef, useState } from "react"

import { CanonicalClientError } from "../api/canonical.ts"
import {
  canConvertQuotation,
  canViewGlobalAudit,
  classifyProgressReconciliation,
  createOrderCommandGate,
  createOrderConversionAttemptManager,
  createOrderRequestGuards,
  executeOrderConversionAttempt,
  fetchAcceptedQuotations,
  fetchGlobalAudit,
  fetchOrderIndex,
  fetchOrderWorkspace,
  isAmbiguousOrderError,
  orderCommandStateFromError,
  orderLifecyclePermissions,
  postOrderProgressCommand,
  settleOrderCommandOnDeactivate,
  validateOrderConversionPayload,
  validateOrderProgressPayload,
  wouldDuplicateInProgressEvent,
  type CanonicalAuditEvent,
  type CanonicalClient,
  type CanonicalOrder,
  type OrderCommandState,
  type OrderProgressAction,
  type OrderProgressPayload,
  type OrderReasonPayload,
  type OrderWorkspaceData,
} from "../api/orderCommands.ts"
import {
  fetchQuotationWorkspace,
  type CanonicalQuotationSummary,
} from "../api/quotationCommands.ts"
import type { CanonicalPage } from "../api/rfq.ts"

const inputClass =
  "w-full border border-white/10 bg-zinc-950 px-3 py-2 text-sm outline-none focus:border-orange-500 focus-visible:ring-2 focus-visible:ring-orange-400 disabled:cursor-not-allowed disabled:opacity-50"
const buttonClass =
  "bg-orange-600 px-4 py-2 text-xs font-semibold uppercase tracking-widest text-white hover:bg-orange-500 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-400 focus-visible:ring-offset-2 focus-visible:ring-offset-zinc-950 disabled:cursor-not-allowed disabled:opacity-50"
const ghostButtonClass =
  "border border-white/20 px-4 py-2 text-xs uppercase tracking-widest hover:border-orange-500 hover:text-orange-400 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-400 focus-visible:ring-offset-2 focus-visible:ring-offset-zinc-950 disabled:cursor-not-allowed disabled:opacity-50"

function safeText(value: string) {
  return value.trim().slice(0, 500)
}

function FieldError({
  state,
  name,
}: {
  state: OrderCommandState
  name: string
}) {
  const message = state.fieldErrors?.[name]
  return message ? (
    <p className="text-xs text-orange-400" role="alert">
      {message}
    </p>
  ) : null
}

export default function OrderWorkspace({
  client,
  authenticated,
  role,
  active,
  goToLogin,
  onAuthenticationFailure,
}: {
  client: CanonicalClient
  authenticated: boolean
  role: string | null
  active: boolean
  goToLogin: () => void
  onAuthenticationFailure: () => void
}) {
  const [orders, setOrders] = useState<CanonicalPage<CanonicalOrder> | null>(
    null,
  )
  const [acceptedQuotations, setAcceptedQuotations] =
    useState<CanonicalPage<CanonicalQuotationSummary> | null>(null)
  const [workspace, setWorkspace] = useState<OrderWorkspaceData | null>(null)
  const [globalAudit, setGlobalAudit] =
    useState<CanonicalPage<CanonicalAuditEvent> | null>(null)
  const [auditOffset, setAuditOffset] = useState(0)
  const [selectedQuotationId, setSelectedQuotationId] = useState("")
  const [progressPercent, setProgressPercent] = useState("0")
  const [milestoneNote, setMilestoneNote] = useState("")
  const [reason, setReason] = useState("")
  const [indexState, setIndexState] = useState<OrderCommandState>({
    status: "initial",
    message: "Chưa tải danh sách Order.",
  })
  const [auditState, setAuditState] = useState<OrderCommandState>({
    status: "initial",
    message: "Chưa tải global audit.",
  })
  const [conversionState, setConversionState] = useState<OrderCommandState>({
    status: "initial",
    message: "Chưa tải quotation ACCEPTED.",
  })
  const [command, setCommand] = useState<OrderCommandState>({
    status: "initial",
    message: "Chọn quotation ACCEPTED hoặc canonical Order.",
  })
  const gate = useMemo(() => createOrderCommandGate(), [])
  const conversionAttempt = useMemo(
    () => createOrderConversionAttemptManager(),
    [],
  )
  const guards = useMemo(() => createOrderRequestGuards(), [])
  const indexAbort = useRef<AbortController | null>(null)
  const conversionAbort = useRef<AbortController | null>(null)
  const workspaceAbort = useRef<AbortController | null>(null)
  const auditAbort = useRef<AbortController | null>(null)
  const progressPending = useRef(false)
  const pending = command.status === "pending"
  const ambiguous = command.status === "ambiguous"
  const activeConversion = conversionAttempt.hasActiveAttempt()
  const locked = pending || ambiguous || activeConversion
  const selectedQuotation =
    acceptedQuotations?.results.find(
      (quotation) => String(quotation.id) === selectedQuotationId,
    ) ?? null
  const permissions = orderLifecyclePermissions(
    role,
    workspace?.order.workflow_status ?? null,
    locked,
  )
  const conversionAllowed = canConvertQuotation(
    role,
    selectedQuotation?.workflow_status ?? null,
    pending || ambiguous,
  )
  const globalAuditAllowed = canViewGlobalAudit(role)

  const handleError = (error: unknown) => {
    const next = orderCommandStateFromError(error)
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
      message: "Đang tải canonical Orders...",
    })
    void fetchOrderIndex(client, controller.signal)
      .then((result) => {
        if (!guards.index.isLatest(requestId)) return
        setOrders(result)
        setIndexState({
          status: "ready",
          message:
            result.count === 0
              ? "Chưa có canonical Order."
              : `${result.count} canonical Orders`,
        })
      })
      .catch((error) => {
        if (!guards.index.isLatest(requestId)) return
        const next = orderCommandStateFromError(error)
        setIndexState(next)
        if (next.status === "authentication_failure") {
          onAuthenticationFailure()
        }
      })
  }

  const loadConversionSources = () => {
    if (!authenticated || !active) return
    if (role !== "Admin" && role !== "Sales") {
      setAcceptedQuotations(null)
      setConversionState({
        status: "permission_denied",
        message: "Role hiện tại không thực hiện quotation conversion.",
      })
      return
    }
    conversionAbort.current?.abort()
    const controller = new AbortController()
    conversionAbort.current = controller
    const requestId = guards.conversion.next()
    setConversionState({
      status: "loading",
      message: "Đang tải quotation ACCEPTED...",
    })
    void fetchAcceptedQuotations(client, controller.signal)
      .then((result) => {
        if (!guards.conversion.isLatest(requestId)) return
        setAcceptedQuotations(result)
        setConversionState({
          status: "ready",
          message:
            result.count === 0
              ? "Không có quotation ACCEPTED."
              : `${result.count} quotation ACCEPTED`,
        })
      })
      .catch((error) => {
        if (!guards.conversion.isLatest(requestId)) return
        const next = orderCommandStateFromError(error)
        setConversionState(next)
        if (next.status === "authentication_failure") {
          onAuthenticationFailure()
        }
      })
  }

  const loadAudit = (offset = auditOffset) => {
    if (!authenticated || !active) return
    if (!globalAuditAllowed) {
      setGlobalAudit(null)
      setAuditState({
        status: "permission_denied",
        message: "Global audit chỉ dành cho Admin hoặc Manager được cấp quyền.",
      })
      return
    }
    auditAbort.current?.abort()
    const controller = new AbortController()
    auditAbort.current = controller
    const requestId = guards.audit.next()
    setAuditState({ status: "loading", message: "Đang tải global audit..." })
    void fetchGlobalAudit(client, offset, controller.signal)
      .then((result) => {
        if (!guards.audit.isLatest(requestId)) return
        setAuditOffset(offset)
        setGlobalAudit(result)
        setAuditState({
          status: "ready",
          message:
            result.count === 0
              ? "Global audit trống."
              : `Hiển thị ${result.results.length}/${result.count} audit events`,
        })
      })
      .catch((error) => {
        if (!guards.audit.isLatest(requestId)) return
        const next = orderCommandStateFromError(error)
        setAuditState(next)
        if (next.status === "authentication_failure") {
          onAuthenticationFailure()
        }
      })
  }

  useEffect(() => {
    if (!authenticated) {
      indexAbort.current?.abort()
      conversionAbort.current?.abort()
      workspaceAbort.current?.abort()
      auditAbort.current?.abort()
      guards.index.next()
      guards.conversion.next()
      guards.workspace.next()
      guards.audit.next()
      gate.finish()
      conversionAttempt.reset()
      progressPending.current = false
      setOrders(null)
      setAcceptedQuotations(null)
      setWorkspace(null)
      setGlobalAudit(null)
      setAuditOffset(0)
      setSelectedQuotationId("")
      setProgressPercent("0")
      setMilestoneNote("")
      setReason("")
      setIndexState({ status: "initial", message: "Chưa tải danh sách Order." })
      setAuditState({ status: "initial", message: "Chưa tải global audit." })
      setConversionState({
        status: "initial",
        message: "Chưa tải quotation ACCEPTED.",
      })
      setCommand({
        status: "initial",
        message: "Chọn quotation ACCEPTED hoặc canonical Order.",
      })
      return
    }
    if (!active) {
      indexAbort.current?.abort()
      conversionAbort.current?.abort()
      workspaceAbort.current?.abort()
      auditAbort.current?.abort()
      guards.index.next()
      guards.conversion.next()
      guards.workspace.next()
      guards.audit.next()
      setCommand((state) =>
        settleOrderCommandOnDeactivate(state, progressPending.current),
      )
      return
    }
    loadIndex()
    loadConversionSources()
    loadAudit(0)
  }, [active, authenticated, client, role])

  useEffect(
    () => () => {
      indexAbort.current?.abort()
      conversionAbort.current?.abort()
      workspaceAbort.current?.abort()
      auditAbort.current?.abort()
      guards.index.next()
      guards.conversion.next()
      guards.workspace.next()
      guards.audit.next()
    },
    [],
  )

  const applyWorkspace = (data: OrderWorkspaceData) => {
    setWorkspace(data)
    setProgressPercent(String(data.order.progress_percent))
    setMilestoneNote("")
    setReason("")
  }

  const selectOrder = (orderId: number) => {
    if (pending || activeConversion) return
    workspaceAbort.current?.abort()
    const controller = new AbortController()
    workspaceAbort.current = controller
    const requestId = guards.workspace.next()
    setCommand({ status: "pending", message: "Đang tải canonical Order..." })
    void fetchOrderWorkspace(client, orderId, controller.signal)
      .then((data) => {
        if (!guards.workspace.isLatest(requestId)) return
        applyWorkspace(data)
        setCommand({ status: "ready", message: "Đã đồng bộ canonical Order." })
      })
      .catch((error) => {
        if (guards.workspace.isLatest(requestId)) handleError(error)
      })
  }

  const finishAccepted = (data: OrderWorkspaceData, message: string) => {
    applyWorkspace(data)
    setCommand({ status: "accepted", message })
    setSelectedQuotationId("")
    loadIndex()
    loadConversionSources()
    loadAudit(0)
  }

  const convert = () => {
    let target = conversionAttempt.activeTarget()
    let payload = conversionAttempt.activePayload()
    if (target === null || payload === null) {
      if (
        selectedQuotation === null ||
        selectedQuotation.quotation_family_number === null
      ) {
        setCommand({
          status: "validation",
          message: "Phải chọn quotation ACCEPTED canonical hợp lệ.",
        })
        return
      }
      target = {
        quotationId: selectedQuotation.id,
        familyNumber: selectedQuotation.quotation_family_number,
      }
      try {
        payload = validateOrderConversionPayload({})
      } catch (error) {
        handleError(error)
        return
      }
    }
    if (!gate.tryStart()) return
    workspaceAbort.current?.abort()
    const controller = new AbortController()
    workspaceAbort.current = controller
    const requestId = guards.workspace.next()
    setCommand({ status: "pending", message: "Đang convert quotation..." })
    void executeOrderConversionAttempt(
      client,
      conversionAttempt,
      target,
      payload,
      async (orderId, retainedTarget, signal) => {
        const [orderData] = await Promise.all([
          fetchOrderWorkspace(client, orderId, signal),
          fetchQuotationWorkspace(
            client,
            retainedTarget.quotationId,
            retainedTarget.familyNumber,
            signal,
          ),
        ])
        return orderData
      },
      controller.signal,
    )
      .then((data) => {
        if (!guards.workspace.isLatest(requestId)) return
        finishAccepted(data, "Conversion đã được xác nhận và đồng bộ.")
      })
      .catch((error) => {
        if (!guards.workspace.isLatest(requestId)) return
        if (
          conversionAttempt.hasActiveAttempt() &&
          isAmbiguousOrderError(error)
        ) {
          setCommand({
            status: "ambiguous",
            message:
              "Kết quả conversion chưa xác định; thử lại giữ nguyên logical attempt.",
          })
          return
        }
        handleError(error)
      })
      .finally(() => gate.finish())
  }

  const reconcileAmbiguousProgress = async (
    before: OrderWorkspaceData,
    action: OrderProgressAction,
    payload: OrderProgressPayload | OrderReasonPayload,
  ) => {
    const controller = new AbortController()
    workspaceAbort.current = controller
    const requestId = guards.workspace.next()
    try {
      const after = await fetchOrderWorkspace(
        client,
        before.order.id,
        controller.signal,
      )
      if (!guards.workspace.isLatest(requestId)) return
      const outcome = classifyProgressReconciliation(
        before,
        after,
        action,
        payload,
      )
      applyWorkspace(after)
      if (outcome === "applied") {
        finishAccepted(after, "Progress command đã được chứng minh là applied.")
      } else if (outcome === "not_applied") {
        setCommand({
          status: "not_applied",
          message:
            "Reconciliation chứng minh command chưa được áp dụng; có thể gửi lệnh mới.",
        })
      } else {
        setCommand({
          status: "ambiguous",
          message:
            "Không thể chứng minh kết quả command; hãy refresh authoritative trước lệnh khác.",
        })
      }
    } catch {
      if (!guards.workspace.isLatest(requestId)) return
      setCommand({
        status: "ambiguous",
        message:
          "Không thể reconcile kết quả command; hãy refresh authoritative trước lệnh khác.",
      })
    }
  }

  const progressCommand = (action: OrderProgressAction) => {
    if (!workspace || !permissions[action]) return
    let payload: OrderProgressPayload | OrderReasonPayload
    try {
      payload = validateOrderProgressPayload(
        {
          progress_percent:
            action === "complete" ? 100 : Number(progressPercent),
          milestone_note: milestoneNote,
          ...(action === "hold" || action === "cancel" ? { reason } : {}),
        },
        action,
      )
      if (wouldDuplicateInProgressEvent(workspace.order, action, payload)) {
        throw new CanonicalClientError({
          kind: "validation",
          code: "client_validation_error",
          message: "Duplicate progress event.",
          details: { progress_percent: "duplicate" },
        })
      }
    } catch (error) {
      handleError(error)
      return
    }
    if (!gate.tryStart()) return
    const before = workspace
    workspaceAbort.current?.abort()
    const controller = new AbortController()
    workspaceAbort.current = controller
    const requestId = guards.workspace.next()
    progressPending.current = true
    setCommand({ status: "pending", message: "Đang gửi progress command..." })
    void postOrderProgressCommand(
      client,
      before.order.id,
      action,
      payload,
      controller.signal,
    )
      .then((order) => fetchOrderWorkspace(client, order.id, controller.signal))
      .then((data) => {
        if (!guards.workspace.isLatest(requestId)) return
        finishAccepted(data, "Progress command đã được chấp nhận và đồng bộ.")
      })
      .catch((error) => {
        if (!guards.workspace.isLatest(requestId)) return
        if (isAmbiguousOrderError(error)) {
          setCommand({
            status: "ambiguous",
            message:
              "Kết quả progress command chưa xác định; đang reconcile authoritative.",
          })
          void reconcileAmbiguousProgress(before, action, payload)
          return
        }
        handleError(error)
      })
      .finally(() => {
        progressPending.current = false
        gate.finish()
      })
  }

  if (!authenticated) {
    return (
      <div className="grid min-h-64 place-items-center border border-white/10 p-8 text-center">
        <div>
          <p>Đăng nhập để quản lý canonical Orders.</p>
          <button className={`${buttonClass} mt-5`} onClick={goToLogin}>
            Đăng nhập
          </button>
        </div>
      </div>
    )
  }

  const showControls = Object.values(permissions).some(Boolean)

  return (
    <div className="grid gap-6">
      <div className="flex flex-wrap items-center justify-between gap-3 border border-white/10 bg-zinc-900/30 p-4">
        <div>
          <div className="text-xs uppercase tracking-widest text-orange-500">
            Canonical Order · progress · audit · {role ?? "unknown role"}
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
        <div className="flex flex-wrap gap-2">
          <button
            className={ghostButtonClass}
            disabled={pending}
            onClick={loadIndex}
          >
            Tải lại Orders
          </button>
          {workspace && (
            <button
              className={ghostButtonClass}
              disabled={pending || activeConversion}
              onClick={() => selectOrder(workspace.order.id)}
            >
              Refresh authoritative
            </button>
          )}
        </div>
      </div>

      <div className="grid gap-6 xl:grid-cols-3">
        <div className="border border-white/10 p-5">
          <h3 className="font-serif text-2xl">Convert ACCEPTED quotation</h3>
          <select
            aria-label="Quotation đã chấp nhận để chuyển đổi"
            className={`${inputClass} mt-4`}
            data-testid="order-conversion-selector"
            disabled={pending || activeConversion}
            value={selectedQuotationId}
            onChange={(event) =>
              setSelectedQuotationId(event.currentTarget.value)
            }
          >
            <option value="">Chọn quotation ACCEPTED</option>
            {acceptedQuotations?.results.map((quotation) => (
              <option key={quotation.id} value={quotation.id}>
                {quotation.quotation_number} · {quotation.total}{" "}
                {quotation.currency}
              </option>
            ))}
          </select>
          {(conversionAllowed || activeConversion) && (
            <button
              className={`${buttonClass} mt-3`}
              disabled={pending}
              onClick={convert}
            >
              {activeConversion ? "Thử lại conversion" : "Convert to Order"}
            </button>
          )}
          <p className="mt-3 text-xs text-zinc-500">
            Payload conversion là rỗng; ownership và exact permissions do
            backend quyết định.
          </p>
          <p className="mt-2 text-xs text-zinc-500">
            {conversionState.message}
          </p>
        </div>

        <div className="border border-white/10 p-5">
          <h3 className="font-serif text-2xl">Canonical Orders</h3>
          <p className="mt-2 text-sm text-zinc-500">{indexState.message}</p>
          <div className="mt-4 grid gap-2">
            {orders?.results.map((order) => (
              <button
                className={ghostButtonClass}
                data-order-id={order.id}
                disabled={pending || activeConversion}
                key={order.id}
                onClick={() => selectOrder(order.id)}
              >
                {order.order_number} · {order.workflow_status} ·{" "}
                {order.progress_percent}%
              </button>
            ))}
          </div>
        </div>

        <div className="border border-white/10 p-5">
          <div className="flex items-center justify-between gap-2">
            <h3 className="font-serif text-2xl">Global audit</h3>
            {globalAuditAllowed && (
              <button
                className={ghostButtonClass}
                disabled={auditState.status === "loading"}
                onClick={() => loadAudit(auditOffset)}
              >
                Refresh
              </button>
            )}
          </div>
          <p className="mt-2 text-sm text-zinc-500">{auditState.message}</p>
          {globalAuditAllowed && globalAudit && (
            <>
              <div className="mt-4 grid gap-2">
                {globalAudit.results.map((event) => (
                  <div
                    className="border border-white/10 p-3 text-xs"
                    key={event.id}
                  >
                    <b>{safeText(event.action)}</b> ·{" "}
                    {safeText(event.entity_type)} #{safeText(event.entity_id)}
                    <p className="mt-1 text-zinc-500">
                      {safeText(event.actor_display)} ·{" "}
                      {event.created_at ?? "—"}
                    </p>
                  </div>
                ))}
              </div>
              <div className="mt-3 flex gap-2">
                <button
                  className={ghostButtonClass}
                  disabled={globalAudit.previous_offset === null}
                  onClick={() => loadAudit(globalAudit.previous_offset ?? 0)}
                >
                  Trước
                </button>
                <button
                  className={ghostButtonClass}
                  disabled={globalAudit.next_offset === null}
                  onClick={() =>
                    loadAudit(globalAudit.next_offset ?? auditOffset)
                  }
                >
                  Sau
                </button>
              </div>
            </>
          )}
        </div>
      </div>

      {workspace && (
        <>
          <div
            className="border border-white/10 bg-[#0b0d0f] p-5"
            data-order-number={workspace.order.order_number}
            data-order-progress={workspace.order.progress_percent}
            data-order-status={workspace.order.workflow_status}
            data-testid="order-workspace-detail"
          >
            <div className="flex flex-wrap justify-between gap-4">
              <div>
                <div className="text-xs uppercase tracking-widest text-orange-500">
                  {workspace.order.workflow_status}
                </div>
                <h3 className="mt-2 font-serif text-3xl">
                  {workspace.order.order_number}
                </h3>
                <p className="mt-2 text-sm text-zinc-500">
                  Source quotation #{workspace.order.source_quotation_id ?? "—"}
                </p>
              </div>
              <div className="text-right">
                <div className="text-3xl font-semibold">
                  {workspace.order.progress_percent}%
                </div>
                <div className="mt-2 text-orange-400">
                  {workspace.order.total_amount} {workspace.order.currency}
                </div>
              </div>
            </div>
            <div className="mt-4 grid gap-2 text-sm text-zinc-400 sm:grid-cols-3">
              <span>
                Expected: {workspace.order.expected_delivery_date ?? "—"}
              </span>
              <span>Hold: {safeText(workspace.order.hold_reason) || "—"}</span>
              <span>
                Cancel: {safeText(workspace.order.cancel_reason) || "—"}
              </span>
            </div>
          </div>

          {showControls && (
            <div className="grid gap-4 border border-white/10 p-5">
              <h3 className="font-serif text-2xl">Order progress commands</h3>
              <div className="grid gap-3 sm:grid-cols-2">
                <input
                  aria-label="Phần trăm tiến độ"
                  className={inputClass}
                  data-testid="order-progress-input"
                  disabled={locked}
                  inputMode="numeric"
                  placeholder="Progress 0–100"
                  value={progressPercent}
                  onChange={(event) =>
                    setProgressPercent(event.currentTarget.value)
                  }
                />
                <input
                  aria-label="Ghi chú mốc tiến độ"
                  className={inputClass}
                  data-testid="order-milestone-input"
                  disabled={locked}
                  maxLength={240}
                  placeholder="Milestone note"
                  value={milestoneNote}
                  onChange={(event) =>
                    setMilestoneNote(event.currentTarget.value)
                  }
                />
              </div>
              <textarea
                aria-label="Lý do hold hoặc cancel"
                className={inputClass}
                data-testid="order-reason-input"
                disabled={locked}
                placeholder="Reason bắt buộc cho hold/cancel"
                value={reason}
                onChange={(event) => setReason(event.currentTarget.value)}
              />
              <FieldError state={command} name="progress_percent" />
              <FieldError state={command} name="reason" />
              <FieldError state={command} name="expected_delivery_date" />
              <div className="flex flex-wrap gap-2">
                {permissions.progress && (
                  <button
                    className={buttonClass}
                    onClick={() => progressCommand("progress")}
                  >
                    Update progress
                  </button>
                )}
                {permissions.hold && (
                  <button
                    className={ghostButtonClass}
                    onClick={() => progressCommand("hold")}
                  >
                    Hold
                  </button>
                )}
                {permissions.resume && (
                  <button
                    className={buttonClass}
                    onClick={() => progressCommand("resume")}
                  >
                    Resume
                  </button>
                )}
                {permissions.complete && (
                  <button
                    className={buttonClass}
                    onClick={() => progressCommand("complete")}
                  >
                    Complete 100%
                  </button>
                )}
                {permissions.cancel && (
                  <button
                    className={ghostButtonClass}
                    onClick={() => progressCommand("cancel")}
                  >
                    Cancel
                  </button>
                )}
              </div>
              <p className="text-xs text-zinc-500">
                Progress commands không tự retry sau ambiguous outcome.
              </p>
            </div>
          )}

          <div className="grid gap-5 xl:grid-cols-3">
            <div className="border border-white/10 p-5">
              <h3 className="font-serif text-2xl">Immutable lines</h3>
              {workspace.lines.length === 0 ? (
                <p className="mt-3 text-sm text-zinc-500">
                  Không có dòng Order.
                </p>
              ) : (
                workspace.lines.map((line) => (
                  <div
                    className="mt-3 border border-white/10 p-3 text-sm"
                    key={line.id}
                  >
                    <b>
                      #{line.line_number} ·{" "}
                      {safeText(line.description_snapshot)}
                    </b>
                    <p className="mt-1 text-zinc-500">
                      {line.quantity} {line.unit} × {line.unit_price} ={" "}
                      {line.line_total}
                    </p>
                  </div>
                ))
              )}
            </div>

            <div className="border border-white/10 p-5">
              <h3 className="font-serif text-2xl">Progress history</h3>
              {workspace.progress.map((event) => (
                <div
                  className="mt-3 border border-white/10 p-3 text-sm"
                  key={event.id}
                >
                  <b>
                    {event.from_status ?? "CREATED"} → {event.to_status}
                  </b>
                  <p className="mt-1 text-zinc-500">
                    {event.progress_percent}% ·{" "}
                    {safeText(event.milestone_note) || "—"}
                  </p>
                  {event.reason && (
                    <p className="mt-1 text-orange-400">
                      {safeText(event.reason)}
                    </p>
                  )}
                </div>
              ))}
            </div>

            <div className="border border-white/10 p-5">
              <h3 className="font-serif text-2xl">Order audit timeline</h3>
              {workspace.timeline.map((event) => (
                <div
                  className="mt-3 border border-white/10 p-3 text-sm"
                  key={event.id}
                >
                  <b>{safeText(event.action)}</b>
                  <p className="mt-1 text-zinc-500">
                    {event.old_status ?? "—"} → {event.new_status ?? "—"} ·{" "}
                    {event.created_at ?? "—"}
                  </p>
                  {event.reason && (
                    <p className="mt-1 text-orange-400">
                      {safeText(event.reason)}
                    </p>
                  )}
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  )
}
