import { useState } from "react"

import { CanonicalClientError } from "../api/canonical.ts"
import {
  askSyntheticRagDemo,
  type RagDemoResult,
} from "../api/aiDemo.ts"

const DATASET_ID = "rag_synthetic_demo_v1"
const samples = [
  "Which synthetic product uses SUS316 with an electropolished finish?",
  "Find the oil-impregnated bronze pivot bushing.",
  "Which red anodized block has G1/8 pneumatic ports?",
  "Which fixture uses a locating-hole grid for camera inspection?",
  "Which synthetic guide has a fit clearance of 0.008 mm?",
  "Cite the synthetic record with a 25 mm grid pitch and blue anodized finish.",
  "What is the sales price of SYN-RAG-0001?",
  "Which customer ordered the optical sensor housing?",
]

type Props = {
  token: string | null
  onLoginRequired: () => void
  onAuthenticationFailure: () => void
}

function humanError(error: unknown) {
  if (error instanceof CanonicalClientError) {
    if (error.kind === "permission") return "Tài khoản không có quyền sử dụng RAG demo nội bộ."
    if (error.kind === "authentication") return "Phiên đăng nhập đã hết hạn."
    if (error.kind === "validation") return error.message
    if (error.kind === "timeout") return "Yêu cầu RAG đã hết thời gian chờ."
    if (error.kind === "network") return "Không thể kết nối API RAG nội bộ."
  }
  return "Không thể xử lý câu hỏi. Không có câu trả lời thay thế được tạo."
}

export default function RagDemoPage({
  token,
  onLoginRequired,
  onAuthenticationFailure,
}: Props) {
  const [question, setQuestion] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")
  const [result, setResult] = useState<RagDemoResult | null>(null)

  const ask = async (candidate = question) => {
    const normalized = candidate.trim()
    setQuestion(normalized)
    setResult(null)
    if (!normalized) {
      setError("Nhập câu hỏi trước khi gửi.")
      return
    }
    if (!token) {
      setError("Cần đăng nhập bằng tài khoản nội bộ.")
      return
    }
    setLoading(true)
    setError("")
    try {
      setResult(await askSyntheticRagDemo(token, normalized))
    } catch (requestError) {
      if (
        requestError instanceof CanonicalClientError &&
        requestError.kind === "authentication"
      ) {
        onAuthenticationFailure()
      }
      setError(humanError(requestError))
    } finally {
      setLoading(false)
    }
  }

  if (!token) {
    return (
      <section className="border border-white/10 bg-zinc-950 p-6">
        <h2 className="text-xl font-semibold">Internal RAG Technical Demo</h2>
        <p className="mt-3 text-sm text-zinc-400">
          Trang này chỉ dành cho người dùng nội bộ đã xác thực.
        </p>
        <button
          className="mt-5 bg-orange-600 px-5 py-3 text-sm font-semibold text-white"
          onClick={onLoginRequired}
        >
          Đăng nhập nội bộ
        </button>
      </section>
    )
  }

  const citationFailure = result?.status === "SUPPORTED" && result.sources.length === 0

  return (
    <div className="grid gap-6" data-testid="internal-rag-demo-page">
      <section className="border border-red-500/40 bg-red-500/10 p-5">
        <div className="text-xs font-semibold uppercase tracking-[.24em] text-red-300">
          SYNTHETIC DEMO DATA — NOT REAL COMPANY DATA
        </div>
        <div className="mt-3 flex flex-wrap gap-x-6 gap-y-2 text-sm text-zinc-300">
          <span>Dataset: <b>{DATASET_ID}</b></span>
          <span>25 synthetic products</span>
          <span>Internal engineering validation only</span>
        </div>
      </section>

      <div className="grid gap-6 xl:grid-cols-[minmax(320px,420px)_1fr]">
        <section className="border border-white/10 p-5">
          <h2 className="font-semibold">Câu hỏi kỹ thuật</h2>
          <label className="mt-4 grid gap-2">
            <span className="text-[10px] uppercase tracking-[.2em] text-zinc-500">
              Natural-language question
            </span>
            <textarea
              aria-label="RAG demo question"
              className="min-h-32 border border-white/10 bg-zinc-950 p-4 text-sm outline-none focus:border-orange-500 focus-visible:ring-2 focus-visible:ring-orange-400"
              disabled={loading}
              onChange={(event) => setQuestion(event.currentTarget.value)}
              placeholder="Ask only about the controlled synthetic Product corpus…"
              value={question}
            />
          </label>
          <button
            className="mt-4 bg-orange-600 px-5 py-3 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-50"
            disabled={loading}
            onClick={() => void ask()}
          >
            {loading ? "Đang truy xuất…" : "Ask RAG"}
          </button>

          <div className="mt-7">
            <div className="text-[10px] uppercase tracking-[.2em] text-zinc-500">
              Gold-set samples
            </div>
            <div className="mt-3 grid gap-2">
              {samples.map((sample) => (
                <button
                  className="border border-white/10 p-3 text-left text-xs leading-5 text-zinc-300 hover:border-orange-500 disabled:opacity-50"
                  disabled={loading}
                  key={sample}
                  onClick={() => void ask(sample)}
                >
                  {sample}
                </button>
              ))}
            </div>
          </div>
        </section>

        <div className="grid content-start gap-5" aria-live="polite">
          {loading && (
            <section className="border border-sky-500/30 bg-sky-500/10 p-5 text-sm text-sky-100">
              Đang truy xuất corpus synthetic và kiểm tra grounding…
            </section>
          )}
          {error && (
            <section className="border border-red-500/30 bg-red-500/10 p-5 text-sm text-red-100" role="alert">
              {error}
            </section>
          )}
          {!loading && !error && !result && (
            <section className="border border-white/10 p-6 text-sm text-zinc-500">
              Chưa có truy vấn trong phiên này.
            </section>
          )}
          {result && (
            <>
              <section className="border border-white/10 p-6">
                <div className="flex items-center justify-between gap-3">
                  <h2 className="font-semibold">Answer</h2>
                  <span className={result.status === "SUPPORTED" ? "border border-emerald-500/30 bg-emerald-500/10 px-2 py-1 text-xs text-emerald-300" : "border border-amber-500/30 bg-amber-500/10 px-2 py-1 text-xs text-amber-200"}>
                    {result.status}
                  </span>
                </div>
                <p className="mt-4 whitespace-pre-wrap text-sm leading-7 text-zinc-300">
                  {result.answer}
                </p>
              </section>

              <section className="border border-white/10 p-6">
                <h2 className="font-semibold">Sources</h2>
                {citationFailure && (
                  <div className="mt-4 border border-red-500/30 bg-red-500/10 p-3 text-sm text-red-100">
                    Citation rendering failure: supported answer has no source.
                  </div>
                )}
                {result.sources.length === 0 ? (
                  <p className="mt-4 text-sm text-zinc-500">
                    Không có citation vì câu hỏi được xác định là UNAVAILABLE.
                  </p>
                ) : (
                  <ol className="mt-4 grid gap-3">
                    {result.sources.map((source) => (
                      <li className="border border-white/10 bg-white/[.02] p-4" key={`${source.document_id}-${source.chunk_id}`}>
                        <div className="font-medium">{source.title}</div>
                        <dl className="mt-3 grid gap-2 text-xs text-zinc-400 sm:grid-cols-2">
                          <div><dt className="text-zinc-600">Product code</dt><dd>{source.product_code}</dd></div>
                          <div><dt className="text-zinc-600">Revision</dt><dd>{source.revision} · document v{source.version}</dd></div>
                          <div className="sm:col-span-2"><dt className="text-zinc-600">Citation</dt><dd className="break-all">{source.citation}</dd></div>
                          <div><dt className="text-zinc-600">Document / chunk</dt><dd>{source.document_id} / {source.chunk_id}</dd></div>
                          <div><dt className="text-zinc-600">Relevance</dt><dd>{source.relevance_score.toFixed(4)}</dd></div>
                        </dl>
                      </li>
                    ))}
                  </ol>
                )}
              </section>

              <section className="border border-white/10 p-6">
                <h2 className="font-semibold">Technical diagnostics</h2>
                <dl className="mt-4 grid gap-3 text-sm sm:grid-cols-2">
                  <div><dt className="text-zinc-500">Provider</dt><dd>{result.retrieval.provider}</dd></div>
                  <div><dt className="text-zinc-500">Provider mode</dt><dd>{result.retrieval.provider_mode}</dd></div>
                  <div><dt className="text-zinc-500">Retrieved documents/chunks</dt><dd>{result.retrieval.result_count}</dd></div>
                  <div><dt className="text-zinc-500">Corpus documents</dt><dd>{result.retrieval.corpus_documents}</dd></div>
                  <div><dt className="text-zinc-500">Dataset</dt><dd>{result.retrieval.dataset_id}</dd></div>
                  <div><dt className="text-zinc-500">Status</dt><dd>{result.status}</dd></div>
                  <div><dt className="text-zinc-500">Generation</dt><dd>{result.retrieval.generation_provider || "not called"}</dd></div>
                  <div><dt className="text-zinc-500">Confidence</dt><dd>{result.retrieval.confidence?.toFixed(4) || "n.a."}</dd></div>
                </dl>
                {result.retrieval.provider_mode === "development-hash-plus-lexical" && (
                  <p className="mt-4 border-l-2 border-amber-500 pl-3 text-xs leading-5 text-amber-200">
                    Development hash embedding + lexical reranking. This is not labelled as semantic embedding.
                  </p>
                )}
              </section>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
