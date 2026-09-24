import { useRef, useState, type FormEvent } from "react"

import { analyzeAiSales, type AiSalesAnalysis, type AiSalesAnalyzeInput } from "../api/aiSales.ts"
import { CanonicalClientError } from "../api/canonical.ts"

type Props = {
  authenticated: boolean
  token: string | null
  onLoginRequired: () => void
  onAuthenticationFailure: () => void
}

const emptyInput: AiSalesAnalyzeInput = {
  customer_name: "",
  request: "",
  material: "",
  process: "",
  surface_treatment: "",
  tolerance: "",
  drawing_available: null,
  deadline: "",
}

const examples: Array<{ label: string; input: AiSalesAnalyzeInput }> = [
  {
    label: "SUS316 supported case",
    input: {
      customer_name: "Synthetic Precision Systems",
      request: "Need 100 SUS316 precision housings with CNC machining and electropolishing",
      material: "SUS316",
      quantity: 100,
      process: "CNC machining",
      surface_treatment: "electropolishing",
      tolerance: "per customer drawing",
      drawing_available: true,
      deadline: "2026-12-01",
    },
  },
  { label: "Unsupported weather case", input: { request: "What is the weather in Tokyo?" } },
  { label: "Incomplete request case", input: { request: "Need precision component." } },
]

function list(items: string[], empty: string) {
  if (items.length === 0) return <p className="mt-2 text-sm text-zinc-500">{empty}</p>
  return <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-zinc-300">{items.map((item) => <li key={item}>{item}</li>)}</ul>
}

export default function AiSalesPage({
  authenticated,
  token,
  onLoginRequired,
  onAuthenticationFailure,
}: Props) {
  const [input, setInput] = useState<AiSalesAnalyzeInput>(emptyInput)
  const [result, setResult] = useState<AiSalesAnalysis | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")
  const abortRef = useRef<AbortController | null>(null)

  const update = (field: keyof AiSalesAnalyzeInput, value: string | number | boolean | null) =>
    setInput((current) => ({ ...current, [field]: value }))

  const run = async (candidate = input) => {
    if (!authenticated || !token) {
      setError("Bạn cần đăng nhập bằng tài khoản Sales, Manager hoặc Admin.")
      return
    }
    abortRef.current?.abort()
    const controller = new AbortController()
    abortRef.current = controller
    setLoading(true)
    setError("")
    setResult(null)
    try {
      setResult(await analyzeAiSales(token, candidate, controller.signal))
    } catch (requestError) {
      if (requestError instanceof CanonicalClientError) {
        if (requestError.kind === "authentication") onAuthenticationFailure()
        if (requestError.kind === "permission") setError("Tài khoản không có quyền AI Sales nội bộ.")
        else if (requestError.kind === "validation") setError(requestError.message)
        else if (requestError.kind !== "cancelled") setError("Không thể phân tích yêu cầu lúc này.")
      } else setError("Không thể phân tích yêu cầu lúc này.")
    } finally {
      if (abortRef.current === controller) setLoading(false)
    }
  }

  const submit = (event: FormEvent) => {
    event.preventDefault()
    void run()
  }

  if (!authenticated) {
    return <section className="border border-white/10 p-7" data-testid="ai-sales-login-required">
      <p className="text-sm text-zinc-400">AI Sales chỉ dành cho người dùng nội bộ được cấp quyền.</p>
      <button className="mt-5 bg-orange-600 px-5 py-3 text-sm font-semibold" onClick={onLoginRequired}>Đăng nhập nội bộ</button>
    </section>
  }

  return <div className="grid gap-6" data-testid="admin-ai-sales-page">
    <section className="border border-amber-500/30 bg-amber-500/10 p-5">
      <div className="text-xs font-semibold uppercase tracking-[.2em] text-amber-200">AI recommendation — human review required</div>
      <p className="mt-2 text-sm text-zinc-300">Không tự động gửi email, tạo báo giá, thay đổi giá/đơn hàng/RFQ hoặc liên hệ khách hàng.</p>
    </section>

    <div className="grid gap-6 xl:grid-cols-[420px_1fr]">
      <form className="grid content-start gap-4 border border-white/10 p-5" onSubmit={submit}>
        <label className="grid gap-2 text-xs text-zinc-400">Khách hàng
          <input className="border border-white/10 bg-zinc-950 p-3 text-sm text-white" value={input.customer_name ?? ""} onChange={(e) => update("customer_name", e.currentTarget.value)} />
        </label>
        <label className="grid gap-2 text-xs text-zinc-400">Yêu cầu
          <textarea aria-label="Sales request" className="min-h-28 border border-white/10 bg-zinc-950 p-3 text-sm text-white" required value={input.request ?? ""} onChange={(e) => update("request", e.currentTarget.value)} />
        </label>
        <div className="grid grid-cols-2 gap-3">
          <label className="grid gap-2 text-xs text-zinc-400">Vật liệu<input className="border border-white/10 bg-zinc-950 p-3 text-sm text-white" value={input.material ?? ""} onChange={(e) => update("material", e.currentTarget.value)} /></label>
          <label className="grid gap-2 text-xs text-zinc-400">Số lượng<input className="border border-white/10 bg-zinc-950 p-3 text-sm text-white" min="0" type="number" value={input.quantity ?? ""} onChange={(e) => update("quantity", Number(e.currentTarget.value) || 0)} /></label>
          <label className="grid gap-2 text-xs text-zinc-400">Quy trình<input className="border border-white/10 bg-zinc-950 p-3 text-sm text-white" value={input.process ?? ""} onChange={(e) => update("process", e.currentTarget.value)} /></label>
          <label className="grid gap-2 text-xs text-zinc-400">Xử lý bề mặt<input className="border border-white/10 bg-zinc-950 p-3 text-sm text-white" value={input.surface_treatment ?? ""} onChange={(e) => update("surface_treatment", e.currentTarget.value)} /></label>
          <label className="grid gap-2 text-xs text-zinc-400">Dung sai<input className="border border-white/10 bg-zinc-950 p-3 text-sm text-white" value={input.tolerance ?? ""} onChange={(e) => update("tolerance", e.currentTarget.value)} /></label>
          <label className="grid gap-2 text-xs text-zinc-400">Deadline<input className="border border-white/10 bg-zinc-950 p-3 text-sm text-white" type="date" value={input.deadline ?? ""} onChange={(e) => update("deadline", e.currentTarget.value)} /></label>
        </div>
        <label className="flex items-center gap-2 text-sm text-zinc-300"><input checked={input.drawing_available === true} onChange={(e) => update("drawing_available", e.currentTarget.checked)} type="checkbox" />Đã có bản vẽ/tài liệu</label>
        <button className="bg-orange-600 px-5 py-3 text-sm font-semibold disabled:opacity-50" disabled={loading} type="submit">{loading ? "Đang phân tích…" : "Phân tích cơ hội"}</button>
        <div className="grid gap-2 border-t border-white/10 pt-4">
          {examples.map((example) => <button className="border border-white/10 p-3 text-left text-xs hover:border-orange-500" key={example.label} onClick={() => { setInput({ ...emptyInput, ...example.input }); void run(example.input) }} type="button">{example.label}</button>)}
        </div>
      </form>

      <section aria-live="polite" className="grid content-start gap-4">
        {error && <div className="border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-100" role="alert">{error}</div>}
        {!result && !error && !loading && <div className="border border-white/10 p-6 text-sm text-zinc-500">Chọn một demo synthetic hoặc nhập cơ hội/RFQ cần phân tích.</div>}
        {result && <>
          <article className="border border-white/10 p-5">
            <div className="flex flex-wrap items-center gap-3"><b>{result.status}</b><span className="border border-orange-500/40 px-2 py-1 text-xs">Priority {result.priority}</span>{result.synthetic_input && <span className="text-xs text-sky-300">SYNTHETIC INPUT</span>}</div>
            <p className="mt-4 text-sm leading-6 text-zinc-300">{result.summary}</p>
            <h3 className="mt-5 text-xs font-semibold uppercase tracking-wider">Why</h3>{list(result.priority_reasons, "Không có lý do ưu tiên.")}
          </article>
          <article className="grid gap-5 border border-white/10 p-5 md:grid-cols-2">
            <div><h3 className="text-xs font-semibold uppercase tracking-wider">Matched components</h3>{result.matched_products.length ? result.matched_products.map((item) => <div className="mt-3 border border-white/10 p-3 text-sm" key={item.product_code}><b>{item.product_code}</b><div className="text-zinc-400">{item.title}</div><p className="mt-2 text-xs text-zinc-500">{item.reason}</p></div>) : <p className="mt-2 text-sm text-zinc-500">Không có component được đề xuất.</p>}</div>
            <div><h3 className="text-xs font-semibold uppercase tracking-wider">Missing information</h3>{list(result.missing_information, "Không phát hiện thiếu thông tin bắt buộc.")}<h3 className="mt-5 text-xs font-semibold uppercase tracking-wider">Risks</h3>{list(result.risks, "Không có rủi ro bổ sung.")}</div>
          </article>
          <article className="border border-white/10 p-5"><h3 className="text-xs font-semibold uppercase tracking-wider">Recommended next action</h3><b className="mt-2 block text-orange-300">{result.recommended_next_action}</b><p className="mt-2 text-sm text-zinc-400">{result.recommended_next_action_reason}</p></article>
          <article className="border border-amber-500/30 p-5"><h3 className="text-xs font-semibold uppercase tracking-wider">Draft response · review before use</h3><pre className="mt-3 whitespace-pre-wrap font-sans text-sm leading-6 text-zinc-300">{result.draft_response}</pre></article>
          <article className="border border-white/10 p-5"><h3 className="text-xs font-semibold uppercase tracking-wider">Sources</h3>{result.sources.length ? result.sources.map((source) => <div className="mt-3 border border-white/10 p-3 text-xs" key={`${source.id}-${source.product_code}`}><b>{source.product_code} · {source.title}</b><div className="mt-1 break-all text-zinc-500">{source.citation}</div></div>) : <p className="mt-2 text-sm text-zinc-500">Không có nguồn hỗ trợ.</p>}<p className="mt-4 text-xs text-zinc-600">Request ID: {result.request_id}</p></article>
        </>}
      </section>
    </div>
  </div>
}
