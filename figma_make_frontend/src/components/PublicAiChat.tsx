import { useRef, useState, type FormEvent } from "react"

import { askPublicAssistant, type KnowledgeAiResult } from "../api/ai.ts"

export default function PublicAiChat({
  goToContact,
}: {
  goToContact: () => void
}) {
  const [open, setOpen] = useState(false)
  const [question, setQuestion] = useState("")
  const [result, setResult] = useState<KnowledgeAiResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState("")
  const abortRef = useRef<AbortController | null>(null)

  const submit = (event: FormEvent) => {
    event.preventDefault()
    abortRef.current?.abort()
    const controller = new AbortController()
    abortRef.current = controller
    setLoading(true)
    setMessage("")
    void askPublicAssistant(question, { signal: controller.signal })
      .then((nextResult) => {
        setResult(nextResult)
        setLoading(false)
      })
      .catch(() => {
        if (controller.signal.aborted) return
        setMessage(
          "Trợ lý đang bận. Bạn có thể gửi yêu cầu để nhân viên tư vấn.",
        )
        setLoading(false)
      })
  }

  return (
    <div className="fixed bottom-16 right-5 z-50">
      {open && (
        <section className="mb-3 w-[min(380px,calc(100vw-2.5rem))] border border-white/15 bg-zinc-950 p-5 shadow-2xl">
          <div className="flex items-start justify-between gap-4">
            <div>
              <h2 className="font-semibold">Trợ lý MecPrecision</h2>
              <p className="mt-1 text-xs text-zinc-500">
                Chỉ sử dụng thông tin công khai
              </p>
            </div>
            <button
              aria-label="Đóng trợ lý AI"
              className="text-zinc-400"
              onClick={() => setOpen(false)}
            >
              ×
            </button>
          </div>
          <div
            aria-live="polite"
            className="mt-4 min-h-28 border border-white/10 bg-zinc-900/60 p-4 text-sm"
          >
            {result?.answer ||
              "Bạn có thể hỏi về sản phẩm, vật liệu và năng lực gia công."}
          </div>
          {result?.sources && result.sources.length > 0 && (
            <p className="mt-2 text-xs text-zinc-500">
              Nguồn: {result.sources.map((source) => source.title).join(", ")}
            </p>
          )}
          {message && (
            <p role="alert" className="mt-3 text-xs text-orange-400">
              {message}
            </p>
          )}
          <form className="mt-4 grid gap-3" onSubmit={submit}>
            <input
              aria-label="Câu hỏi cho trợ lý MecPrecision"
              className="border border-white/10 bg-black px-4 py-3 text-sm"
              maxLength={800}
              placeholder="Ví dụ: Công ty có gia công SUS304 không?"
              required
              value={question}
              onChange={(event) => setQuestion(event.currentTarget.value)}
            />
            <button
              className="bg-orange-600 px-4 py-3 text-xs font-semibold uppercase tracking-widest"
              disabled={loading}
              type="submit"
            >
              {loading ? "Đang trả lời…" : "Gửi câu hỏi"}
            </button>
          </form>
          {(result?.contact_recommended || message) && (
            <button
              className="mt-3 w-full border border-white/15 px-4 py-3 text-xs"
              onClick={goToContact}
            >
              Chuyển sang yêu cầu tư vấn
            </button>
          )}
        </section>
      )}
      <button
        aria-expanded={open}
        aria-label="Mở trợ lý AI"
        className="ml-auto block bg-orange-600 px-5 py-3 text-xs font-semibold uppercase tracking-widest text-white shadow-xl"
        onClick={() => setOpen((value) => !value)}
      >
        AI tư vấn
      </button>
    </div>
  )
}
