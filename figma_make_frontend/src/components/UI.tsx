import React, { useState, useEffect, useRef } from "react";

// ── Button ────────────────────────────────────────────────────────────────────
type BtnVariant = "primary" | "secondary" | "ghost" | "danger" | "outline";
interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: BtnVariant;
  size?: "sm" | "md" | "lg";
  loading?: boolean;
  icon?: React.ReactNode;
}

export function Button({ variant = "primary", size = "md", loading, icon, children, className = "", disabled, ...props }: ButtonProps) {
  const base = "inline-flex items-center gap-2 font-mono uppercase tracking-widest text-xs font-medium transition-all duration-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-orange-500 disabled:opacity-40 disabled:cursor-not-allowed";
  const variants: Record<BtnVariant, string> = {
    primary: "bg-[#ff5500] text-white hover:bg-[#ff6a1f] active:scale-[0.98]",
    secondary: "bg-[#222830] text-[#f5f0e8] border border-white/10 hover:bg-[#2a3040] hover:border-white/20",
    ghost: "text-[#f5f0e8]/70 hover:text-[#f5f0e8] hover:bg-white/5",
    danger: "bg-red-600 text-white hover:bg-red-500",
    outline: "border border-[#ff5500] text-[#ff5500] hover:bg-[#ff5500]/10",
  };
  const sizes = { sm: "px-3 py-1.5 text-[10px]", md: "px-5 py-2.5", lg: "px-7 py-3.5 text-sm" };
  return (
    <button className={`${base} ${variants[variant]} ${sizes[size]} ${className}`} disabled={disabled || loading} {...props}>
      {loading ? <Spinner size="sm" /> : icon}
      {children}
    </button>
  );
}

// ── Badge ─────────────────────────────────────────────────────────────────────
type BadgeColor = "orange" | "green" | "red" | "yellow" | "blue" | "gray";
export function Badge({ color = "gray", children }: { color?: BadgeColor; children: React.ReactNode }) {
  const colors: Record<BadgeColor, string> = {
    orange: "bg-[#ff5500]/15 text-[#ff5500] border-[#ff5500]/30",
    green: "bg-green-500/10 text-green-400 border-green-500/30",
    red: "bg-red-500/10 text-red-400 border-red-500/30",
    yellow: "bg-yellow-500/10 text-yellow-400 border-yellow-500/30",
    blue: "bg-blue-500/10 text-blue-400 border-blue-500/30",
    gray: "bg-white/5 text-[#f5f0e8]/60 border-white/10",
  };
  return <span className={`inline-flex items-center px-2 py-0.5 text-[10px] font-mono uppercase tracking-wider border ${colors[color]}`}>{children}</span>;
}

// ── Spinner ───────────────────────────────────────────────────────────────────
export function Spinner({ size = "md" }: { size?: "sm" | "md" | "lg" }) {
  const s = { sm: "w-3 h-3", md: "w-5 h-5", lg: "w-8 h-8" };
  return <div className={`${s[size]} border-2 border-white/20 border-t-[#ff5500] rounded-full animate-spin`} />;
}

// ── Loading / Empty / Error states ────────────────────────────────────────────
export function LoadingState({ text = "Đang tải..." }: { text?: string }) {
  return (
    <div className="flex flex-col items-center justify-center gap-4 py-20">
      <Spinner size="lg" />
      <p className="font-mono text-xs uppercase tracking-widest text-[#f5f0e8]/40">{text}</p>
    </div>
  );
}

export function EmptyState({ icon, title, description, action }: { icon?: React.ReactNode; title: string; description?: string; action?: React.ReactNode }) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-20 text-center">
      {icon && <div className="text-4xl text-[#f5f0e8]/20 mb-2">{icon}</div>}
      <p className="font-mono text-xs uppercase tracking-widest text-[#f5f0e8]/40">{title}</p>
      {description && <p className="text-sm text-[#f5f0e8]/30 max-w-xs">{description}</p>}
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}

export function ErrorState({ message = "Có lỗi xảy ra. Vui lòng thử lại." }: { message?: string }) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-20">
      <div className="text-4xl">⚠</div>
      <p className="font-mono text-xs uppercase tracking-widest text-red-400">Lỗi</p>
      <p className="text-sm text-[#f5f0e8]/50">{message}</p>
    </div>
  );
}

// ── Card ──────────────────────────────────────────────────────────────────────
export function Card({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return <div className={`bg-[#1a1e22] border border-white/8 ${className}`}>{children}</div>;
}

// ── Table ─────────────────────────────────────────────────────────────────────
export function Table({ headers, rows, onRowClick }: { headers: string[]; rows: React.ReactNode[][]; onRowClick?: (i: number) => void }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm border-collapse">
        <thead>
          <tr className="border-b border-white/8">
            {headers.map((h) => (
              <th key={h} className="text-left px-4 py-3 font-mono text-[10px] uppercase tracking-widest text-[#f5f0e8]/40">{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i} onClick={() => onRowClick?.(i)} className={`border-b border-white/5 transition-colors ${onRowClick ? "cursor-pointer hover:bg-white/3" : ""}`}>
              {row.map((cell, j) => (
                <td key={j} className="px-4 py-3 text-[#f5f0e8]/80">{cell}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ── Pagination ────────────────────────────────────────────────────────────────
export function Pagination({ page, total, perPage, onChange }: { page: number; total: number; perPage: number; onChange: (p: number) => void }) {
  const pages = Math.ceil(total / perPage);
  return (
    <div className="flex items-center gap-2 px-4 py-3 border-t border-white/8">
      <span className="font-mono text-[10px] text-[#f5f0e8]/40 uppercase tracking-wider mr-auto">
        {(page - 1) * perPage + 1}–{Math.min(page * perPage, total)} / {total}
      </span>
      {Array.from({ length: pages }, (_, i) => (
        <button key={i} onClick={() => onChange(i + 1)} className={`w-7 h-7 font-mono text-xs transition-colors ${page === i + 1 ? "bg-[#ff5500] text-white" : "text-[#f5f0e8]/40 hover:text-[#f5f0e8]"}`}>
          {i + 1}
        </button>
      ))}
    </div>
  );
}

// ── Input ─────────────────────────────────────────────────────────────────────
export function Input({ label, error, icon, ...props }: React.InputHTMLAttributes<HTMLInputElement> & { label?: string; error?: string; icon?: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-1.5">
      {label && <label className="font-mono text-[10px] uppercase tracking-widest text-[#f5f0e8]/50">{label}</label>}
      <div className="relative">
        {icon && <span className="absolute left-3 top-1/2 -translate-y-1/2 text-[#f5f0e8]/30">{icon}</span>}
        <input className={`w-full bg-[#131619] border border-white/10 text-[#f5f0e8] text-sm px-3 py-2.5 focus:outline-none focus:border-[#ff5500]/60 transition-colors placeholder:text-[#f5f0e8]/20 ${icon ? "pl-9" : ""} ${error ? "border-red-500/50" : ""}`} {...props} />
      </div>
      {error && <p className="text-red-400 text-xs">{error}</p>}
    </div>
  );
}

export function Select({ label, children, ...props }: React.SelectHTMLAttributes<HTMLSelectElement> & { label?: string }) {
  return (
    <div className="flex flex-col gap-1.5">
      {label && <label className="font-mono text-[10px] uppercase tracking-widest text-[#f5f0e8]/50">{label}</label>}
      <select className="w-full bg-[#131619] border border-white/10 text-[#f5f0e8] text-sm px-3 py-2.5 focus:outline-none focus:border-[#ff5500]/60 transition-colors" {...props}>
        {children}
      </select>
    </div>
  );
}

export function Textarea({ label, ...props }: React.TextareaHTMLAttributes<HTMLTextAreaElement> & { label?: string }) {
  return (
    <div className="flex flex-col gap-1.5">
      {label && <label className="font-mono text-[10px] uppercase tracking-widest text-[#f5f0e8]/50">{label}</label>}
      <textarea className="w-full bg-[#131619] border border-white/10 text-[#f5f0e8] text-sm px-3 py-2.5 focus:outline-none focus:border-[#ff5500]/60 transition-colors placeholder:text-[#f5f0e8]/20 resize-none" rows={4} {...props} />
    </div>
  );
}

// ── Dialog / Modal ────────────────────────────────────────────────────────────
export function Dialog({ open, onClose, title, children, wide }: { open: boolean; onClose: () => void; title: string; children: React.ReactNode; wide?: boolean }) {
  useEffect(() => {
    const handler = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [onClose]);

  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 animate-fade-in">
      <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" onClick={onClose} />
      <div className={`relative bg-[#1a1e22] border border-white/10 shadow-2xl ${wide ? "max-w-3xl" : "max-w-lg"} w-full max-h-[90vh] overflow-y-auto`}>
        <div className="flex items-center justify-between px-6 py-4 border-b border-white/8">
          <h3 className="font-mono text-xs uppercase tracking-widest text-[#f5f0e8]/70">{title}</h3>
          <button onClick={onClose} className="text-[#f5f0e8]/40 hover:text-[#f5f0e8] transition-colors text-lg">×</button>
        </div>
        <div className="px-6 py-5">{children}</div>
      </div>
    </div>
  );
}

// ── Drawer ────────────────────────────────────────────────────────────────────
export function Drawer({ open, onClose, title, children }: { open: boolean; onClose: () => void; title: string; children: React.ReactNode }) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex justify-end">
      <div className="absolute inset-0 bg-black/60" onClick={onClose} />
      <div className="relative bg-[#1a1e22] border-l border-white/10 w-full max-w-md h-full overflow-y-auto animate-slide-in flex flex-col">
        <div className="flex items-center justify-between px-6 py-4 border-b border-white/8">
          <h3 className="font-mono text-xs uppercase tracking-widest text-[#f5f0e8]/70">{title}</h3>
          <button onClick={onClose} className="text-[#f5f0e8]/40 hover:text-[#f5f0e8] text-lg">×</button>
        </div>
        <div className="flex-1 px-6 py-5">{children}</div>
      </div>
    </div>
  );
}

// ── Toast ─────────────────────────────────────────────────────────────────────
interface ToastMsg { id: number; message: string; type: "success" | "error" | "info"; }
let toastListeners: ((t: ToastMsg) => void)[] = [];
export function showToast(message: string, type: "success" | "error" | "info" = "success") {
  toastListeners.forEach((fn) => fn({ id: Date.now(), message, type }));
}

export function ToastProvider() {
  const [toasts, setToasts] = useState<ToastMsg[]>([]);
  useEffect(() => {
    const handler = (t: ToastMsg) => {
      setToasts((prev) => [...prev, t]);
      setTimeout(() => setToasts((prev) => prev.filter((x) => x.id !== t.id)), 3500);
    };
    toastListeners.push(handler);
    return () => { toastListeners = toastListeners.filter((f) => f !== handler); };
  }, []);

  const colors = { success: "border-green-500/50 text-green-400", error: "border-red-500/50 text-red-400", info: "border-[#ff5500]/50 text-[#ff5500]" };
  return (
    <div className="fixed bottom-6 right-6 z-[100] flex flex-col gap-2">
      {toasts.map((t) => (
        <div key={t.id} className={`bg-[#1a1e22] border ${colors[t.type]} px-4 py-3 font-mono text-xs shadow-xl animate-fade-in max-w-xs`}>
          {t.message}
        </div>
      ))}
    </div>
  );
}

// ── Stat Card ─────────────────────────────────────────────────────────────────
export function StatCard({ label, value, delta, color }: { label: string; value: string; delta?: string; color?: string }) {
  return (
    <div className="bg-[#1a1e22] border border-white/8 p-5">
      <p className="font-mono text-[10px] uppercase tracking-widest text-[#f5f0e8]/40 mb-3">{label}</p>
      <p className={`text-2xl font-serif font-bold ${color || "text-[#f5f0e8]"}`}>{value}</p>
      {delta && <p className="font-mono text-[10px] text-green-400 mt-1">{delta}</p>}
    </div>
  );
}

// ── Progress Bar ──────────────────────────────────────────────────────────────
export function ProgressBar({ value, color = "#ff5500" }: { value: number; color?: string }) {
  return (
    <div className="h-1.5 bg-white/10 w-full overflow-hidden">
      <div className="h-full transition-all duration-500" style={{ width: `${value}%`, background: color }} />
    </div>
  );
}

// ── Section Label ─────────────────────────────────────────────────────────────
export function SectionLabel({ children }: { children: React.ReactNode }) {
  return <p className="font-mono text-[10px] uppercase tracking-widest text-[#ff5500]">{children}</p>;
}

// ── Divider ───────────────────────────────────────────────────────────────────
export function Divider() {
  return <div className="border-t border-white/8 my-6" />;
}
