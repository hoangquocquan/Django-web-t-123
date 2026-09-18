import { useRef, useState, type FormEvent } from "react"

import {
  requestSalesAssistance,
  type CanonicalClient,
  type SalesAiAction,
  type SalesAiResult,
} from "../api/ai.ts"
import { CanonicalClientError } from "../api/canonical.ts"

type Props = {
  authenticated: boolean
  client: CanonicalClient
  onAuthenticationFailure: () => void
  goToLogin: () => void
}

function messageFor(error: unknown): string {
  if (error instanceof CanonicalClientError) {
    if (error.kind === "authentication") return "Phiên đăng nhập đã hết hạn."
    if (error.kind === "permission")
      return "Tài khoản không có quyền dùng AI Sales."
    if (error.kind === "timeout") return "AI phản hồi quá thời gian chờ."
    if (error.kind === "network") return "Không thể kết nối dịch vụ AI."
  }
  return "Không thể hoàn thành yêu cầu AI lúc này."
}

export default function AiSalesWorkspace({
  authenticated,
  client,
  onAuthenticationFailure,
  goToLogin,
}: Props) {
  const [action, setAction] = useState<SalesAiAction>("weekly_recommendation")
  const [company, setCompany] = useState("")
  const [contact, setContact] = useState("")
  const [details, setDetails] = useState("")
  const [result, setResult] = useState<SalesAiResult | null>(null)
  const [status, setStatus] = useState<"idle" | "loading" | "error">("idle")
  const [message, setMessage] = useState("")
  const abortRef = useRef<AbortController | null>(null)

  const submit = (event: FormEvent) => {
    event.preventDefault()
    if (!authenticated) {
      goToLogin()
      return
    }
    const payload =
      action === "weekly_recommendation"
        ? {}
        : action === "lead_analysis"
          ? {
              company,
              contact_person: contact,
              notes: details,
              industry: "precision manufacturing",
            }
          : {
              company,
              recipient_name: contact,
              product_interest: details,
              purpose: "follow_up",
            }
    abortRef.current?.abort()
    const controller = new AbortController()
    abortRef.current = controller
    setStatus("loading")
    setMessage("")
    void requestSalesAssistance(client, action, payload, controller.signal)
      .then((nextResult) => {
        setResult(nextResult)
        setStatus("idle")
      })
      .catch((error) => {
        if (controller.signal.aborted) return
        if (
          error instanceof CanonicalClientError &&
          error.kind === "authentication"
        ) {
          onAuthenticationFailure()
          return
        }
        setMessage(messageFor(error))
        setStatus("error")
      })
  }

  return (
    <div className="grid gap-5 lg:grid-cols-[380px_1fr]">
      <form
        onSubmit={submit}
        className="grid content-start gap-4 border border-white/10 p-6"
      >
        <label className="grid gap-2 text-sm">
          <span>Loại hỗ trợ</span>
          <select
            className="border border-white/10 bg-zinc-950 px-4 py-3"
            value={action}
            onChange={(event) =>
              setAction(event.currentTarget.value as SalesAiAction)
            }
          >
            <option value="weekly_recommendation">
              Ưu tiên bán hàng tuần này
            </option>
            <option value="lead_analysis">Phân tích lead</option>
            <option value="email_draft">Soạn email theo dõi</option>
          </select>
        </label>
        {action !== "weekly_recommendation" && (
          <>
            <input
              aria-label="Tên công ty"
              className="border border-white/10 bg-zinc-950 px-4 py-3"
              placeholder="Tên công ty"
              required
              value={company}
              onChange={(event) => setCompany(event.currentTarget.value)}
            />
            <input
              aria-label="Người liên hệ"
              className="border border-white/10 bg-zinc-950 px-4 py-3"
              placeholder="Người liên hệ"
              required
              value={contact}
              onChange={(event) => setContact(event.currentTarget.value)}
            />
            <textarea
              aria-label="Thông tin cần AI hỗ trợ"
              className="min-h-28 border border-white/10 bg-zinc-950 p-4"
              placeholder="Nhu cầu, vật liệu, số lượng hoặc mục đích email"
              value={details}
              onChange={(event) => setDetails(event.currentTarget.value)}
            />
          </>
        )}
        <button
          className="bg-orange-600 px-5 py-3 text-xs font-semibold uppercase tracking-widest text-white disabled:opacity-60"
          disabled={status === "loading"}
          type="submit"
        >
          {status === "loading" ? "AI đang phân tích…" : "Yêu cầu AI hỗ trợ"}
        </button>
        {message && (
          <p role="alert" className="text-sm text-orange-400">
            {message}
          </p>
        )}
      </form>

      <section aria-live="polite" className="border border-white/10 p-6">
        <h3 className="font-semibold">Kết quả tư vấn</h3>
        {!result ? (
          <p className="mt-5 text-sm text-zinc-500">
            AI chỉ đưa ra gợi ý. Mọi email, thay đổi CRM và báo giá đều cần con
            người duyệt.
          </p>
        ) : (
          <div className="mt-5 grid gap-5 text-sm">
            {result.analysis && (
              <p className="text-zinc-300">{result.analysis}</p>
            )}
            {result.recommendations && (
              <ul className="list-disc space-y-2 pl-5 text-zinc-300">
                {result.recommendations.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            )}
            {result.leads_to_contact && (
              <ul className="space-y-2">
                {result.leads_to_contact.map((lead) => (
                  <li className="border border-white/10 p-3" key={lead.id}>
                    <b>{lead.company}</b> · {lead.contact_person}
                  </li>
                ))}
              </ul>
            )}
            {result.draft && (
              <div className="border border-orange-500/30 bg-orange-500/5 p-4">
                <b>{result.draft.subject || "Email nháp"}</b>
                <p className="mt-3 whitespace-pre-wrap text-zinc-300">
                  {result.draft.body}
                </p>
              </div>
            )}
            <p className="border-l-2 border-amber-500 pl-3 text-xs text-amber-300">
              {result.safety_note ||
                "Cần nhân viên kiểm tra và phê duyệt trước khi sử dụng."}
            </p>
          </div>
        )}
      </section>
    </div>
  )
}
