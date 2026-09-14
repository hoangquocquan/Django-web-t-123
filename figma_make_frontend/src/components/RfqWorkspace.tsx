import { useEffect, useMemo, useRef, useState, type ReactNode } from "react"

import { CanonicalClientError } from "../api/canonical.ts"
import {
  addRfqLine,
  commandState,
  commandStateFromError,
  createCommandGate,
  createRfqCreateAttemptManager,
  createRfqRequestGuards,
  executeRfqCreateAttempt,
  fetchRfqDetail,
  fetchRfqLines,
  loadRfqSelectors,
  removeRfqLine,
  rfqLifecyclePermissions,
  submitRfq,
  updateRfqDraft,
  updateRfqLine,
  validateRfqCreatePayload,
  validateRfqLineCreatePayload,
  validateRfqLineUpdatePayload,
  validateRfqUpdatePayload,
  type CanonicalRfqLine,
  type RfqCommandViewState,
  type RfqSelectors,
} from "../api/rfqCommands.ts"
import {
  rfqRows,
  rfqStatusText,
  type CanonicalRfq,
  type RfqClient,
  type RfqViewState,
} from "../api/rfq.ts"

type HeaderForm = {
  customerId: string
  projectName: string
  notes: string
  quoteDueAt: string
  requiredDeliveryDate: string
}

type LineForm = {
  partId: string
  materialId: string
  description: string
  quantity: string
  unit: "PCS" | "KG" | "M" | "MM"
  requiredDeliveryDate: string
  tolerance: string
  technicalNotes: string
}

const emptyHeader: HeaderForm = {
  customerId: "",
  projectName: "",
  notes: "",
  quoteDueAt: "",
  requiredDeliveryDate: "",
}

const emptyLine: LineForm = {
  partId: "",
  materialId: "",
  description: "",
  quantity: "1.0000",
  unit: "PCS",
  requiredDeliveryDate: "",
  tolerance: "",
  technicalNotes: "",
}

const inputClass =
  "w-full border border-white/10 bg-zinc-950 px-3 py-2 text-sm outline-none focus:border-orange-500 disabled:cursor-not-allowed disabled:opacity-50"
const buttonClass =
  "bg-orange-600 px-4 py-2 text-xs font-semibold uppercase tracking-widest text-white hover:bg-orange-500 disabled:cursor-not-allowed disabled:opacity-50"
const ghostButtonClass =
  "border border-white/20 px-4 py-2 text-xs uppercase tracking-widest hover:border-orange-500 hover:text-orange-400 disabled:cursor-not-allowed disabled:opacity-50"

function today(): string {
  return new Date().toISOString().slice(0, 10)
}

function headerFromRfq(rfq: CanonicalRfq): HeaderForm {
  return {
    customerId: String(rfq.customer_id),
    projectName: rfq.project_name,
    notes: rfq.notes,
    quoteDueAt: rfq.quote_due_at ?? "",
    requiredDeliveryDate: rfq.required_delivery_date ?? "",
  }
}

function lineFromRfq(line: CanonicalRfqLine): LineForm {
  return {
    partId: line.part_id === null ? "" : String(line.part_id),
    materialId: line.material_id === null ? "" : String(line.material_id),
    description: line.description,
    quantity: line.quantity,
    unit: ["PCS", "KG", "M", "MM"].includes(line.unit)
      ? line.unit as LineForm["unit"]
      : "PCS",
    requiredDeliveryDate: line.required_delivery_date,
    tolerance: line.tolerance,
    technicalNotes: line.technical_notes,
  }
}

function FieldError({
  state,
  name,
}: {
  state: RfqCommandViewState
  name: string
}) {
  const message = state.fieldErrors?.[name]
  return message ? (
    <span className="text-xs text-orange-400">{message}</span>
  ) : null
}

type LabeledProps = {
  label: string
  children: ReactNode
}

function Labeled({ label, children }: LabeledProps) {
  return (
    <label className="grid gap-2">
      <span className="text-[10px] uppercase tracking-[.18em] text-zinc-500">
        {label}
      </span>
      {children}
    </label>
  )
}

export default function RfqWorkspace({
  client,
  authenticated,
  rfqState,
  reloadRfqs,
  goToLogin,
  onAuthenticationFailure,
}: {
  client: RfqClient
  authenticated: boolean
  rfqState: RfqViewState
  reloadRfqs: () => void
  goToLogin: () => void
  onAuthenticationFailure: () => void
}) {
  const [selectors, setSelectors] = useState<RfqSelectors>({
    customers: [],
    parts: [],
    materials: [],
  })
  const [selectorState, setSelectorState] = useState<RfqCommandViewState>(
    commandState("initial"),
  )
  const [command, setCommand] = useState<RfqCommandViewState>(
    commandState("initial"),
  )
  const [header, setHeader] = useState<HeaderForm>(emptyHeader)
  const [lineForm, setLineForm] = useState<LineForm>(emptyLine)
  const [selectedRfq, setSelectedRfq] = useState<CanonicalRfq | null>(null)
  const [lines, setLines] = useState<CanonicalRfqLine[]>([])
  const [editingLineId, setEditingLineId] = useState<number | null>(null)
  const gate = useMemo(() => createCommandGate(), [])
  const createAttempt = useMemo(() => createRfqCreateAttemptManager(), [])
  const requestGuards = useMemo(() => createRfqRequestGuards(), [])
  const { selectors: selectorGuard, workspace: workspaceGuard } = requestGuards
  const activeAbort = useRef<AbortController | null>(null)
  const pending = command.status === "submitting"
  const needsReconciliation = ["timeout", "network"].includes(command.status)
  const activeCreateAttempt = createAttempt.hasActiveAttempt()
  const lifecycle = rfqLifecyclePermissions(
    selectedRfq?.status ?? null,
    pending || needsReconciliation,
  )
  const editable = lifecycle.header && lifecycle.lines
  const headerEditable =
    selectedRfq === null ? !pending && !activeCreateAttempt : editable

  const handleFailure = (error: unknown) => {
    const next = commandStateFromError(error)
    setCommand(next)
    if (next.status === "authentication_failure") onAuthenticationFailure()
  }

  const reconcile = async (rfqId: number, signal: AbortSignal) => {
    const [rfq, nextLines] = await Promise.all([
      fetchRfqDetail(client, rfqId, signal),
      fetchRfqLines(client, rfqId, signal),
    ])
    return { rfq, lines: nextLines }
  }

  const applyReconciledRfq = (
    rfq: CanonicalRfq,
    nextLines: CanonicalRfqLine[],
  ) => {
    setSelectedRfq(rfq)
    setHeader(headerFromRfq(rfq))
    setLines(nextLines)
    setEditingLineId(null)
    setLineForm({
      ...emptyLine,
      requiredDeliveryDate: rfq.required_delivery_date ?? "",
    })
    reloadRfqs()
  }

  const runCommand = async (
    action: (
      signal: AbortSignal,
    ) => Promise<{
      rfq: CanonicalRfq
      lines: CanonicalRfqLine[]
    }>,
  ) => {
    if (!gate.tryStart()) return
    activeAbort.current?.abort()
    const controller = new AbortController()
    activeAbort.current = controller
    const requestId = workspaceGuard.next()
    setCommand(commandState("submitting"))
    try {
      const result = await action(controller.signal)
      if (!workspaceGuard.isLatest(requestId)) return
      applyReconciledRfq(result.rfq, result.lines)
      setCommand(commandState("accepted"))
    } catch (error) {
      if (!workspaceGuard.isLatest(requestId)) return
      handleFailure(error)
    } finally {
      gate.finish()
    }
  }

  useEffect(() => {
    if (!authenticated) {
      setSelectorState(commandState("initial"))
      return
    }
    const controller = new AbortController()
    const requestId = selectorGuard.next()
    setSelectorState(commandState("loading_selectors"))
    void loadRfqSelectors(client, controller.signal)
      .then((result) => {
        if (!selectorGuard.isLatest(requestId)) return
        setSelectors(result)
        setSelectorState(commandState("ready"))
      })
      .catch((error) => {
        if (!selectorGuard.isLatest(requestId)) return
        const next = commandStateFromError(error)
        setSelectorState(next)
        if (next.status === "authentication_failure") onAuthenticationFailure()
      })
    return () => {
      controller.abort()
      selectorGuard.next()
    }
  }, [authenticated, client])

  useEffect(
    () => () => {
      activeAbort.current?.abort()
      workspaceGuard.next()
      selectorGuard.next()
    },
    [],
  )

  const startNew = () => {
    if (pending || activeCreateAttempt) return
    setSelectedRfq(null)
    setLines([])
    setHeader(emptyHeader)
    setLineForm(emptyLine)
    setEditingLineId(null)
    setCommand(commandState("initial"))
  }

  const openRfq = (rfq: CanonicalRfq) => {
    if (pending || activeCreateAttempt) return
    activeAbort.current?.abort()
    const controller = new AbortController()
    activeAbort.current = controller
    const requestId = workspaceGuard.next()
    setCommand(commandState("submitting"))
    void Promise.all([
      fetchRfqDetail(client, rfq.id, controller.signal),
      fetchRfqLines(client, rfq.id, controller.signal),
    ])
      .then(([detail, detailLines]) => {
        if (!workspaceGuard.isLatest(requestId)) return
        setSelectedRfq(detail)
        setHeader(headerFromRfq(detail))
        setLines(detailLines)
        setLineForm({
          ...emptyLine,
          requiredDeliveryDate: detail.required_delivery_date ?? "",
        })
        setCommand(commandState("ready"))
      })
      .catch((error) => {
        if (workspaceGuard.isLatest(requestId)) handleFailure(error)
      })
  }

  const createDraft = () => {
    let payload = createAttempt.activePayload()
    if (payload === null) {
      try {
        payload = validateRfqCreatePayload(
          {
            customer_id: Number(header.customerId),
            project_name: header.projectName,
            notes: header.notes,
            quote_due_at: header.quoteDueAt,
            required_delivery_date: header.requiredDeliveryDate,
          },
          today(),
        )
      } catch (error) {
        handleFailure(error)
        return
      }
    }
    void runCommand((signal) =>
      executeRfqCreateAttempt(
        client,
        createAttempt,
        payload,
        (rfqId, reconcileSignal) => reconcile(rfqId, reconcileSignal!),
        signal,
      ),
    )
  }

  const updateHeader = () => {
    if (!selectedRfq || !editable) return
    try {
      const payload = validateRfqUpdatePayload(
        {
          project_name: header.projectName,
          notes: header.notes,
          quote_due_at: header.quoteDueAt,
          required_delivery_date: header.requiredDeliveryDate,
        },
        {
          quote_due_at: selectedRfq.quote_due_at,
          required_delivery_date: selectedRfq.required_delivery_date,
        },
        today(),
      )
      void runCommand(async (signal) => {
        const rfq = await updateRfqDraft(
          client,
          selectedRfq.id,
          payload,
          signal,
        )
        return reconcile(rfq.id, signal)
      })
    } catch (error) {
      handleFailure(error)
    }
  }

  const saveLine = () => {
    if (!selectedRfq || !editable) return
    const raw = {
      part_id: lineForm.partId ? Number(lineForm.partId) : null,
      material_id: lineForm.materialId ? Number(lineForm.materialId) : null,
      description: lineForm.description,
      quantity: lineForm.quantity,
      unit: lineForm.unit,
      required_delivery_date: lineForm.requiredDeliveryDate,
      tolerance: lineForm.tolerance,
      technical_notes: lineForm.technicalNotes,
      drawing_required: false,
    }
    try {
      if (editingLineId === null) {
        const payload = validateRfqLineCreatePayload(raw)
        void runCommand(async (signal) => {
          await addRfqLine(client, selectedRfq.id, payload, signal)
          return reconcile(selectedRfq.id, signal)
        })
      } else {
        const payload = validateRfqLineUpdatePayload(raw)
        void runCommand(async (signal) => {
          await updateRfqLine(
            client,
            selectedRfq.id,
            editingLineId,
            payload,
            signal,
          )
          return reconcile(selectedRfq.id, signal)
        })
      }
    } catch (error) {
      handleFailure(error)
    }
  }

  const removeLine = (lineId: number) => {
    if (!selectedRfq || !editable) return
    void runCommand(async (signal) => {
      await removeRfqLine(client, selectedRfq.id, lineId, signal)
      return reconcile(selectedRfq.id, signal)
    })
  }

  const submitDraft = () => {
    if (!selectedRfq || !editable) return
    try {
      if (selectedRfq.status !== "DRAFT") {
        throw new CanonicalClientError({
          kind: "conflict",
          code: "invalid_state",
          message: "RFQ is not editable.",
        })
      }
      if (lines.length === 0) {
        throw new CanonicalClientError({
          kind: "validation",
          code: "client_validation_error",
          message: "RFQ requires a line.",
          details: { lines: true },
        })
      }
      if (!selectedRfq.quote_due_at || selectedRfq.quote_due_at <= today()) {
        throw new CanonicalClientError({
          kind: "validation",
          code: "client_validation_error",
          message: "RFQ due date is invalid.",
          details: { quote_due_at: true },
        })
      }
      for (const line of lines) {
        validateRfqLineCreatePayload({
          part_id: line.part_id,
          material_id: line.material_id,
          description: line.description,
          quantity: line.quantity,
          unit: line.unit,
          required_delivery_date: line.required_delivery_date,
          tolerance: line.tolerance,
          technical_notes: line.technical_notes,
          drawing_required: line.drawing_required,
        })
      }
      void runCommand(async (signal) => {
        const rfq = await submitRfq(client, selectedRfq.id, signal)
        return reconcile(rfq.id, signal)
      })
    } catch (error) {
      handleFailure(error)
    }
  }

  if (!authenticated) {
    return (
      <div className="grid min-h-[260px] place-items-center border border-white/10 bg-zinc-900/30 p-10 text-center">
        <div>
          <h3 className="font-serif text-3xl">RFQ canonical</h3>
          <p className="mt-3 text-zinc-500">Đăng nhập để quản lý RFQ.</p>
          <button className={`${buttonClass} mt-6`} onClick={goToLogin}>
            Đăng nhập
          </button>
        </div>
      </div>
    )
  }

  const selectorsReady = selectorState.status === "ready"

  return (
    <div className="grid gap-6">
      <div className="flex flex-wrap items-center justify-between gap-3 border border-white/10 bg-zinc-900/30 p-4">
        <div>
          <div className="text-xs uppercase tracking-widest text-orange-500">
            Canonical RFQ workflow
          </div>
          <p className="mt-1 text-sm text-zinc-400">
            {selectorState.status === "loading_selectors"
              ? selectorState.message
              : command.message}
          </p>
        </div>
        <button
          className={buttonClass}
          disabled={pending || activeCreateAttempt}
          onClick={startNew}
        >
          + RFQ nháp
        </button>
      </div>

      {needsReconciliation && selectedRfq && (
        <button
          className={ghostButtonClass}
          disabled={pending}
          onClick={() => openRfq(selectedRfq)}
        >
          Tải lại trạng thái RFQ trước khi thử lại
        </button>
      )}

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1.15fr)_minmax(360px,.85fr)]">
        <div className="grid gap-5">
          <div className="overflow-auto border border-white/10">
            {rfqState.status === "populated" ? (
              <table className="w-full min-w-[720px] text-left text-sm">
                <thead className="bg-zinc-900 text-[10px] uppercase tracking-widest text-zinc-500">
                  <tr>
                    {[
                      "RFQ",
                      "Khách hàng",
                      "Hạn báo giá",
                      "Dự án",
                      "Trạng thái",
                    ].map((heading) => (
                      <th className="px-4 py-3" key={heading}>
                        {heading}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {rfqState.page.results.map((rfq, index) => (
                    <tr
                      className="cursor-pointer border-t border-white/10 hover:bg-white/[.03]"
                      key={rfq.id}
                      onClick={() => openRfq(rfq)}
                    >
                      {rfqRows(rfqState.page)[index]!.map((cell) => (
                        <td className="px-4 py-3" key={cell}>
                          {cell}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <div className="grid min-h-[220px] place-items-center p-8 text-center text-zinc-500">
                <div>
                  <p>{rfqStatusText(rfqState)}</p>
                  <button
                    className={`${ghostButtonClass} mt-4`}
                    disabled={pending}
                    onClick={reloadRfqs}
                  >
                    Tải lại danh sách
                  </button>
                </div>
              </div>
            )}
          </div>

          {selectedRfq && (
            <div className="border border-white/10 p-5">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <div className="text-xs text-zinc-500">
                    {selectedRfq.rfq_number}
                  </div>
                  <h3 className="mt-1 font-serif text-2xl">Dòng RFQ</h3>
                </div>
                <span className="border border-orange-500/30 px-3 py-1 text-xs text-orange-400">
                  {selectedRfq.status}
                </span>
              </div>
              {lines.length === 0 ? (
                <p className="mt-5 border border-dashed border-white/20 p-6 text-center text-sm text-zinc-500">
                  RFQ chưa có dòng chi tiết.
                </p>
              ) : (
                <div className="mt-5 grid gap-3">
                  {lines.map((line) => (
                    <div className="border border-white/10 p-4" key={line.id}>
                      <div className="flex flex-wrap justify-between gap-3">
                        <div>
                          <b>
                            #{line.line_number} · {line.description}
                          </b>
                          <p className="mt-1 text-xs text-zinc-500">
                            {line.quantity} {line.unit} · giao{" "}
                            {line.required_delivery_date}
                          </p>
                        </div>
                        <div className="flex gap-2">
                          <button
                            className={ghostButtonClass}
                            disabled={!editable}
                            onClick={() => {
                              setEditingLineId(line.id)
                              setLineForm(lineFromRfq(line))
                            }}
                          >
                            Sửa
                          </button>
                          <button
                            className={ghostButtonClass}
                            disabled={!editable}
                            onClick={() => removeLine(line.id)}
                          >
                            Xóa
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        <div className="grid content-start gap-5">
          <div className="border border-white/10 bg-[#0b0d0f] p-5">
            <h3 className="font-serif text-2xl">
              {selectedRfq ? selectedRfq.rfq_number : "Tạo RFQ nháp"}
            </h3>
            <div className="mt-5 grid gap-4">
              <Labeled label="Khách hàng">
                <select
                  className={inputClass}
                  disabled={
                    !selectorsReady ||
                    selectedRfq !== null ||
                    pending ||
                    activeCreateAttempt
                  }
                  value={header.customerId}
                  onChange={(event) =>
                    setHeader({
                      ...header,
                      customerId: event.currentTarget.value,
                    })
                  }
                >
                  <option value="">Chọn khách hàng canonical</option>
                  {selectors.customers.map((customer) => (
                    <option key={customer.id} value={customer.id}>
                      {customer.customer_code} · {customer.company_name}
                    </option>
                  ))}
                </select>
              </Labeled>
              <FieldError state={command} name="customer_id" />
              <Labeled label="Dự án">
                <input
                  className={inputClass}
                  disabled={!headerEditable}
                  maxLength={220}
                  value={header.projectName}
                  onChange={(event) =>
                    setHeader({
                      ...header,
                      projectName: event.currentTarget.value,
                    })
                  }
                />
              </Labeled>
              <Labeled label="Ghi chú">
                <textarea
                  className={inputClass}
                  disabled={!headerEditable}
                  value={header.notes}
                  onChange={(event) =>
                    setHeader({ ...header, notes: event.currentTarget.value })
                  }
                />
              </Labeled>
              <div className="grid gap-4 sm:grid-cols-2">
                <Labeled label="Hạn báo giá">
                  <input
                    className={inputClass}
                    disabled={!headerEditable}
                    type="date"
                    value={header.quoteDueAt}
                    onChange={(event) =>
                      setHeader({
                        ...header,
                        quoteDueAt: event.currentTarget.value,
                      })
                    }
                  />
                </Labeled>
                <Labeled label="Ngày giao hàng">
                  <input
                    className={inputClass}
                    disabled={!headerEditable}
                    type="date"
                    value={header.requiredDeliveryDate}
                    onChange={(event) =>
                      setHeader({
                        ...header,
                        requiredDeliveryDate: event.currentTarget.value,
                      })
                    }
                  />
                </Labeled>
              </div>
              <FieldError state={command} name="quote_due_at" />
              <FieldError state={command} name="required_delivery_date" />
              {selectedRfq ? (
                <button
                  className={buttonClass}
                  disabled={!editable}
                  onClick={updateHeader}
                >
                  Lưu thông tin RFQ
                </button>
              ) : (
                <button
                  className={buttonClass}
                  disabled={!selectorsReady || pending}
                  onClick={createDraft}
                >
                  {createAttempt.hasUnreconciledCreate()
                    ? "Đồng bộ lại RFQ đã tạo"
                    : activeCreateAttempt
                      ? "Thử lại tạo RFQ"
                      : "Tạo bản nháp"}
                </button>
              )}
            </div>
          </div>

          {selectedRfq && (
            <div className="border border-white/10 bg-[#0b0d0f] p-5">
              <h3 className="font-serif text-2xl">
                {editingLineId === null ? "Thêm dòng RFQ" : "Cập nhật dòng RFQ"}
              </h3>
              <div className="mt-5 grid gap-4">
                <div className="grid gap-4 sm:grid-cols-2">
                  <Labeled label="Part canonical">
                    <select
                      className={inputClass}
                      disabled={!editable || !selectorsReady}
                      value={lineForm.partId}
                      onChange={(event) =>
                        setLineForm({
                          ...lineForm,
                          partId: event.currentTarget.value,
                        })
                      }
                    >
                      <option value="">Không chọn part</option>
                      {selectors.parts.map((part) => (
                        <option key={part.id} value={part.id}>
                          {part.part_code} · {part.name}
                        </option>
                      ))}
                    </select>
                  </Labeled>
                  <Labeled label="Vật liệu canonical">
                    <select
                      className={inputClass}
                      disabled={!editable || !selectorsReady}
                      value={lineForm.materialId}
                      onChange={(event) =>
                        setLineForm({
                          ...lineForm,
                          materialId: event.currentTarget.value,
                        })
                      }
                    >
                      <option value="">Không chọn vật liệu</option>
                      {selectors.materials.map((material) => (
                        <option key={material.id} value={material.id}>
                          {material.material_code} · {material.name}
                        </option>
                      ))}
                    </select>
                  </Labeled>
                </div>
                <Labeled label="Mô tả chi tiết">
                  <input
                    className={inputClass}
                    disabled={!editable}
                    value={lineForm.description}
                    onChange={(event) =>
                      setLineForm({
                        ...lineForm,
                        description: event.currentTarget.value,
                      })
                    }
                  />
                </Labeled>
                <div className="grid gap-4 sm:grid-cols-3">
                  <Labeled label="Số lượng">
                    <input
                      className={inputClass}
                      disabled={!editable}
                      inputMode="decimal"
                      value={lineForm.quantity}
                      onChange={(event) =>
                        setLineForm({
                          ...lineForm,
                          quantity: event.currentTarget.value,
                        })
                      }
                    />
                  </Labeled>
                  <Labeled label="Đơn vị">
                    <select
                      className={inputClass}
                      disabled={!editable}
                      value={lineForm.unit}
                      onChange={(event) =>
                        setLineForm({
                          ...lineForm,
                          unit: event.currentTarget.value as LineForm["unit"],
                        })
                      }
                    >
                      {(["PCS", "KG", "M", "MM"] as const).map((unit) => (
                        <option key={unit}>{unit}</option>
                      ))}
                    </select>
                  </Labeled>
                  <Labeled label="Ngày giao">
                    <input
                      className={inputClass}
                      disabled={!editable}
                      type="date"
                      value={lineForm.requiredDeliveryDate}
                      onChange={(event) =>
                        setLineForm({
                          ...lineForm,
                          requiredDeliveryDate: event.currentTarget.value,
                        })
                      }
                    />
                  </Labeled>
                </div>
                <Labeled label="Dung sai">
                  <input
                    className={inputClass}
                    disabled={!editable}
                    maxLength={120}
                    value={lineForm.tolerance}
                    onChange={(event) =>
                      setLineForm({
                        ...lineForm,
                        tolerance: event.currentTarget.value,
                      })
                    }
                  />
                </Labeled>
                <Labeled label="Ghi chú kỹ thuật">
                  <textarea
                    className={inputClass}
                    disabled={!editable}
                    value={lineForm.technicalNotes}
                    onChange={(event) =>
                      setLineForm({
                        ...lineForm,
                        technicalNotes: event.currentTarget.value,
                      })
                    }
                  />
                </Labeled>
                <FieldError state={command} name="lines" />
                <FieldError state={command} name="description" />
                <FieldError state={command} name="quantity" />
                <FieldError state={command} name="tolerance" />
                <FieldError state={command} name="technical_notes" />
                <div className="flex flex-wrap gap-3">
                  <button
                    className={buttonClass}
                    disabled={!editable}
                    onClick={saveLine}
                  >
                    {editingLineId === null ? "Thêm dòng" : "Lưu dòng"}
                  </button>
                  {editingLineId !== null && (
                    <button
                      className={ghostButtonClass}
                      disabled={!editable}
                      onClick={() => {
                        setEditingLineId(null)
                        setLineForm({
                          ...emptyLine,
                          requiredDeliveryDate:
                            selectedRfq.required_delivery_date ?? "",
                        })
                      }}
                    >
                      Hủy sửa
                    </button>
                  )}
                </div>
              </div>
            </div>
          )}

          {selectedRfq?.status === "DRAFT" && (
            <button
              className={buttonClass}
              disabled={!editable || lines.length === 0}
              onClick={submitDraft}
            >
              Gửi RFQ sang SUBMITTED
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
