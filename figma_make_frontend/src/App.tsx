import {
  useEffect,
  useMemo,
  useRef,
  useState,
  type FormEvent,
  type ReactNode,
} from "react"

import {
  CanonicalClientError,
  InMemoryAuthSession,
  createCanonicalClient,
} from "./api/canonical.ts"
import {
  canonicalBaseUrlForPhase5b,
  createFoundationAuthClient,
  type FoundationUser,
} from "./api/foundation.ts"
import {
  createLatestRequestGuard,
  fetchRfqPage,
  rfqStateFromError,
  type RfqViewState,
} from "./api/rfq.ts"
import RfqWorkspace from "./components/RfqWorkspace.tsx"
import QuotationWorkspace from "./components/QuotationWorkspace.tsx"
import OrderWorkspace from "./components/OrderWorkspace.tsx"

const orange = "#ff5a1f"
const products = [
  [
    "MP-5X-001",
    "Chi tiết phay CNC 5 trục",
    "Nhôm 7075",
    "±0,005 mm",
    "Đang sản xuất",
  ],
  [
    "MP-TN-014",
    "Trục truyền động chính xác",
    "Thép SCM440",
    "±0,008 mm",
    "Sẵn sàng",
  ],
  ["MP-EDM-08", "Khuôn cắt dây EDM", "SKD11", "±0,003 mm", "Kiểm định"],
  ["MP-JIG-21", "Đồ gá kiểm tra module pin", "SUS304", "±0,010 mm", "Sẵn sàng"],
]
const customers = [
  ["Samsung SDI Việt Nam", "Điện tử", "12 dự án", "4,8 tỷ ₫", "Đang hoạt động"],
  ["Thaco Industries", "Ô tô", "8 dự án", "3,2 tỷ ₫", "Đang hoạt động"],
  ["Viettel High Tech", "Công nghệ", "5 dự án", "2,1 tỷ ₫", "Tiềm năng"],
  ["Nidec Việt Nam", "Cơ điện", "7 dự án", "1,9 tỷ ₫", "Đang hoạt động"],
]
const news = [
  [
    "ĐẦU TƯ",
    "MecPrecision mở rộng với hai trung tâm gia công 5 trục Mazak Variaxis",
    "Khoản đầu tư 12,4 tỷ đồng giúp nhà máy đáp ứng nhu cầu titan hàng không vũ trụ.",
  ],
  [
    "CHỨNG NHẬN",
    "Đánh giá ISO 9001:2015 không có điểm không phù hợp",
    "Kết quả sạch lần thứ ba liên tiếp khẳng định hệ thống quản lý chất lượng.",
  ],
  [
    "HỢP TÁC",
    "Ký hợp đồng cung ứng linh kiện vỏ pin thế hệ mới",
    "Hợp đồng khung ba năm cho chương trình pin xe điện tại Việt Nam.",
  ],
]

type UnauthenticatedSessionState = {
  status: "unauthenticated"
  message?: string
}

type AuthenticatingSessionState = {
  status: "authenticating"
  message?: string
}

type AuthenticatedSessionState = {
  status: "authenticated"
  user: FoundationUser
  expiresAt: string
  message?: string
}

type SessionState = UnauthenticatedSessionState | AuthenticatingSessionState | AuthenticatedSessionState

type AuthDependencies = {
  authSession: InMemoryAuthSession
  foundationAuth: ReturnType<typeof createFoundationAuthClient>
  canonicalClient: ReturnType<typeof createCanonicalClient>
}

const defaultAuthSession = new InMemoryAuthSession()
const defaultFoundationAuth = createFoundationAuthClient({
  auth: defaultAuthSession,
})
const defaultCanonicalClient = createCanonicalClient({
  baseUrl: canonicalBaseUrlForPhase5b(),
  auth: defaultAuthSession,
})

function loginMessage(error: unknown): string {
  if (error instanceof CanonicalClientError) {
    if (error.kind === "validation") return "Nhập email và mật khẩu."
    if (error.kind === "authentication" || error.kind === "permission") {
      return "Đăng nhập bị từ chối."
    }
    if (error.kind === "timeout") return "Đăng nhập hết thời gian chờ."
    if (error.kind === "network") return "Không thể kết nối máy chủ."
  }
  return "Không thể đăng nhập lúc này."
}

function Logo() {
  return (
    <button
      onClick={() => (location.hash = "")}
      className="flex items-center gap-3 font-semibold tracking-widest"
    >
      <span className="grid h-8 w-8 place-items-center bg-orange-600 text-white">
        M
      </span>
      <span>MECPRECISION</span>
    </button>
  )
}
function Badge({
  children,
  tone = "orange",
}: {
  children: ReactNode
  tone?: string
}) {
  const c =
    tone === "green"
      ? "bg-emerald-500/15 text-emerald-400 border-emerald-500/30"
      : tone === "blue"
        ? "bg-sky-500/15 text-sky-400 border-sky-500/30"
        : "bg-orange-500/15 text-orange-400 border-orange-500/30"
  return (
    <span
      className={
        "inline-flex border px-2 py-1 text-[10px] uppercase tracking-widest " +
        c
      }
    >
      {children}
    </span>
  )
}
function Btn({
  children,
  onClick,
  ghost = false,
  disabled,
  type = "button",
}: {
  children: ReactNode
  onClick?: () => void
  ghost?: boolean
  disabled?: boolean
  type?: "button" | "submit"
}) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      type={type}
      className={
        ghost
          ? "border border-white/20 px-5 py-3 text-xs uppercase tracking-widest hover:border-orange-500 hover:text-orange-400"
          : "bg-orange-600 px-5 py-3 text-xs font-semibold uppercase tracking-widest text-white hover:bg-orange-500 disabled:cursor-not-allowed disabled:opacity-60"
      }
    >
      {children}
    </button>
  )
}
function Field({
  label,
  placeholder,
  type = "text",
  value,
  onChange,
  required,
}: {
  label: string
  placeholder: string
  type?: string
  value?: string
  onChange?: (value: string) => void
  required?: boolean
}) {
  return (
    <label className="grid gap-2">
      <span className="text-[10px] uppercase tracking-[.2em] text-zinc-500">
        {label}
      </span>
      <input
        placeholder={placeholder}
        type={type}
        value={value}
        onChange={(event) => onChange?.(event.currentTarget.value)}
        required={required}
        className="border border-white/10 bg-zinc-950 px-4 py-3 outline-none focus:border-orange-500"
      />
    </label>
  )
}
function Stat({
  label,
  value,
  sub,
}: {
  label: string
  value: string
  sub?: string
}) {
  return (
    <div className="border border-white/10 bg-zinc-900/60 p-5">
      <div className="text-2xl font-semibold text-white">{value}</div>
      <div className="mt-1 text-xs uppercase tracking-widest text-zinc-500">
        {label}
      </div>
      {sub && <div className="mt-3 text-xs text-emerald-400">{sub}</div>}
    </div>
  )
}
function SectionTitle({
  eyebrow,
  title,
  copy,
}: {
  eyebrow: string
  title: string
  copy?: string
}) {
  return (
    <div className="mb-10 grid gap-4 lg:grid-cols-2">
      <div>
        <div className="mb-3 text-xs uppercase tracking-[.28em] text-orange-500">
          — {eyebrow}
        </div>
        <h2 className="font-serif text-4xl leading-tight md:text-6xl">
          {title}
        </h2>
      </div>
      {copy && <p className="self-end text-zinc-400">{copy}</p>}
    </div>
  )
}
type DataTableProps = {
  headers: string[]
  rows: string[][]
}

function DataTable({ headers, rows }: DataTableProps) {
  return (
    <div className="overflow-auto border border-white/10">
      <table className="w-full min-w-[760px] text-left text-sm">
        <thead className="bg-white/[.04] text-[10px] uppercase tracking-widest text-zinc-500">
          <tr>
            {headers.map((h) => (
              <th className="p-4" key={h}>
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr
              className="border-t border-white/10 hover:bg-white/[.03]"
              key={i}
            >
              {r.map((v, j) => (
                <td className="p-4" key={j}>
                  {j === r.length - 1 ? (
                    <Badge
                      tone={
                        v.includes("hoạt") || v.includes("Sẵn")
                          ? "green"
                          : "orange"
                      }
                    >
                      {v}
                    </Badge>
                  ) : (
                    v
                  )}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

const publicNav = [
  ["", "Trang chủ"],
  ["products", "Sản phẩm"],
  ["technology", "Công nghệ"],
  ["news", "Tin tức"],
  ["contact", "Liên hệ"],
]
function PublicHeader({ go }: { go: (v: string) => void }) {
  return (
    <header className="sticky top-0 z-30 border-b border-white/10 bg-[#0b0d0f]/95 backdrop-blur">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-5 py-4">
        <Logo />
        <nav className="hidden gap-7 lg:flex">
          {publicNav.map(([r, l]) => (
            <button
              onClick={() => go(r)}
              className="text-xs uppercase tracking-widest text-zinc-400 hover:text-orange-500"
              key={r}
            >
              {l}
            </button>
          ))}
        </nav>
        <Btn onClick={() => go("contact")}>Yêu cầu báo giá</Btn>
      </div>
    </header>
  )
}
function Footer() {
  return (
    <footer className="border-t border-white/10 px-5 py-10">
      <div className="mx-auto flex max-w-7xl flex-col justify-between gap-6 text-sm text-zinc-500 md:flex-row">
        <Logo />
        <span>KCN Thăng Long, Đông Anh, Hà Nội · +84 24 3827 xxxx</span>
        <span>© 2026 MecPrecision</span>
      </div>
    </footer>
  )
}

function Home({ go }: { go: (v: string) => void }) {
  const capabilityImages = [
    "https://images.unsplash.com/photo-1565043589221-1a6fd9ae45c7?auto=format&fit=crop&w=1000&q=80",
    "https://images.unsplash.com/photo-1581092160607-ee22621dd758?auto=format&fit=crop&w=1000&q=80",
    "https://images.unsplash.com/photo-1581092335397-9583eb92d232?auto=format&fit=crop&w=1000&q=80",
  ]
  return (
    <>
      <section className="relative min-h-[820px] overflow-hidden border-b border-orange-600/40">
        <img
          className="absolute inset-0 h-full w-full object-cover opacity-45"
          src="https://images.unsplash.com/photo-1581092160607-ee22621dd758?auto=format&fit=crop&w=2200&q=88"
        />
        <div className="absolute inset-0 bg-gradient-to-r from-black via-black/80 to-black/20" />
        <div
          className="absolute inset-0 opacity-20"
          style={{
            backgroundImage:
              "linear-gradient(rgba(255,255,255,.12) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.12) 1px,transparent 1px)",
            backgroundSize: "80px 80px",
          }}
        />
        <div className="absolute left-[8%] top-28 h-40 w-px bg-orange-500/50" />
        <div className="relative mx-auto grid min-h-[820px] max-w-7xl items-center gap-12 px-5 lg:grid-cols-[1.3fr_.7fr]">
          <div className="pt-20">
            <div className="mb-6 flex items-center gap-4 text-xs uppercase tracking-[.32em] text-orange-500">
              <span className="h-px w-10 bg-orange-500" /> Gia công chính xác ·
              Hà Nội
            </div>
            <h1 className="font-serif text-6xl leading-[.9] md:text-8xl xl:text-[108px]">
              Nơi kim loại gặp
              <br />
              <em className="text-orange-500">sự chính xác.</em>
            </h1>
            <p className="mt-8 max-w-2xl border-l border-white/20 pl-6 text-lg leading-8 text-zinc-300">
              Đối tác sản xuất linh kiện CNC cho hàng không, ô tô và điện tử —
              từ nguyên mẫu đến hàng triệu chi tiết.
            </p>
            <div className="mt-9 flex flex-wrap gap-3">
              <Btn onClick={() => go("contact")}>
                Tải bản vẽ · Nhận báo giá →
              </Btn>
              <Btn ghost onClick={() => go("products")}>
                Khám phá nhà máy
              </Btn>
            </div>
            <div className="mt-12 flex flex-wrap gap-6 text-[10px] uppercase tracking-[.2em] text-zinc-500">
              <span>ISO 9001:2015</span>
              <span>·</span>
              <span>IATF 16949 Ready</span>
              <span>·</span>
              <span>100% truy xuất nguồn gốc</span>
            </div>
          </div>
          <div className="hidden lg:block">
            <div className="border border-white/15 bg-black/60 p-5 backdrop-blur-xl">
              <div className="flex items-center justify-between border-b border-white/10 pb-4">
                <div>
                  <div className="text-[10px] uppercase tracking-widest text-zinc-500">
                    Trạng thái nhà máy
                  </div>
                  <div className="mt-1 text-sm text-emerald-400">
                    ● Tất cả hệ thống hoạt động
                  </div>
                </div>
                <Badge tone="green">LIVE</Badge>
              </div>
              <div className="mt-5 grid grid-cols-2 gap-3">
                <Stat label="Máy đang chạy" value="28 / 32" />
                <Stat label="OEE hôm nay" value="87,6%" />
                <Stat label="Lệnh sản xuất" value="146" />
                <Stat label="QC pass" value="99,42%" />
              </div>
              <div className="mt-5 border border-white/10 p-4">
                <div className="flex justify-between text-xs">
                  <span>Tiến độ ca 2</span>
                  <span className="text-orange-400">72%</span>
                </div>
                <div className="mt-3 h-1 bg-white/10">
                  <div className="h-full w-[72%] bg-orange-500" />
                </div>
              </div>
              <div className="mt-4 grid grid-cols-3 gap-2 text-center text-[10px] text-zinc-500">
                <span className="border border-white/10 p-2">CNC · 18</span>
                <span className="border border-white/10 p-2">EDM · 06</span>
                <span className="border border-white/10 p-2">CMM · 04</span>
              </div>
            </div>
          </div>
        </div>
        <div className="absolute bottom-5 right-8 hidden items-center gap-3 text-[10px] uppercase tracking-widest text-zinc-500 md:flex">
          <span>Cuộn để khám phá</span>
          <span className="text-orange-500">↓</span>
        </div>
      </section>

      <section className="border-b border-white/10 bg-zinc-950">
        <div className="mx-auto grid max-w-7xl grid-cols-2 md:grid-cols-4">
          {[
            ["18+", "Năm hoạt động", "Từ 2008"],
            ["3.200+", "Dự án hoàn thành", "28 quốc gia"],
            ["240+", "Khách hàng", "91% quay lại"],
            ["±0,005mm", "Dung sai chặt nhất", "CMM verified"],
          ].map((x) => (
            <div
              className="group border-x border-white/10 p-8 hover:bg-orange-600"
              key={x[0]}
            >
              <div className="font-serif text-4xl group-hover:text-black">
                {x[0]}
              </div>
              <div className="mt-2 text-[10px] uppercase tracking-widest text-zinc-500 group-hover:text-black">
                {x[1]}
              </div>
              <div className="mt-5 text-xs text-zinc-700 group-hover:text-black/60">
                {x[2]}
              </div>
            </div>
          ))}
        </div>
      </section>

      <section className="border-b border-white/10 py-10">
        <div className="mx-auto flex max-w-7xl flex-col gap-6 px-5 lg:flex-row lg:items-center">
          <div className="min-w-52 text-[10px] uppercase tracking-[.25em] text-zinc-600">
            Được tin cậy bởi
          </div>
          <div className="grid flex-1 grid-cols-2 gap-px bg-white/10 text-center md:grid-cols-5">
            {["SAMSUNG SDI", "THACO", "VIETTEL", "NIDEC", "PANASONIC"].map(
              (x) => (
                <div
                  className="bg-[#0b0d0f] px-4 py-5 text-xs font-semibold tracking-widest text-zinc-500 hover:text-white"
                  key={x}
                >
                  {x}
                </div>
              ),
            )}
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-5 py-28">
        <SectionTitle
          eyebrow="Năng lực sản xuất"
          title="Từ một bản vẽ đến sản phẩm hoàn chỉnh"
          copy="Một hệ sinh thái gia công khép kín giúp giảm nhà cung cấp trung gian, rút ngắn lead time và kiểm soát chất lượng ở từng micron."
        />
        <div className="grid gap-px bg-white/10 lg:grid-cols-3">
          {["Phay CNC 5 trục", "Tiện CNC kiểu Thụy Sĩ", "Cắt dây EDM"].map(
            (x, i) => (
              <button
                onClick={() => go(i === 0 ? "product" : "products")}
                className="group relative min-h-[440px] overflow-hidden bg-black text-left"
                key={x}
              >
                <img
                  className="absolute inset-0 h-full w-full object-cover opacity-35 transition duration-700 group-hover:scale-105 group-hover:opacity-55"
                  src={capabilityImages[i]}
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black via-black/40 to-transparent" />
                <div className="relative flex h-full min-h-[440px] flex-col justify-between p-7">
                  <div className="flex justify-between">
                    <span className="text-xs text-orange-500">0{i + 1}</span>
                    <Badge>±0,005 mm</Badge>
                  </div>
                  <div>
                    <h3 className="font-serif text-3xl">{x}</h3>
                    <p className="mt-3 max-w-sm text-sm text-zinc-400">
                      Gia công hình học phức tạp, vật liệu hàng không và kiểm
                      tra CMM toàn diện.
                    </p>
                    <div className="mt-5 text-xs uppercase tracking-widest text-orange-500">
                      Xem năng lực →
                    </div>
                  </div>
                </div>
              </button>
            ),
          )}
        </div>
        <div className="grid gap-px bg-white/10 md:grid-cols-3">
          {[
            ["04", "Mài chính xác", "Độ phẳng 0,002 mm"],
            ["05", "Đồ gá & tự động hóa", "Lặp lại ổn định"],
            ["06", "Đo lường CMM", "Truy xuất quốc gia"],
          ].map((x) => (
            <button
              onClick={() => go("products")}
              className="flex items-center justify-between bg-[#0b0d0f] p-6 text-left hover:bg-zinc-900"
              key={x[0]}
            >
              <span className="text-orange-500">{x[0]}</span>
              <span className="flex-1 px-5">
                <b className="block">{x[1]}</b>
                <small className="text-zinc-600">{x[2]}</small>
              </span>
              <span>→</span>
            </button>
          ))}
        </div>
      </section>

      <section className="border-y border-white/10 bg-zinc-900/40 py-28">
        <div className="mx-auto grid max-w-7xl gap-16 px-5 lg:grid-cols-2">
          <div>
            <div className="text-xs uppercase tracking-[.28em] text-orange-500">
              — Công nghệ
            </div>
            <h2 className="mt-5 font-serif text-5xl leading-tight md:text-7xl">
              Nhà máy được thiết kế cho{" "}
              <em className="text-orange-500">sai số bằng không.</em>
            </h2>
            <p className="mt-7 max-w-xl text-zinc-400">
              32 trung tâm gia công, kiểm soát nhiệt 22±1°C và kết nối dữ liệu
              thời gian thực từ máy đến phòng chất lượng.
            </p>
            <div className="mt-10">
              <Btn onClick={() => go("technology")}>Xem công nghệ nhà máy</Btn>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-px bg-white/10">
            {[
              ["18.000", "RPM spindle"],
              ["120", "Tool capacity"],
              ["0,1 μm", "Độ phân giải CMM"],
              ["24/7", "Giám sát sản xuất"],
              ["32", "Máy CNC"],
              ["6", "Máy CMM/vision"],
            ].map((x, i) => (
              <div className="bg-[#101214] p-6" key={i}>
                <div className="font-serif text-3xl">{x[0]}</div>
                <div className="mt-2 text-[10px] uppercase tracking-widest text-zinc-600">
                  {x[1]}
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-5 py-28">
        <SectionTitle
          eyebrow="Quy trình"
          title="Một luồng dữ liệu. Không điểm mù."
          copy="Mọi quyết định kỹ thuật, thông số gia công và kết quả đo đều được lưu cùng hồ sơ chi tiết."
        />
        <div className="relative grid gap-4 md:grid-cols-5">
          {[
            ["01", "Tiếp nhận RFQ", "Trong 2 giờ"],
            ["02", "DFM & báo giá", "Trong 24 giờ"],
            ["03", "FAI & mẫu thử", "3–7 ngày"],
            ["04", "Sản xuất hàng loạt", "Theo takt time"],
            ["05", "QC & giao hàng", "100% truy xuất"],
          ].map((x, i) => (
            <div
              className="relative border border-white/10 p-5 hover:border-orange-500"
              key={x[0]}
            >
              <div className="text-4xl font-light text-white/10">{x[0]}</div>
              <h3 className="mt-8 font-semibold">{x[1]}</h3>
              <p className="mt-2 text-xs text-zinc-600">{x[2]}</p>
              {i < 4 && (
                <span className="absolute -right-3 top-1/2 z-10 hidden h-6 w-6 place-items-center bg-orange-600 text-black md:grid">
                  →
                </span>
              )}
            </div>
          ))}
        </div>
      </section>

      <section className="border-y border-white/10 bg-black py-28">
        <div className="mx-auto max-w-7xl px-5">
          <SectionTitle
            eyebrow="Dự án tiêu biểu"
            title="Độ chính xác tạo nên lợi thế"
            copy="Những chương trình sản xuất đòi hỏi độ ổn định, tốc độ và khả năng mở rộng."
          />
          <div className="grid gap-5 lg:grid-cols-2">
            <div className="group min-h-[520px] border border-white/10 bg-gradient-to-br from-zinc-800 to-black p-8">
              <div className="flex justify-between">
                <Badge>Ô tô điện</Badge>
                <span className="text-xs text-zinc-600">CASE 01</span>
              </div>
              <div className="mt-72 max-w-xl">
                <h3 className="font-serif text-4xl">
                  2,4 triệu vỏ pin nhôm mỗi năm
                </h3>
                <p className="mt-4 text-zinc-500">
                  Giảm cycle time 31% và đạt Cpk 1,67 trên 12 kích thước trọng
                  yếu.
                </p>
              </div>
            </div>
            <div className="grid gap-5">
              <div className="border border-white/10 p-7">
                <Badge>Hàng không</Badge>
                <h3 className="mt-12 font-serif text-3xl">
                  Khung avionics titan Grade 5
                </h3>
                <div className="mt-6 grid grid-cols-3 gap-3">
                  <Stat label="Giảm trọng lượng" value="−28%" />
                  <Stat label="First-pass yield" value="99,1%" />
                  <Stat label="Lead time" value="14 ngày" />
                </div>
              </div>
              <div className="border border-orange-500/30 bg-orange-500/5 p-7">
                <div className="text-5xl text-orange-500">“</div>
                <p className="mt-3 font-serif text-2xl">
                  MecPrecision giúp chúng tôi chuyển từ mẫu thử sang sản xuất ổn
                  định nhanh hơn kế hoạch sáu tuần.
                </p>
                <p className="mt-5 text-xs uppercase tracking-widest text-zinc-500">
                  Giám đốc chuỗi cung ứng · Khách hàng Tier-1
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-5 py-28">
        <SectionTitle
          eyebrow="Tin tức & insight"
          title="Bên trong MecPrecision"
        />
        <div className="grid gap-5 md:grid-cols-3">
          {news.map((n, i) => (
            <button
              onClick={() => go("article")}
              className="group border border-white/10 p-6 text-left hover:border-orange-500"
              key={i}
            >
              <div className="flex justify-between">
                <Badge>{n[0]}</Badge>
                <span className="text-xs text-zinc-700">0{i + 1}</span>
              </div>
              <h3 className="mt-12 font-serif text-2xl group-hover:text-orange-400">
                {n[1]}
              </h3>
              <p className="mt-4 text-sm text-zinc-500">{n[2]}</p>
              <div className="mt-7 text-xs uppercase tracking-widest text-orange-500">
                Đọc bài viết →
              </div>
            </button>
          ))}
        </div>
      </section>
    </>
  )
}

function Products({ go }: { go: (v: string) => void }) {
  return (
    <main className="mx-auto max-w-7xl px-5 py-20">
      <SectionTitle
        eyebrow="Danh mục"
        title="Năng lực & sản phẩm"
        copy="Tìm theo quy trình, vật liệu hoặc độ chính xác yêu cầu."
      />
      <div className="mb-8 flex flex-col gap-3 md:flex-row">
        <input
          className="flex-1 border border-white/10 bg-zinc-950 px-4 py-3"
          placeholder="Tìm sản phẩm, vật liệu, mã…"
        />
        <select className="border border-white/10 bg-zinc-950 px-4">
          <option>Tất cả quy trình</option>
          <option>Phay CNC</option>
          <option>Tiện CNC</option>
        </select>
        <Btn>Lọc kết quả</Btn>
      </div>
      <div className="grid gap-5 md:grid-cols-2">
        {products.map((p, i) => (
          <button
            onClick={() => go("product")}
            className="overflow-hidden border border-white/10 text-left hover:border-orange-500"
            key={p[0]}
          >
            <div className="h-52 bg-gradient-to-br from-zinc-700 to-zinc-950 p-6">
              <Badge>{p[0]}</Badge>
              <div className="mt-16 font-serif text-3xl">{p[1]}</div>
            </div>
            <div className="grid grid-cols-3 gap-4 p-5 text-xs">
              <span>
                <b className="block text-zinc-500">Vật liệu</b>
                {p[2]}
              </span>
              <span>
                <b className="block text-zinc-500">Dung sai</b>
                {p[3]}
              </span>
              <Badge tone="green">{p[4]}</Badge>
            </div>
          </button>
        ))}
      </div>
    </main>
  )
}
function ProductDetail({ go }: { go: (v: string) => void }) {
  return (
    <main>
      <section className="mx-auto grid max-w-7xl gap-10 px-5 py-20 lg:grid-cols-2">
        <div className="min-h-[520px] bg-gradient-to-br from-zinc-700 via-zinc-900 to-black p-8">
          <Badge>MP-5X-001</Badge>
          <div className="mt-72 text-xs uppercase tracking-widest text-zinc-400">
            Ảnh mô phỏng chi tiết gia công
          </div>
        </div>
        <div>
          <div className="text-xs uppercase tracking-widest text-orange-500">
            Phay CNC 5 trục
          </div>
          <h1 className="mt-4 font-serif text-6xl">
            Chi tiết khung nhôm hàng không
          </h1>
          <p className="mt-6 text-zinc-400">
            Gia công đồng thời năm trục từ nhôm 7075-T6, tối ưu độ cứng và giảm
            số lần gá đặt.
          </p>
          <div className="my-8 grid grid-cols-2 gap-3">
            <Stat label="Dung sai" value="±0,005 mm" />
            <Stat label="Độ nhám" value="Ra 0,4 μm" />
            <Stat label="Kích thước tối đa" value="800 × 600 mm" />
            <Stat label="Lead time" value="12–18 ngày" />
          </div>
          <Btn onClick={() => go("contact")}>Gửi bản vẽ nhận báo giá</Btn>
        </div>
      </section>
      <section className="border-y border-white/10 bg-zinc-900/40">
        <div className="mx-auto grid max-w-7xl gap-8 px-5 py-16 md:grid-cols-3">
          {[
            ["Vật liệu", "Nhôm 6061, 7075 · Titan Grade 5 · Inox 304"],
            ["Quy trình", "Phay 5 trục · Taro · Anodizing · Laser marking"],
            ["Kiểm tra", "CMM ZEISS · Báo cáo FAI · Chứng chỉ vật liệu"],
          ].map((x) => (
            <div key={x[0]}>
              <h3 className="text-xs uppercase tracking-widest text-orange-500">
                {x[0]}
              </h3>
              <p className="mt-4 text-zinc-300">{x[1]}</p>
            </div>
          ))}
        </div>
      </section>
    </main>
  )
}
function Technology() {
  return (
    <main className="mx-auto max-w-7xl px-5 py-20">
      <SectionTitle
        eyebrow="Công nghệ"
        title="Được thiết kế đạt tiêu chuẩn khắt khe"
        copy="Hơn 40 trục điều khiển trong môi trường kiểm soát nhiệt độ, hiệu chuẩn theo tiêu chuẩn quốc gia."
      />
      <div className="grid gap-5 lg:grid-cols-2">
        <div className="min-h-[480px] bg-gradient-to-br from-zinc-700 to-black p-8">
          <div className="mt-72 font-serif text-4xl">Mazak Variaxis i-700</div>
          <p className="mt-3 text-zinc-400">
            Gia công 5 trục đồng thời · 18.000 rpm
          </p>
        </div>
        <div className="grid grid-cols-2 gap-4">
          {[
            ["±0,005 mm", "Dung sai"],
            ["0,1 μm", "Độ nhám Ra"],
            ["40+ trục", "Số trục máy"],
            ["120+", "Loại vật liệu"],
            ["ISO 9001", "Chứng nhận"],
            ["98,7%", "Đúng hạn"],
          ].map((x) => (
            <Stat key={x[0]} value={x[0]} label={x[1]} />
          ))}
        </div>
      </div>
      <div className="mt-16 grid gap-px bg-white/10 md:grid-cols-4">
        {[
          "01 Tiếp nhận bản vẽ",
          "02 Phân tích DFM",
          "03 Gia công & kiểm tra",
          "04 Nghiệm thu & giao hàng",
        ].map((x) => (
          <div className="bg-[#0b0d0f] p-6 text-sm" key={x}>
            {x}
          </div>
        ))}
      </div>
    </main>
  )
}
function News({ go }: { go: (v: string) => void }) {
  return (
    <main className="mx-auto max-w-7xl px-5 py-20">
      <SectionTitle eyebrow="Tin tức" title="Cập nhật từ nhà máy" />
      <div className="grid gap-6 lg:grid-cols-3">
        {[...news, ...news].map((n, i) => (
          <button
            onClick={() => go("article")}
            className="border border-white/10 p-6 text-left hover:border-orange-500"
            key={i}
          >
            <Badge>{n[0]}</Badge>
            <div className="mt-5 text-xs text-zinc-600">
              15.08.2026 · 5 phút đọc
            </div>
            <h3 className="mt-4 font-serif text-2xl">{n[1]}</h3>
            <p className="mt-3 text-sm text-zinc-500">{n[2]}</p>
          </button>
        ))}
      </div>
    </main>
  )
}
function Article() {
  return (
    <article className="mx-auto max-w-4xl px-5 py-20">
      <Badge>Đầu tư</Badge>
      <h1 className="mt-7 font-serif text-5xl md:text-7xl">
        MecPrecision mở rộng với hai trung tâm gia công 5 trục
      </h1>
      <p className="mt-6 text-zinc-500">
        15 tháng 8, 2026 · Ban kỹ thuật MecPrecision
      </p>
      <div className="my-12 h-96 bg-gradient-to-br from-zinc-700 to-black" />
      <div className="space-y-6 text-lg leading-8 text-zinc-300">
        <p>
          Khoản đầu tư mới giúp nâng công suất gia công titan và nhôm hàng không
          lên 35%, đồng thời rút ngắn thời gian chuyển đổi giữa các lô sản xuất.
        </p>
        <h2 className="font-serif text-4xl text-white">
          Chất lượng được tích hợp trong quy trình
        </h2>
        <p>
          Mỗi chi tiết đều được đo CMM tại các mốc kiểm soát quan trọng. Dữ liệu
          đo được liên kết trực tiếp với lệnh sản xuất và hồ sơ vật liệu.
        </p>
      </div>
    </article>
  )
}
function Contact() {
  const [sent, setSent] = useState(false)
  return (
    <main className="mx-auto max-w-7xl px-5 py-20">
      <SectionTitle
        eyebrow="Liên hệ"
        title="Hãy cùng tạo ra thứ gì đó thật chính xác."
        copy="Tải bản vẽ hoặc mô tả yêu cầu. Đội kỹ thuật phản hồi báo giá và nhận xét DFM trong một ngày làm việc."
      />
      <div className="grid gap-10 lg:grid-cols-2">
        <div className="space-y-6 text-zinc-400">
          <p>
            <b className="block text-xs uppercase tracking-widest text-orange-500">
              Địa chỉ
            </b>
            KCN Thăng Long, Đông Anh, Hà Nội
          </p>
          <p>
            <b className="block text-xs uppercase tracking-widest text-orange-500">
              Email
            </b>
            baogia@mecprecision.vn
          </p>
          <p>
            <b className="block text-xs uppercase tracking-widest text-orange-500">
              Điện thoại
            </b>
            +84 24 3827 xxxx
          </p>
          <div className="mt-10 h-64 border border-white/10 bg-zinc-900 grid place-items-center text-zinc-600">
            BẢN ĐỒ NHÀ MÁY
          </div>
        </div>
        {sent ? (
          <div className="grid min-h-[480px] place-items-center border border-emerald-500/30 bg-emerald-500/5 p-10 text-center">
            <div>
              <div className="mx-auto grid h-16 w-16 place-items-center rounded-full bg-emerald-500 text-3xl">
                ✓
              </div>
              <h3 className="mt-6 font-serif text-4xl">Đã nhận yêu cầu</h3>
              <p className="mt-3 text-zinc-400">
                Mã yêu cầu RFQ-2026-0821. Kỹ sư sẽ liên hệ trong 24 giờ.
              </p>
            </div>
          </div>
        ) : (
          <form
            onSubmit={(e) => {
              e.preventDefault()
              setSent(true)
            }}
            className="grid gap-5 border border-white/10 bg-zinc-900/40 p-7"
          >
            <Field label="Họ và tên" placeholder="Nguyễn Văn A" />
            <Field label="Email công ty" placeholder="kysu@congty.vn" />
            <Field label="Tên công ty" placeholder="Công ty của bạn" />
            <label className="border border-dashed border-white/20 p-8 text-center text-sm text-zinc-500">
              Kéo thả bản vẽ STEP, PDF, DWG hoặc nhấp để tải lên
            </label>
            <textarea
              className="min-h-28 border border-white/10 bg-zinc-950 p-4"
              placeholder="Số lượng, vật liệu, dung sai…"
            />
            <Btn>Gửi yêu cầu →</Btn>
          </form>
        )}
      </div>
    </main>
  )
}

const adminItems = [
  ["admin", "Tổng quan"],
  ["admin-products", "Sản phẩm"],
  ["admin-customers", "Khách hàng"],
  ["admin-inventory", "Kho hàng"],
  ["admin-orders", "Đơn hàng"],
  ["admin-workflows", "Quy trình"],
  ["admin-transactions", "Giao dịch"],
]
const salesItems = [
  ["sales", "Tổng quan bán hàng"],
  ["sales-leads", "Lead pipeline"],
  ["sales-customers", "Khách hàng CRM"],
  ["sales-quotes", "Báo giá"],
  ["sales-ai", "AI Sales"],
  ["sales-docs", "Tài liệu thông minh"],
]
function SideLayout({
  mode,
  route,
  go,
  children,
}: {
  mode: "admin" | "sales"
  route: string
  go: (v: string) => void
  children: any
}) {
  const items = mode === "admin" ? adminItems : salesItems
  return (
    <div className="min-h-screen bg-[#0b0d0f]">
      <aside className="fixed inset-y-0 left-0 hidden w-64 border-r border-white/10 bg-zinc-950 p-5 lg:block">
        <Logo />
        <div className="mt-10 text-[10px] uppercase tracking-widest text-zinc-600">
          {mode === "admin" ? "Vận hành nhà máy" : "Sales & CRM"}
        </div>
        <nav className="mt-4 grid gap-1">
          {items.map(([r, l]) => (
            <button
              onClick={() => go(r)}
              className={
                "px-4 py-3 text-left text-sm " +
                (route === r
                  ? "bg-orange-600 text-white"
                  : "text-zinc-400 hover:bg-white/5")
              }
              key={r}
            >
              {l}
            </button>
          ))}
        </nav>
        <button
          onClick={() => go("")}
          className="absolute bottom-6 left-5 text-xs text-zinc-500 hover:text-white"
        >
          ← Về website public
        </button>
      </aside>
      <div className="lg:pl-64">
        <header className="flex h-16 items-center justify-between border-b border-white/10 px-5">
          <span className="text-sm text-zinc-500">
            MecPrecision / {mode === "admin" ? "Admin" : "Sales"}
          </span>
          <div className="flex items-center gap-4">
            <button>⌕</button>
            <button>◉</button>
            <Badge tone="green">Hoàng Quốc Quân</Badge>
          </div>
        </header>
        <main className="p-5 md:p-8">{children}</main>
      </div>
    </div>
  )
}
function FoundationLoginForm({
  session,
  onLogin,
}: {
  session: SessionState
  onLogin: (email: string, password: string) => Promise<void>
}) {
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const disabled = session.status === "authenticating"
  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const submittedPassword = password
    setPassword("")
    void onLogin(email, submittedPassword)
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="w-full max-w-md border border-white/10 bg-[#0b0d0f] p-8"
    >
      <Logo />
      <h1 className="mt-12 font-serif text-4xl">Đăng nhập quản trị</h1>
      <div className="mt-8 grid gap-5">
        <Field
          label="Email"
          placeholder="Email đăng nhập"
          type="email"
          value={email}
          onChange={setEmail}
          required
        />
        <Field
          label="Mật khẩu"
          placeholder="Mật khẩu"
          type="password"
          value={password}
          onChange={setPassword}
          required
        />
        {session.message && (
          <p className="text-sm text-orange-400">{session.message}</p>
        )}
        <Btn disabled={disabled} type="submit">
          {disabled ? "Đang đăng nhập" : "Đăng nhập"}
        </Btn>
      </div>
    </form>
  )
}

function AdminPage({
  route,
  go,
  session,
  onLogin,
  onLogout,
}: {
  route: string
  go: (v: string) => void
  session: SessionState
  onLogin: (email: string, password: string) => Promise<void>
  onLogout: () => void
}) {
  if (route === "admin-login")
    return (
      <div className="grid min-h-screen place-items-center bg-zinc-950 p-5">
        <FoundationLoginForm session={session} onLogin={onLogin} />
      </div>
    )
  let title =
    {
      admin: "Tổng quan vận hành",
      "admin-products": "Quản lý sản phẩm",
      "admin-customers": "Khách hàng",
      "admin-inventory": "Tồn kho vật tư",
      "admin-orders": "Đơn hàng sản xuất",
      "admin-workflows": "Quy trình công việc",
      "admin-transactions": "Giao dịch",
    }[route] || "Quản trị"
  return (
    <SideLayout mode="admin" route={route} go={go}>
      <div className="mb-8 flex items-end justify-between">
        <div>
          <div className="text-xs uppercase tracking-widest text-orange-500">
            Vận hành nhà máy
          </div>
          <h1 className="mt-2 font-serif text-4xl">{title}</h1>
        </div>
        {session.status === "authenticated" ? (
          <Btn ghost onClick={onLogout}>
            Đăng xuất
          </Btn>
        ) : (
          <Btn onClick={() => go("admin-login")}>Đăng nhập</Btn>
        )}
      </div>
      {route === "admin" ? (
        <>
          <div className="grid gap-4 md:grid-cols-4">
            <Stat label="Doanh thu tháng" value="8,42 tỷ ₫" sub="↑ 12,4%" />
            <Stat label="Đơn đang chạy" value="38" sub="4 cần chú ý" />
            <Stat label="OEE nhà máy" value="87,6%" sub="↑ 3,1%" />
            <Stat label="Giao đúng hạn" value="98,7%" sub="Mục tiêu 98%" />
          </div>
          <div className="mt-6 grid gap-6 lg:grid-cols-3">
            <div className="col-span-2 border border-white/10 p-6">
              <h3 className="font-semibold">Sản lượng 30 ngày</h3>
              <div className="mt-8 flex h-52 items-end gap-3">
                {[42, 64, 48, 75, 58, 82, 70, 90, 66, 84, 72, 92].map(
                  (h, i) => (
                    <div
                      key={i}
                      className="flex-1 bg-orange-600/70 hover:bg-orange-500"
                      style={{ height: h + "%" }}
                    />
                  ),
                )}
              </div>
            </div>
            <div className="border border-white/10 p-6">
              <h3 className="font-semibold">Cảnh báo</h3>
              {[
                "Vật tư AL7075 dưới định mức",
                "CMM-02 cần hiệu chuẩn",
                "Đơn PO-1048 trễ 2 giờ",
              ].map((x) => (
                <div
                  className="mt-4 border-l-2 border-orange-500 pl-4 text-sm text-zinc-400"
                  key={x}
                >
                  {x}
                </div>
              ))}
            </div>
          </div>
        </>
      ) : route === "admin-products" ? (
        <DataTable
          headers={["Mã", "Tên sản phẩm", "Vật liệu", "Dung sai", "Trạng thái"]}
          rows={products}
        />
      ) : route === "admin-customers" ? (
        <DataTable
          headers={["Khách hàng", "Ngành", "Dự án", "Giá trị", "Trạng thái"]}
          rows={customers}
        />
      ) : route === "admin-inventory" ? (
        <DataTable
          headers={["Mã vật tư", "Mô tả", "Tồn kho", "Đơn vị", "Trạng thái"]}
          rows={[
            ["AL7075-T6", "Nhôm tấm 7075 T6", "128", "kg", "Sắp hết"],
            ["SUS304", "Inox tấm 304", "420", "kg", "Sẵn sàng"],
            ["SCM440", "Thép hợp kim", "86", "kg", "Sắp hết"],
            ["TI-G5", "Titan Grade 5", "42", "kg", "Kiểm định"],
          ]}
        />
      ) : route === "admin-orders" ? (
        <DataTable
          headers={[
            "Đơn hàng",
            "Khách hàng",
            "Tiến độ",
            "Ngày giao",
            "Trạng thái",
          ]}
          rows={[
            [
              "PO-2026-1048",
              "Samsung SDI",
              "72%",
              "05/09/2026",
              "Đang hoạt động",
            ],
            ["PO-2026-1051", "Thaco", "48%", "12/09/2026", "Đang hoạt động"],
            ["PO-2026-1055", "Viettel", "15%", "20/09/2026", "Kiểm định"],
          ]}
        />
      ) : route === "admin-workflows" ? (
        <div className="grid gap-4 md:grid-cols-4">
          {[
            "Chờ xác nhận",
            "Lập trình CAM",
            "Đang gia công",
            "Kiểm tra & giao",
          ].map((x, i) => (
            <div className="border border-white/10 p-4" key={x}>
              <div className="mb-4 flex justify-between">
                <b>{x}</b>
                <Badge>{i + 3}</Badge>
              </div>
              {["PO-1048 · Housing", "PO-1051 · Shaft", "PO-1055 · Jig"]
                .slice(0, i + 1)
                .map((y) => (
                  <div
                    className="mb-3 border border-white/10 bg-zinc-900 p-4 text-sm"
                    key={y}
                  >
                    {y}
                    <div className="mt-3 text-xs text-zinc-500">
                      Ưu tiên cao · Nguyễn Minh
                    </div>
                  </div>
                ))}
            </div>
          ))}
        </div>
      ) : (
        <DataTable
          headers={["Mã", "Ngày", "Loại", "Đối tác", "Giá trị", "Trạng thái"]}
          rows={[
            [
              "TX-8821",
              "31/08/2026",
              "Thu",
              "Samsung SDI",
              "1,2 tỷ ₫",
              "Đã đối soát",
            ],
            [
              "TX-8820",
              "30/08/2026",
              "Chi",
              "Mazak Việt Nam",
              "480 triệu ₫",
              "Đang xử lý",
            ],
            [
              "TX-8819",
              "29/08/2026",
              "Thu",
              "Thaco",
              "820 triệu ₫",
              "Đã đối soát",
            ],
          ]}
        />
      )}
    </SideLayout>
  )
}

function SalesPage({
  route,
  go,
  authenticated,
  canonicalClient,
  rfqState,
  reloadRfqs,
  onAuthenticationFailure,
  role,
}: {
  route: string
  go: (v: string) => void
  authenticated: boolean
  canonicalClient: ReturnType<typeof createCanonicalClient>
  rfqState: RfqViewState
  reloadRfqs: () => void
  onAuthenticationFailure: () => void
  role: string | null
}) {
  const [quoteWorkspace, setQuoteWorkspace] =
    useState<"rfq" | "quotation" | "order">("rfq")
  const title =
    {
      sales: "Tổng quan kinh doanh",
      "sales-leads": "Lead pipeline",
      "sales-customers": "Khách hàng CRM",
      "sales-quotes": "Báo giá",
      "sales-ai": "AI Sales Assistant",
      "sales-docs": "Document Intelligence",
    }[route] || "Sales"
  return (
    <SideLayout mode="sales" route={route} go={go}>
      <div className="mb-8 flex items-end justify-between">
        <div>
          <div className="text-xs uppercase tracking-widest text-orange-500">
            Sales & CRM
          </div>
          <h1 className="mt-2 font-serif text-4xl">{title}</h1>
        </div>
        {route !== "sales-quotes" && <Btn>+ Tạo mới</Btn>}
      </div>
      {route === "sales" ? (
        <>
          <div className="grid gap-4 md:grid-cols-4">
            <Stat label="Pipeline" value="24,8 tỷ ₫" sub="↑ 18%" />
            <Stat label="Lead mới" value="42" sub="Tuần này" />
            <Stat label="Tỷ lệ chốt" value="31,6%" sub="↑ 4,2%" />
            <Stat label="Báo giá chờ" value="12" sub="3 quá hạn" />
          </div>
          <div className="mt-6 border border-white/10 p-6">
            <h3 className="font-semibold">Cơ hội doanh thu theo giai đoạn</h3>
            <div className="mt-8 grid gap-4 md:grid-cols-5">
              {[
                ["Lead", "8,4 tỷ"],
                ["Đủ điều kiện", "6,2 tỷ"],
                ["Báo giá", "4,8 tỷ"],
                ["Đàm phán", "3,1 tỷ"],
                ["Chốt", "2,3 tỷ"],
              ].map((x) => (
                <div
                  className="border-l-2 border-orange-500 bg-white/[.03] p-5"
                  key={x[0]}
                >
                  <div className="text-xs text-zinc-500">{x[0]}</div>
                  <div className="mt-2 text-xl">{x[1]}</div>
                </div>
              ))}
            </div>
          </div>
        </>
      ) : route === "sales-leads" ? (
        <div className="grid gap-4 xl:grid-cols-4">
          {["Lead mới", "Đã xác minh", "Đang báo giá", "Đàm phán"].map(
            (x, i) => (
              <div className="border border-white/10 p-4" key={x}>
                <div className="mb-4 flex justify-between">
                  <b>{x}</b>
                  <Badge>{i + 2}</Badge>
                </div>
                {customers.slice(0, i + 1).map((c, j) => (
                  <div
                    className="mb-3 border border-white/10 bg-zinc-900 p-4"
                    key={j}
                  >
                    <b>{c[0]}</b>
                    <div className="mt-2 text-xs text-zinc-500">
                      Giá trị dự kiến {c[3]}
                    </div>
                    <div className="mt-4 flex justify-between">
                      <Badge tone="blue">Hot lead</Badge>
                      <span className="text-xs">Q.Quân</span>
                    </div>
                  </div>
                ))}
              </div>
            ),
          )}
        </div>
      ) : route === "sales-customers" ? (
        <DataTable
          headers={[
            "Khách hàng",
            "Ngành",
            "Dự án",
            "Giá trị vòng đời",
            "Trạng thái",
          ]}
          rows={customers}
        />
      ) : route === "sales-quotes" ? (
        <div className="grid gap-5">
          <div className="flex flex-wrap gap-3 border-b border-white/10 pb-4">
            <button
              className={
                quoteWorkspace === "rfq"
                  ? "bg-orange-600 px-4 py-2 text-sm"
                  : "border border-white/20 px-4 py-2 text-sm"
              }
              onClick={() => setQuoteWorkspace("rfq")}
            >
              RFQ
            </button>
            <button
              className={
                quoteWorkspace === "quotation"
                  ? "bg-orange-600 px-4 py-2 text-sm"
                  : "border border-white/20 px-4 py-2 text-sm"
              }
              onClick={() => setQuoteWorkspace("quotation")}
            >
              Quotation lifecycle
            </button>
            <button
              className={
                quoteWorkspace === "order"
                  ? "bg-orange-600 px-4 py-2 text-sm"
                  : "border border-white/20 px-4 py-2 text-sm"
              }
              onClick={() => setQuoteWorkspace("order")}
            >
              Order progress & audit
            </button>
          </div>
          <div
            aria-hidden={quoteWorkspace !== "rfq"}
            className={quoteWorkspace === "rfq" ? "block" : "hidden"}
          >
            <RfqWorkspace
              client={canonicalClient}
              authenticated={authenticated}
              rfqState={rfqState}
              reloadRfqs={reloadRfqs}
              goToLogin={() => go("admin-login")}
              onAuthenticationFailure={onAuthenticationFailure}
            />
          </div>
          <div
            aria-hidden={quoteWorkspace !== "quotation"}
            className={quoteWorkspace === "quotation" ? "block" : "hidden"}
          >
            <QuotationWorkspace
              active={quoteWorkspace === "quotation"}
              authenticated={authenticated}
              client={canonicalClient}
              role={role}
              rfqState={rfqState}
              reloadRfqs={reloadRfqs}
              goToLogin={() => go("admin-login")}
              onAuthenticationFailure={onAuthenticationFailure}
            />
          </div>
          <div
            aria-hidden={quoteWorkspace !== "order"}
            className={quoteWorkspace === "order" ? "block" : "hidden"}
          >
            <OrderWorkspace
              active={quoteWorkspace === "order"}
              authenticated={authenticated}
              client={canonicalClient}
              role={role}
              goToLogin={() => go("admin-login")}
              onAuthenticationFailure={onAuthenticationFailure}
            />
          </div>
        </div>
      ) : route === "sales-ai" ? (
        <div className="grid gap-5 lg:grid-cols-[1fr_320px]">
          <div className="border border-white/10 p-6">
            <div className="space-y-4">
              <div className="max-w-xl bg-zinc-900 p-4 text-sm">
                Hôm nay tôi nên ưu tiên cơ hội nào?
              </div>
              <div className="ml-auto max-w-2xl border border-orange-500/30 bg-orange-500/5 p-5">
                <b>3 cơ hội nên xử lý trước</b>
                <ol className="mt-4 list-decimal space-y-3 pl-5 text-sm text-zinc-300">
                  <li>Samsung SDI — báo giá 1,28 tỷ sắp hết hạn sau 18 giờ.</li>
                  <li>Thaco — khách hàng đã mở báo giá 4 lần trong 2 ngày.</li>
                  <li>
                    Viettel — cần bổ sung chứng chỉ vật liệu trước thứ Sáu.
                  </li>
                </ol>
                <div className="mt-5 text-xs text-zinc-500">
                  Nguồn: CRM #882 · Báo giá QT-082 · Lịch sử tương tác
                </div>
              </div>
            </div>
            <div className="mt-8 flex gap-3">
              <input
                className="flex-1 border border-white/10 bg-zinc-950 px-4"
                placeholder="Hỏi AI về pipeline, khách hàng, báo giá…"
              />
              <Btn>Gửi</Btn>
            </div>
          </div>
          <div className="border border-white/10 p-5">
            <h3 className="font-semibold">Hành động đề xuất</h3>
            {[
              "Soạn email theo dõi Samsung",
              "Tạo nhiệm vụ gọi Thaco",
              "Tóm tắt hồ sơ Viettel",
            ].map((x) => (
              <button
                className="mt-3 w-full border border-white/10 p-3 text-left text-sm hover:border-orange-500"
                key={x}
              >
                {x}
              </button>
            ))}
          </div>
        </div>
      ) : (
        <div className="grid gap-5 lg:grid-cols-2">
          <div className="grid min-h-[420px] place-items-center border border-dashed border-white/20 bg-zinc-900/30 p-10 text-center">
            <div>
              <div className="text-5xl">⇧</div>
              <h3 className="mt-5 font-serif text-3xl">
                Tải tài liệu kỹ thuật
              </h3>
              <p className="mt-3 text-zinc-500">
                RFQ, bản vẽ PDF, STEP, Excel hoặc email khách hàng
              </p>
              <div className="mt-6">
                <Btn>Chọn tệp</Btn>
              </div>
            </div>
          </div>
          <div className="border border-white/10 p-6">
            <div className="flex justify-between">
              <h3 className="font-semibold">Kết quả trích xuất</h3>
              <Badge tone="green">96% tin cậy</Badge>
            </div>
            <div className="mt-6 grid gap-4">
              <Field label="Khách hàng" placeholder="Samsung SDI Việt Nam" />
              <Field label="Mã chi tiết" placeholder="BAT-HSG-2048" />
              <Field label="Vật liệu" placeholder="Aluminium 7075-T6" />
              <Field label="Số lượng" placeholder="2.400 pcs" />
              <Btn>Tạo lead & báo giá</Btn>
            </div>
          </div>
        </div>
      )}
    </SideLayout>
  )
}

export default function App({ dependencies }: {
  dependencies?: Partial<AuthDependencies>
} = {}) {
  const [route, setRoute] = useState(location.hash.replace("#/", "") || "")
  const authSession = dependencies?.authSession ?? defaultAuthSession
  const foundationAuth = dependencies?.foundationAuth ?? defaultFoundationAuth
  const canonicalClient =
    dependencies?.canonicalClient ?? defaultCanonicalClient
  const requestGuard = useMemo(() => createLatestRequestGuard(), [])
  const loginGuard = useMemo(() => createLatestRequestGuard(), [])
  const loginAbort = useRef<AbortController | null>(null)
  const rfqAbort = useRef<AbortController | null>(null)
  const [session, setSession] = useState<SessionState>({
    status: authSession.getAccessToken()
      ? "unauthenticated"
      : "unauthenticated",
  })
  const [rfqState, setRfqState] = useState<RfqViewState>({
    status: "unauthenticated",
  })
  const go = (r: string) => {
    setRoute(r)
    location.hash = "/" + r
    scrollTo(0, 0)
  }

  const login = async (email: string, password: string) => {
    loginAbort.current?.abort()
    const controller = new AbortController()
    loginAbort.current = controller
    const requestId = loginGuard.next()
    setSession({ status: "authenticating" })
    try {
      const result = await foundationAuth.login({ email, password }, {
        signal: controller.signal,
      })
      if (!loginGuard.isLatest(requestId)) return
      rfqAbort.current?.abort()
      requestGuard.next()
      setSession({
        status: "authenticated",
        user: result.user,
        expiresAt: result.expires_at,
      })
      setRfqState({ status: "unauthenticated" })
      go("admin")
    } catch (error) {
      if (!loginGuard.isLatest(requestId)) return
      authSession.clear()
      setRfqState({ status: "unauthenticated" })
      setSession({
        status:
          error instanceof CanonicalClientError && error.kind === "validation"
            ? "unauthenticated"
            : "unauthenticated",
        message: loginMessage(error),
      })
    }
  }

  const logout = () => {
    const accessToken = authSession.getAccessToken()
    loginAbort.current?.abort()
    loginGuard.next()
    authSession.clear()
    rfqAbort.current?.abort()
    requestGuard.next()
    setSession({ status: "unauthenticated" })
    setRfqState({ status: "unauthenticated" })
    go("admin-login")
    if (accessToken) void foundationAuth.logout(accessToken)
  }

  const handleRfqAuthenticationFailure = () => {
    authSession.clear()
    rfqAbort.current?.abort()
    requestGuard.next()
    setSession({ status: "unauthenticated" })
    setRfqState({ status: "unauthenticated" })
    go("admin-login")
  }

  const loadRfqs = () => {
    if (!authSession.getAccessToken()) {
      setRfqState({ status: "unauthenticated" })
      return
    }
    rfqAbort.current?.abort()
    const controller = new AbortController()
    rfqAbort.current = controller
    const requestId = requestGuard.next()
    setRfqState({ status: "loading" })
    void fetchRfqPage(canonicalClient, controller.signal)
      .then((page) => {
        if (!requestGuard.isLatest(requestId)) return
        setRfqState(
          page.results.length > 0
            ? { status: "populated", page }
            : { status: "empty", page },
        )
      })
      .catch((error) => {
        if (!requestGuard.isLatest(requestId)) return
        if (error instanceof CanonicalClientError) {
          const nextState = rfqStateFromError(error)
          if (nextState.status === "unauthenticated") {
            authSession.clear()
            setSession({ status: "unauthenticated" })
          }
          setRfqState(nextState)
          return
        }
        setRfqState({ status: "protocol" })
      })
  }

  useEffect(() => {
    if (route === "sales-quotes") loadRfqs()
    return () => {
      loginAbort.current?.abort()
      rfqAbort.current?.abort()
    }
  }, [route])

  if (route.startsWith("admin")) {
    return (
      <AdminPage
        route={route}
        go={go}
        session={session}
        onLogin={login}
        onLogout={logout}
      />
    )
  }
  if (route.startsWith("sales")) {
    return (
      <SalesPage
        route={route}
        go={go}
        authenticated={session.status === "authenticated"}
        canonicalClient={canonicalClient}
        rfqState={rfqState}
        reloadRfqs={loadRfqs}
        onAuthenticationFailure={handleRfqAuthenticationFailure}
        role={session.status === "authenticated" ? session.user.role : null}
      />
    )
  }
  let page =
    route === "products" ? (
      <Products go={go} />
    ) : route === "product" ? (
      <ProductDetail go={go} />
    ) : route === "technology" ? (
      <Technology />
    ) : route === "news" ? (
      <News go={go} />
    ) : route === "article" ? (
      <Article />
    ) : route === "contact" ? (
      <Contact />
    ) : (
      <Home go={go} />
    )
  return (
    <div className="min-h-screen bg-[#0b0d0f] text-zinc-100">
      <PublicHeader go={go} />
      {page}
      <section className="border-t border-white/10 bg-orange-600 px-5 py-14 text-black">
        <div className="mx-auto flex max-w-7xl flex-col items-start justify-between gap-6 md:flex-row md:items-center">
          <h2 className="font-serif text-4xl">
            Sẵn sàng biến bản vẽ thành linh kiện?
          </h2>
          <button
            onClick={() => go("contact")}
            className="bg-black px-6 py-4 text-xs uppercase tracking-widest text-white"
          >
            Bắt đầu dự án →
          </button>
        </div>
      </section>
      <div className="fixed bottom-5 right-5 z-40 flex gap-2">
        <button
          onClick={() => go("admin-login")}
          className="border border-white/10 bg-black px-3 py-2 text-[10px] uppercase tracking-widest text-zinc-500 hover:text-white"
        >
          Admin
        </button>
        <button
          onClick={() => go("sales")}
          className="border border-white/10 bg-black px-3 py-2 text-[10px] uppercase tracking-widest text-zinc-500 hover:text-white"
        >
          CRM
        </button>
      </div>
      <Footer />
    </div>
  )
}
