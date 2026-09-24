import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";

const ADMIN_NAV = [
  { label: "Dashboard", href: "/admin/dashboard", icon: "▦" },
  { label: "Sản Phẩm", href: "/admin/san-pham", icon: "⬡" },
  { label: "Khách Hàng", href: "/admin/khach-hang", icon: "◎" },
  { label: "Kho Hàng", href: "/admin/kho-hang", icon: "▣" },
  { label: "Đơn Hàng", href: "/admin/don-hang", icon: "◈" },
  { label: "Quy Trình", href: "/admin/quy-trinh", icon: "⊞" },
  { label: "Giao Dịch", href: "/admin/giao-dich", icon: "≡" },
];

const SALES_NAV = [
  { label: "Sales Dashboard", href: "/sales/dashboard", icon: "◉" },
  { label: "Leads Kanban", href: "/sales/leads", icon: "⊟" },
  { label: "Báo Giá", href: "/sales/bao-gia", icon: "◇" },
  { label: "AI Assistant", href: "/sales/ai-assistant", icon: "✦" },
  { label: "Tài Liệu AI", href: "/sales/tai-lieu", icon: "⊡" },
];

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const location = useLocation();
  const navigate = useNavigate();
  const [collapsed, setCollapsed] = useState(false);

  const isActive = (href: string) => location.pathname === href || location.pathname.startsWith(href + "/");
  const isSales = location.pathname.startsWith("/sales");

  return (
    <div className="flex h-screen bg-[#0b0d0f] text-[#f5f0e8] overflow-hidden">
      {/* Sidebar */}
      <aside className={`flex flex-col bg-[#131619] border-r border-white/8 transition-all duration-300 ${collapsed ? "w-14" : "w-56"} shrink-0`}>
        {/* Logo */}
        <div className={`h-14 flex items-center border-b border-white/8 ${collapsed ? "justify-center px-2" : "px-4 gap-3"}`}>
          <div className="w-7 h-7 bg-[#ff5500] flex items-center justify-center shrink-0">
            <span className="font-mono font-bold text-white text-[10px]">MP</span>
          </div>
          {!collapsed && (
            <div>
              <p className="font-serif font-bold text-xs leading-tight">MecPrecision</p>
              <p className="font-mono text-[8px] uppercase tracking-widest text-[#ff5500]">Admin</p>
            </div>
          )}
        </div>

        {/* Nav */}
        <nav className="flex-1 py-3 overflow-y-auto scrollbar-hide">
          {/* Admin section */}
          {!collapsed && <p className="font-mono text-[9px] uppercase tracking-widest text-[#f5f0e8]/25 px-4 mb-2 mt-2">Quản Trị</p>}
          {ADMIN_NAV.map((n) => (
            <Link key={n.href} to={n.href} className={`flex items-center gap-3 px-4 py-2.5 transition-colors ${collapsed ? "justify-center" : ""} ${isActive(n.href) ? "bg-[#ff5500]/10 text-[#ff5500] border-r-2 border-[#ff5500]" : "text-[#f5f0e8]/50 hover:text-[#f5f0e8] hover:bg-white/4"}`}>
              <span className="text-sm w-4 text-center shrink-0">{n.icon}</span>
              {!collapsed && <span className="font-mono text-[11px] uppercase tracking-wider">{n.label}</span>}
            </Link>
          ))}

          {/* Sales section */}
          {!collapsed && <p className="font-mono text-[9px] uppercase tracking-widest text-[#f5f0e8]/25 px-4 mb-2 mt-4">Sales / CRM</p>}
          {collapsed && <div className="border-t border-white/8 my-2" />}
          {SALES_NAV.map((n) => (
            <Link key={n.href} to={n.href} className={`flex items-center gap-3 px-4 py-2.5 transition-colors ${collapsed ? "justify-center" : ""} ${isActive(n.href) ? "bg-[#ff5500]/10 text-[#ff5500] border-r-2 border-[#ff5500]" : "text-[#f5f0e8]/50 hover:text-[#f5f0e8] hover:bg-white/4"}`}>
              <span className="text-sm w-4 text-center shrink-0">{n.icon}</span>
              {!collapsed && <span className="font-mono text-[11px] uppercase tracking-wider">{n.label}</span>}
            </Link>
          ))}
        </nav>

        {/* Collapse toggle + logout */}
        <div className="border-t border-white/8 p-3 flex flex-col gap-2">
          <button onClick={() => setCollapsed(!collapsed)} className="flex items-center justify-center text-[#f5f0e8]/30 hover:text-[#f5f0e8] transition-colors text-sm py-1">
            {collapsed ? "▶" : "◀"}
          </button>
          <Link to="/" className={`flex items-center gap-3 py-2 px-2 text-[#f5f0e8]/30 hover:text-[#f5f0e8] transition-colors ${collapsed ? "justify-center" : ""}`}>
            <span className="text-sm">↗</span>
            {!collapsed && <span className="font-mono text-[10px] uppercase tracking-wider">Trang Chủ</span>}
          </Link>
        </div>
      </aside>

      {/* Main area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Topbar */}
        <header className="h-14 bg-[#131619] border-b border-white/8 flex items-center px-6 gap-4 shrink-0">
          <div className="flex-1">
            <p className="font-mono text-[10px] uppercase tracking-widest text-[#f5f0e8]/40">
              {ADMIN_NAV.find(n => isActive(n.href))?.label || SALES_NAV.find(n => isActive(n.href))?.label || "MecPrecision"}
            </p>
          </div>
          <div className="flex items-center gap-3">
            <div className="font-mono text-[10px] text-[#f5f0e8]/40 hidden md:block">
              {new Date().toLocaleDateString("vi-VN", { weekday: "short", year: "numeric", month: "short", day: "numeric" })}
            </div>
            <div className="w-7 h-7 bg-[#ff5500]/20 border border-[#ff5500]/30 flex items-center justify-center">
              <span className="font-mono text-[10px] text-[#ff5500]">NM</span>
            </div>
            <div className="hidden md:block">
              <p className="font-mono text-[10px] text-[#f5f0e8]/70">Nguyễn Minh</p>
              <p className="font-mono text-[9px] text-[#f5f0e8]/30">Quản Trị Viên</p>
            </div>
          </div>
        </header>

        {/* Content */}
        <main className="flex-1 overflow-y-auto bg-[#0b0d0f] p-6">
          {children}
        </main>
      </div>
    </div>
  );
}
