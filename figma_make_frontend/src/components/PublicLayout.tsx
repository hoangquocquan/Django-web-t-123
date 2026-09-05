import { useState } from "react";
import { Link, useLocation } from "react-router-dom";

const NAV = [
  { label: "Trang Chủ", href: "/" },
  { label: "Sản Phẩm", href: "/san-pham" },
  { label: "Công Nghệ", href: "/cong-nghe" },
  { label: "Tin Tức", href: "/tin-tuc" },
  { label: "Liên Hệ", href: "/lien-he" },
];

export default function PublicLayout({ children }: { children: React.ReactNode }) {
  const location = useLocation();
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <div className="min-h-screen bg-[#0b0d0f] text-[#f5f0e8] flex flex-col">
      {/* Topbar */}
      <header className="fixed top-0 left-0 right-0 z-40 border-b border-white/8 bg-[#0b0d0f]/95 backdrop-blur-md">
        <div className="max-w-[1440px] mx-auto px-6 lg:px-12 flex items-center h-16 gap-8">
          <Link to="/" className="flex items-center gap-3 shrink-0">
            <div className="w-8 h-8 bg-[#ff5500] flex items-center justify-center">
              <span className="font-mono font-bold text-white text-xs">MP</span>
            </div>
            <div>
              <p className="font-serif font-bold text-[#f5f0e8] text-sm leading-tight">MecPrecision</p>
              <p className="font-mono text-[9px] uppercase tracking-widest text-[#ff5500]">Việt Nam</p>
            </div>
          </Link>

          <nav className="hidden md:flex items-center gap-1 ml-auto">
            {NAV.map((n) => (
              <Link
                key={n.href}
                to={n.href}
                className={`px-4 py-2 font-mono text-[10px] uppercase tracking-widest transition-colors ${location.pathname === n.href || (n.href !== "/" && location.pathname.startsWith(n.href)) ? "text-[#ff5500]" : "text-[#f5f0e8]/60 hover:text-[#f5f0e8]"}`}
              >
                {n.label}
              </Link>
            ))}
            <Link to="/lien-he" className="ml-4 px-5 py-2 bg-[#ff5500] text-white font-mono text-[10px] uppercase tracking-widest hover:bg-[#ff6a1f] transition-colors">
              Yêu Cầu Báo Giá
            </Link>
          </nav>

          <button className="md:hidden ml-auto text-[#f5f0e8]/60 hover:text-[#f5f0e8]" onClick={() => setMenuOpen(!menuOpen)}>
            ☰
          </button>
        </div>

        {menuOpen && (
          <div className="md:hidden border-t border-white/8 bg-[#131619] px-6 py-4 flex flex-col gap-3">
            {NAV.map((n) => (
              <Link key={n.href} to={n.href} className="font-mono text-xs uppercase tracking-widest text-[#f5f0e8]/70 hover:text-[#ff5500]" onClick={() => setMenuOpen(false)}>
                {n.label}
              </Link>
            ))}
          </div>
        )}
      </header>

      <main className="flex-1 pt-16">{children}</main>

      {/* Footer */}
      <footer className="border-t border-white/8 bg-[#0b0d0f] mt-20">
        <div className="max-w-[1440px] mx-auto px-6 lg:px-12 py-12 grid grid-cols-2 md:grid-cols-4 gap-8">
          <div className="col-span-2 md:col-span-1">
            <div className="flex items-center gap-2 mb-4">
              <div className="w-7 h-7 bg-[#ff5500] flex items-center justify-center">
                <span className="font-mono font-bold text-white text-[10px]">MP</span>
              </div>
              <span className="font-serif font-bold text-sm">MecPrecision Việt Nam</span>
            </div>
            <p className="text-[#f5f0e8]/45 text-xs leading-relaxed">Gia công CNC chính xác cao — ISO 9001:2015 & AS9100D. Hơn 15 năm tin cậy trong ngành.</p>
          </div>
          <div>
            <p className="font-mono text-[10px] uppercase tracking-widest text-[#ff5500] mb-3">Dịch Vụ</p>
            {["Phay CNC 5 Trục", "Tiện CNC", "Mài Chính Xác", "EDM Wire Cut", "CMM Kiểm Tra"].map((s) => (
              <p key={s} className="text-[#f5f0e8]/45 text-xs mb-1.5 hover:text-[#f5f0e8] cursor-pointer transition-colors">{s}</p>
            ))}
          </div>
          <div>
            <p className="font-mono text-[10px] uppercase tracking-widest text-[#ff5500] mb-3">Công Ty</p>
            {NAV.map((n) => (
              <Link key={n.href} to={n.href} className="block text-[#f5f0e8]/45 text-xs mb-1.5 hover:text-[#f5f0e8] transition-colors">{n.label}</Link>
            ))}
          </div>
          <div>
            <p className="font-mono text-[10px] uppercase tracking-widest text-[#ff5500] mb-3">Liên Hệ</p>
            <p className="text-[#f5f0e8]/45 text-xs mb-1.5">Khu CNC – Lô C-15</p>
            <p className="text-[#f5f0e8]/45 text-xs mb-1.5">Khu Công Nghệ Cao, TP.HCM</p>
            <p className="text-[#f5f0e8]/45 text-xs mb-1.5">+84 28 3742 5500</p>
            <p className="text-[#f5f0e8]/45 text-xs">info@mecprecision.vn</p>
          </div>
        </div>
        <div className="border-t border-white/5 px-6 lg:px-12 py-4 max-w-[1440px] mx-auto flex items-center justify-between">
          <p className="font-mono text-[10px] text-[#f5f0e8]/25">© 2026 MecPrecision Việt Nam. Bảo lưu mọi quyền.</p>
          <p className="font-mono text-[10px] text-[#f5f0e8]/25">ISO 9001:2015 · AS9100D</p>
        </div>
      </footer>
    </div>
  );
}
