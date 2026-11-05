import { useQuery } from "@tanstack/react-query";
import clsx from "clsx";
import { Bot, FileText, LayoutDashboard, Menu, Radar, Settings as Cog, Sparkles, Star, X } from "lucide-react";
import { lazy, Suspense, useState } from "react";
import { NavLink, Route, Routes } from "react-router-dom";
import { api } from "./lib/api";
import Dashboard from "./pages/Dashboard";
import NewResearch from "./pages/NewResearch";
import Reports from "./pages/Reports";
import SettingsPage from "./pages/Settings";
import Watchlist from "./pages/Watchlist";

const ReportView = lazy(() => import("./pages/ReportView"));
const Explorer = lazy(() => import("./pages/Explorer"));

const NAV = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard },
  { to: "/new", label: "New Research", icon: Sparkles },
  { to: "/reports", label: "Reports", icon: FileText },
  { to: "/explore", label: "Market Explorer", icon: Radar },
  { to: "/watchlist", label: "Watchlist", icon: Star },
  { to: "/settings", label: "Settings", icon: Cog },
];

function Sidebar({ onNav }: { onNav?: () => void }) {
  const { data: cfg } = useQuery({ queryKey: ["config"], queryFn: api.config });
  return (
    <div className="flex h-full flex-col p-4">
      <div className="mb-8 flex items-center gap-3 px-2">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-brand to-cyan text-ink-950"><Bot size={22} /></div>
        <div>
          <p className="font-bold leading-tight text-white">Market Researcher</p>
          <p className="text-[11px] uppercase tracking-widest text-slate-400">Agentic desk</p>
        </div>
      </div>
      <nav className="space-y-1">
        {NAV.map(({ to, label, icon: Icon }) => (
          <NavLink key={to} to={to} end={to === "/"} onClick={onNav}
            className={({ isActive }) => clsx("flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-colors",
              isActive ? "bg-brand/20 text-white shadow-[inset_0_0_0_1px_rgba(129,140,248,.35)]" : "text-slate-400 hover:bg-white/5 hover:text-white")}>
            <Icon size={18} /> {label}
          </NavLink>
        ))}
      </nav>
      <div className="mt-auto glass p-3 text-xs">
        <p className="mb-1.5 font-semibold text-slate-200">System</p>
        <p className="flex items-center gap-2 text-slate-400"><span className={clsx("h-2 w-2 rounded-full", cfg?.llm.enabled ? "bg-up" : "bg-warn")} />
          {cfg ? (cfg.llm.enabled ? `LLM: ${cfg.llm.provider}` : "Heuristic engine (no LLM key)") : "Connecting…"}</p>
        <p className="mt-1 text-slate-500">Data: {cfg?.market_data_mode ?? "…"} · {cfg?.max_concurrent_jobs ?? "…"} workers</p>
      </div>
    </div>
  );
}

export default function App() {
  const [open, setOpen] = useState(false);
  return (
    <div className="flex min-h-full">
      <aside className="sticky top-0 hidden h-screen w-64 shrink-0 border-r border-white/5 bg-ink-900/60 backdrop-blur lg:block"><Sidebar /></aside>
      {open && (
        <div className="fixed inset-0 z-40 lg:hidden" onClick={() => setOpen(false)}>
          <div className="absolute inset-0 bg-black/60" />
          <aside className="relative h-full w-64 bg-ink-900" onClick={(e) => e.stopPropagation()}><Sidebar onNav={() => setOpen(false)} /></aside>
        </div>
      )}
      <div className="min-w-0 flex-1">
        <header className="sticky top-0 z-30 flex items-center gap-3 border-b border-white/5 bg-ink-950/70 px-4 py-3 backdrop-blur lg:hidden">
          <button aria-label="Menu" onClick={() => setOpen(!open)} className="btn-ghost">{open ? <X size={18} /> : <Menu size={18} />}</button>
          <span className="font-bold text-white">Market Researcher</span>
        </header>
        <main className="mx-auto max-w-7xl p-4 md:p-8">
          <Suspense fallback={<div className="skeleton h-64" />}>
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/new" element={<NewResearch />} />
              <Route path="/reports" element={<Reports />} />
              <Route path="/reports/:id" element={<ReportView />} />
              <Route path="/explore" element={<Explorer />} />
              <Route path="/explore/:symbol" element={<Explorer />} />
              <Route path="/watchlist" element={<Watchlist />} />
              <Route path="/settings" element={<SettingsPage />} />
              <Route path="*" element={<p className="text-slate-400">Page not found.</p>} />
            </Routes>
          </Suspense>
        </main>
      </div>
    </div>
  );
}
