import { useEffect, useState, type FormEvent } from "react"

import { CanonicalClientError } from "../api/canonical.ts"
import {
  askPublicComponentDemo,
  publicComponentDemoAvailable,
  type PublicComponentDemoResult,
} from "../api/aiDemo.ts"

const MAX_MESSAGE_LENGTH = 1200
const suggestions = [
  "Which synthetic product uses SUS316 with an electropolished finish?",
  "Which bushing uses oil-impregnated bronze?",
  "Which component has an electropolished finish?",
  "Which red anodized block has G1/8 pneumatic ports?",
]

type Turn = {
  id: number
  message: string
  result: PublicComponentDemoResult
}

function friendlyError(error: unknown) {
  if (error instanceof CanonicalClientError) {
    if (error.status === 429) return "Bạn đã gửi quá nhiều câu hỏi. Vui lòng thử lại sau."
    if (error.kind === "validation") return "Câu hỏi không hợp lệ hoặc quá dài."
    if (error.kind === "timeout") return "Yêu cầu đã hết thời gian chờ."
  }
  return "Hiện không thể kết nối trợ lý demo. Vui lòng thử lại sau."
}

export default function PublicComponentChatWidget() {
  const [available, setAvailable] = useState(false)
  const [open, setOpen] = useState(false)
  const [message, setMessage] = useState("")
  const [turns, setTurns] = useState<Turn[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")

  useEffect(() => {
    const controller = new AbortController()
    void publicComponentDemoAvailable({ signal: controller.signal, timeoutMs: 5000 })
      .then((enabled) => setAvailable(enabled))
      .catch(() => setAvailable(false))
    return () => controller.abort()
  }, [])

  const send = async (candidate = message) => {
    const normalized = candidate.trim()
    if (loading) return
    if (!normalized) {
      setError("Vui lòng nhập câu hỏi.")
      return
    }
    if (normalized.length > MAX_MESSAGE_LENGTH) {
      setError(`Câu hỏi tối đa ${MAX_MESSAGE_LENGTH} ký tự.`)
      return
    }
    setMessage(normalized)
    setError("")
    setLoading(true)
    try {
      const result = await askPublicComponentDemo(normalized)
      setTurns((current) => [
        ...current.slice(-19),
        { id: Date.now(), message: normalized, result },
      ])
      setMessage("")
    } catch (requestError) {
      setError(friendlyError(requestError))
    } finally {
      setLoading(false)
    }
  }

  const submit = (event: FormEvent) => {
    event.preventDefault()
    void send()
  }

  if (!available) return null

  return (
    <div className="fixed bottom-4 right-4 z-40 flex max-w-[calc(100vw-2rem)] flex-col items-end sm:bottom-6 sm:right-6">
      {open && (
        <section
          aria-label="AI Component Assistant"
          className="mb-3 flex max-h-[min(76vh,620px)] w-[min(380px,calc(100vw-2rem))] flex-col overflow-hidden border border-orange-500/30 bg-zinc-950 shadow-2xl shadow-black/60"
        >
          <header className="flex items-center justify-between border-b border-white/10 bg-zinc-900 px-4 py-3">
            <div>
              <h2 className="text-sm font-semibold">AI Component Assistant</h2>
              <p className="mt-1 text-[11px] text-zinc-400">Synthetic demo · không phải dữ liệu công ty</p>
            </div>
            <button aria-label="Đóng trợ lý AI" className="px-2 py-1 text-xl text-zinc-400 hover:text-white" onClick={() => setOpen(false)}>
              ×
            </button>
          </header>

          <div className="grid min-h-0 flex-1 content-start gap-3 overflow-y-auto p-4" aria-live="polite">
            <p className="border border-white/10 p-3 text-xs leading-5 text-zinc-300">
              Xin chào! Tôi có thể hỗ trợ tìm thông tin về linh kiện trong bộ dữ liệu synthetic thử nghiệm.
            </p>
            {turns.map((turn) => (
              <article className="grid gap-2" key={turn.id}>
                <div className="ml-6 border border-orange-500/30 bg-orange-500/10 p-3 text-xs">{turn.message}</div>
                <div className="mr-6 border border-white/10 p-3 text-xs">
                  <span className={turn.result.status === "SUPPORTED" ? "text-emerald-300" : "text-amber-200"}>
                    {turn.result.status}
                  </span>
                  <p className="mt-2 whitespace-pre-wrap leading-5 text-zinc-200">{turn.result.answer}</p>
                  {turn.result.status === "UNAVAILABLE" && (
                    <p className="mt-2 text-amber-200">Không có nguồn phù hợp trong dữ liệu demo.</p>
                  )}
                  {turn.result.sources.length > 0 && (
                    <div className="mt-3 border-t border-white/10 pt-2 text-zinc-400">
                      <div className="font-semibold">Nguồn tham khảo</div>
                      {turn.result.sources.map((source) => (
                        <div className="mt-1" key={`${turn.id}-${source.product_code}`}>
                          {source.title} · {source.product_code}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </article>
            ))}
            {loading && <p className="text-xs text-sky-200" role="status">Đang tìm nguồn và tạo câu trả lời…</p>}
            {error && <p className="text-xs text-red-300" role="alert">{error}</p>}
          </div>

          <div className="border-t border-white/10 p-3">
            {turns.length === 0 && (
              <div className="mb-3 flex flex-wrap gap-1.5">
                {suggestions.map((suggestion) => (
                  <button
                    className="border border-white/10 px-2 py-1 text-left text-[10px] leading-4 text-zinc-400 hover:border-orange-500"
                    disabled={loading}
                    key={suggestion}
                    onClick={() => void send(suggestion)}
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            )}
            <form className="flex gap-2" onSubmit={submit}>
              <input
                aria-label="Nhập câu hỏi cho trợ lý AI"
                className="min-w-0 flex-1 border border-white/10 bg-zinc-900 px-3 py-2 text-xs outline-none focus:border-orange-500"
                disabled={loading}
                maxLength={MAX_MESSAGE_LENGTH}
                onChange={(event) => setMessage(event.currentTarget.value)}
                placeholder="Nhập câu hỏi..."
                value={message}
              />
              <button className="bg-orange-600 px-3 py-2 text-xs font-semibold disabled:opacity-50" disabled={loading} type="submit">
                Gửi
              </button>
            </form>
          </div>
        </section>
      )}
      <button
        aria-expanded={open}
        aria-label={open ? "Ẩn AI Component Assistant" : "Mở AI Component Assistant"}
        className="rounded-full border border-orange-400/50 bg-orange-600 px-5 py-3 text-sm font-semibold text-white shadow-xl shadow-black/50 hover:bg-orange-500"
        onClick={() => setOpen((current) => !current)}
      >
        💬 AI Assistant
      </button>
    </div>
  )
}
