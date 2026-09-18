import { useRef, useState, type FormEvent } from "react"

import {
  askInternalKnowledge,
  type CanonicalClient,
  type KnowledgeAiResult,
} from "../api/ai.ts"
import { CanonicalClientError } from "../api/canonical.ts"

type Props = {
  authenticated: boolean
  client: CanonicalClient
  onAuthenticationFailure: () => void
  goToLogin: () => void
}

export default function KnowledgeAssistantWorkspace({
  authenticated,
  client,
  onAuthenticationFailure,
  goToLogin,
}: Props) {
  const [question, setQuestion] = useState("")
  const [result, setResult] = useState<KnowledgeAiResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState("")
  const abortRef = useRef<AbortController | null>(null)

  const submit = (event: FormEvent) => {
    event.preventDefault()
    if (!authenticated) {
      goToLogin()
      return
    }
    abortRef.current?.abort()
    const controller = new AbortController()
    abortRef.current = controller
    setLoading(true)
    setMessage("")
    void askInternalKnowledge(client, question, controller.signal)
      .then((nextResult) => {
        setResult(nextResult)
        setLoading(false)
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
        setMessage(
          error instanceof CanonicalClientError && error.kind === "permission"
            ? "Tài khoản không có quyền đọc kho tri thức."
            : "Không thể tra cứu tài liệu lúc này.",
        )
        setLoading(false)
      })
  }

  return (
    <div className="grid gap-5 lg:grid-cols-[1fr_340px]">
      <section className="border border-white/10 p-6">
        <h3 className="font-semibold">Hỏi kho tri thức nội bộ</h3>
        <form className="mt-5 flex gap-3" onSubmit={submit}>
          <input
            aria-label="Câu hỏi tài liệu nội bộ"
            className="min-w-0 flex-1 border border-white/10 bg-zinc-950 px-4 py-3"
            maxLength={1200}
            placeholder="Hỏi về quy trình, tiêu chuẩn, vật liệu hoặc năng lực kỹ thuật…"
            required
            value={question}
            onChange={(event) => setQuestion(event.currentTarget.value)}
          />
          <button
            className="bg-orange-600 px-5 py-3 text-xs font-semibold uppercase tracking-widest text-white disabled:opacity-60"
            disabled={loading}
            type="submit"
          >
            {loading ? "Đang tìm…" : "Hỏi AI"}
          </button>
        </form>
        {message && (
          <p role="alert" className="mt-4 text-sm text-orange-400">
            {message}
          </p>
        )}
        <div
          aria-live="polite"
          className="mt-8 min-h-48 border border-white/10 bg-zinc-900/40 p-5"
        >
          {result ? (
            <>
              <p className="whitespace-pre-wrap text-sm leading-7 text-zinc-200">
                {result.answer}
              </p>
              {result.warning && (
                <p className="mt-4 text-xs text-amber-300">{result.warning}</p>
              )}
            </>
          ) : (
            <p className="text-sm text-zinc-500">
              Câu trả lời sẽ xuất hiện tại đây và luôn kèm nguồn nếu có.
            </p>
          )}
        </div>
      </section>
      <aside className="border border-white/10 p-5">
        <h3 className="font-semibold">Nguồn được sử dụng</h3>
        {!result?.sources.length ? (
          <p className="mt-4 text-sm text-zinc-500">Chưa có nguồn phù hợp.</p>
        ) : (
          <ul className="mt-4 grid gap-3">
            {result.sources.map((source) => (
              <li
                className="border border-white/10 p-3 text-sm"
                key={`${source.id}-${source.title}`}
              >
                <b>{source.title}</b>
                {typeof source.relevance_score === "number" && (
                  <div className="mt-2 text-xs text-zinc-500">
                    Độ liên quan {Math.round(source.relevance_score * 100)}%
                  </div>
                )}
              </li>
            ))}
          </ul>
        )}
      </aside>
    </div>
  )
}
