import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ChevronLeft, ChevronRight, FileText, Search, Trash2 } from "lucide-react";
import { useState } from "react";
import { Link } from "react-router-dom";
import { useDebounced } from "../components/TickerPicker";
import { Card, Empty, PageHeader, Skeleton, StanceBadge, StatusBadge } from "../components/ui";
import { api } from "../lib/api";
import { ago } from "../lib/format";

export default function Reports() {
  const qc = useQueryClient();
  const [q, setQ] = useState("");
  const [status, setStatus] = useState("");
  const [page, setPage] = useState(1);
  const dq = useDebounced(q, 300);
  const { data, isLoading } = useQuery({ queryKey: ["jobs", dq, status, page], queryFn: () => api.jobs({ q: dq, status, page, page_size: 12 }), refetchInterval: 5000, placeholderData: (p) => p });
  const del = useMutation({ mutationFn: api.deleteJob, onSuccess: () => { qc.invalidateQueries({ queryKey: ["jobs"] }); qc.invalidateQueries({ queryKey: ["stats"] }); } });
  const pages = data ? Math.max(1, Math.ceil(data.total / data.page_size)) : 1;
  return (
    <div>
      <PageHeader title="Reports" sub={data ? `${data.total} research run${data.total === 1 ? "" : "s"}` : ""} right={<Link to="/new" className="btn-primary">New research</Link>} />
      <div className="mb-5 flex flex-wrap gap-3">
        <div className="relative min-w-60 flex-1">
          <Search size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500" />
          <input className="input !pl-10" placeholder="Search reports…" value={q} onChange={(e) => { setQ(e.target.value); setPage(1); }} />
        </div>
        <select className="input !w-auto" value={status} onChange={(e) => { setStatus(e.target.value); setPage(1); }} aria-label="Status filter">
          <option value="">All statuses</option><option value="completed">Completed</option><option value="running">Running</option><option value="queued">Queued</option><option value="failed">Failed</option>
        </select>
      </div>
      {isLoading ? <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">{Array.from({ length: 6 }).map((_, i) => <Skeleton key={i} className="h-36" />)}</div>
        : data && data.items.length === 0 ? <Card><Empty icon={FileText} title="No reports found" hint="Try a different filter or start a new research run." /></Card>
        : <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {data?.items.map((j) => (
            <Card key={j.id} hover className="group relative flex flex-col">
              <Link to={`/reports/${j.id}`} className="absolute inset-0 z-0 rounded-2xl" aria-label={`Open ${j.title}`} />
              <div className="mb-3 flex items-center justify-between">{j.status === "completed" ? <StanceBadge stance={j.stance} confidence={j.confidence} /> : <StatusBadge status={j.status} />}
                <span className="text-xs text-slate-500">{ago(j.created_at)}</span></div>
              <p className="line-clamp-2 font-semibold text-white">{j.title || j.query}</p>
              <p className="mt-1 line-clamp-2 text-xs text-slate-400">{j.query}</p>
              <div className="mt-auto flex items-center justify-between pt-4">
                <div className="flex flex-wrap gap-1.5">{j.tickers.slice(0, 4).map((t) => <span key={t} className="mono rounded-md bg-brand/15 px-1.5 py-0.5 text-[11px] text-indigo-200">{t}</span>)}</div>
                <button className="relative z-10 rounded-lg p-1.5 text-slate-500 opacity-0 transition hover:bg-down/10 hover:text-down focus:opacity-100 group-hover:opacity-100" aria-label="Delete report"
                  onClick={() => confirm("Delete this report?") && del.mutate(j.id)}><Trash2 size={15} /></button>
              </div>
              {(j.status === "running" || j.status === "queued") && <div className="mt-3 h-1 overflow-hidden rounded bg-white/10"><div className="h-full bg-gradient-to-r from-brand to-cyan transition-all" style={{ width: `${j.progress}%` }} /></div>}
            </Card>
          ))}
        </div>}
      {pages > 1 && (
        <div className="mt-6 flex items-center justify-center gap-3">
          <button className="btn-ghost" disabled={page <= 1} onClick={() => setPage(page - 1)}><ChevronLeft size={16} /></button>
          <span className="text-sm text-slate-400">Page {page} of {pages}</span>
          <button className="btn-ghost" disabled={page >= pages} onClick={() => setPage(page + 1)}><ChevronRight size={16} /></button>
        </div>
      )}
    </div>
  );
}
