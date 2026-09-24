import { useState, type FormEvent } from "react"

import { CanonicalClientError } from "../api/canonical.ts"
import {
  askSyntheticRagChat,
  type RagChatResult,
} from "../api/aiDemo.ts"

const MAX_MESSAGE_LENGTH = 1200
const suggestions = [
  "Which synthetic product uses SUS316 with an electropolished finish?",
  "Which bushing is made from oil-impregnated bronze?",
  "Which red anodized block has G1/8 pneumatic ports?",
  "What is the sales price of SYN-RAG-0001?",
  "Thời tiết Tokyo hôm nay thế nào?",
]

type Turn = {
  id: number
  question: string
  result: RagChatResult
}

type Props = {
  token: string | null
  onLoginRequired: () => void
  onAuthenticationFailure: () => void
}

function errorMessage(error: unknown) {
  if (error instanceof CanonicalClientError) {
    if (error.kind === "authentication") return "Phiên đăng nhập đã hết hạn."
    if (error.kind === "permission") return "Tài khoản không có quyền knowledge:read."
    if (error.kind === "validation") return error.message
    if (error.kind === "timeout") return "Chatbot đã hết thời gian chờ phản hồi."
    if (error.kind === "network") return "Không thể kết nối Django Chat API."
  }
  return "Không thể xử lý câu hỏi. Chatbot không tạo câu trả lời thay thế."
}

export default function RagChatPage({
  token,
  onLoginRequired,
  onAuthenticationFailure,
}: Props) {
  const [message, setMessage] = useState("")
  const [turns, setTurns] = useState<Turn[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")

  const send = async (candidate = message) => {
    const normalized = candidate.trim()
    if (!normalized) {
      setError("Vui lòng nhập câu hỏi.")
      return
    }
    if (normalized.length > MAX_MESSAGE_LENGTH) {
      setError(`Câu hỏi không được vượt quá ${MAX_MESSAGE_LENGTH} ký tự.`)
      return
    }
    if (!token) {
      setError("Bạn cần đăng nhập bằng tài khoản nội bộ.")
      return
    }

    setMessage(normalized)
    setLoading(true)
    setError("")
    try {
      const result = await askSyntheticRagChat(token, normalized)
      setTurns((current) => [
        ...current,
        { id: Date.now(), question: normalized, result },
      ])
      setMessage("")
    } catch (requestError) {
      if (
        requestError instanceof CanonicalClientError &&
        requestError.kind === "authentication"
      ) {
        onAuthenticationFailure()
      }
      setError(errorMessage(requestError))
    } finally {
      setLoading(false)
    }
  }

  const submit = (event: FormEvent) => {
    event.preventDefault()
    void send()
  }

  if (!token) {
    return (
      <section className="border border-white/10 bg-zinc-950 p-7">
        <h2 className="font-serif text-3xl">AI Component Assistant</h2>
        <p className="mt-3 text-sm text-zinc-400">
          Bản demo này dùng corpus synthetic nội bộ và yêu cầu đăng nhập.
        </p>
        <button className="mt-5 bg-orange-600 px-5 py-3 text-sm font-semibold" onClick={onLoginRequired}>
          Đăng nhập nội bộ
        </button>
      </section>
    )
  }

  return (
    <div className="grid gap-6" data-testid="rag-chat-page">
      <section className="border border-amber-500/30 bg-amber-500/10 p-5">
        <div className="text-xs font-semibold uppercase tracking-[.22em] text-amber-200">
          AI Component Assistant · Internal RAG Demo
        </div>
        <p className="mt-3 text-sm leading-6 text-zinc-300">
          Xin chào! Tôi trả lời từ 25 hồ sơ sản phẩm synthetic trong
          <b> rag_synthetic_demo_v1</b>. Đây chưa phải dữ liệu xe hoặc dữ liệu thật của công ty.
        </p>
      </section>

      <div className="grid gap-6 xl:grid-cols-[380px_1fr]">
        <section className="border border-white/10 p-5">
          <form onSubmit={submit}>
            <label className="grid gap-2">
              <span className="text-[10px] uppercase tracking-[.2em] text-zinc-500">Câu hỏi</span>
              <textarea
                aria-label="Chat message"
                className="min-h-32 border border-white/10 bg-zinc-950 p-4 text-sm outline-none focus:border-orange-500"
                disabled={loading}
                maxLength={MAX_MESSAGE_LENGTH}
                onChange={(event) => setMessage(event.currentTarget.value)}
                placeholder="Ví dụ: Sản phẩm synthetic nào dùng SUS316?"
                value={message}
              />
            </label>
            <div className="mt-2 text-right text-xs text-zinc-600">
              {message.length}/{MAX_MESSAGE_LENGTH}
            </div>
            <button
              className="mt-3 w-full bg-orange-600 px-5 py-3 text-sm font-semibold disabled:opacity-50"
              disabled={loading}
              type="submit"
            >
              {loading ? "Đang truy xuất RAG…" : "Gửi"}
            </button>
          </form>

          <div className="mt-7 text-[10px] uppercase tracking-[.2em] text-zinc-500">Câu hỏi mẫu</div>
          <div className="mt-3 grid gap-2">
            {suggestions.map((suggestion) => (
              <button
                className="border border-white/10 p-3 text-left text-xs leading-5 hover:border-orange-500 disabled:opacity-50"
                disabled={loading}
                key={suggestion}
                onClick={() => void send(suggestion)}
              >
                {suggestion}
              </button>
            ))}
          </div>
        </section>

        <section className="grid content-start gap-4" aria-live="polite">
          {turns.length === 0 && !loading && !error && (
            <div className="border border-white/10 p-6 text-sm text-zinc-500">
              Hội thoại chỉ được giữ trong bộ nhớ của trình duyệt trong phiên hiện tại.
            </div>
          )}
          {turns.map((turn) => (
            <article className="grid gap-3" key={turn.id}>
              <div className="ml-auto max-w-[85%] border border-orange-500/30 bg-orange-500/10 p-4">
                <div className="text-[10px] uppercase tracking-widest text-orange-300">User</div>
                <p className="mt-2 whitespace-pre-wrap text-sm">{turn.question}</p>
              </div>
              <div className="max-w-[92%] border border-white/10 bg-white/[.02] p-5">
                <div className="flex items-center justify-between gap-3">
                  <span className="text-[10px] uppercase tracking-widest text-zinc-500">AI</span>
                  <span className={turn.result.status === "SUPPORTED" ? "text-xs text-emerald-300" : "text-xs text-amber-200"}>
                    {turn.result.status}
                  </span>
                </div>
                <p className="mt-3 whitespace-pre-wrap text-sm leading-7 text-zinc-300">{turn.result.answer}</p>
                <div className="mt-5 border-t border-white/10 pt-4">
                  <h3 className="text-xs font-semibold uppercase tracking-wider">Nguồn tham khảo</h3>
                  {turn.result.sources.length === 0 ? (
                    <p className="mt-2 text-xs text-zinc-500">Không có nguồn hỗ trợ; câu hỏi được trả về UNAVAILABLE.</p>
                  ) : (
                    <ol className="mt-3 grid gap-2">
                      {turn.result.sources.map((source) => (
                        <li className="border border-white/10 p-3 text-xs" key={`${turn.id}-${source.document_id}-${source.chunk_id}`}>
                          <div className="font-medium">{source.title} · {source.product_code}</div>
                          <div className="mt-1 text-zinc-500">v{source.version} / rev {source.revision} · chunk {source.chunk_id}</div>
                          <div className="mt-1 break-all text-zinc-500">{source.citation}</div>
                        </li>
                      ))}
                    </ol>
                  )}
                </div>
              </div>
            </article>
          ))}
          {loading && (
            <div className="border border-sky-500/30 bg-sky-500/10 p-4 text-sm text-sky-100" role="status">
              Đang truy xuất context, gọi local LLM và kiểm tra grounding…
            </div>
          )}
          {error && <div className="border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-100" role="alert">{error}</div>}
        </section>
      </div>
    </div>
  )
}
