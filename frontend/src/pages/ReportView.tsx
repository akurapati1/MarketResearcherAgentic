import { useQuery, useQueryClient } from "@tanstack/react-query";
import clsx from "clsx";
import { AlertTriangle, ArrowLeft, Download, ExternalLink, FileJson, Newspaper, Printer, RefreshCw, ShieldAlert, Target, TrendingDown, TrendingUp } from "lucide-react";
import { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import { Link, useNavigate, useParams } from "react-router-dom";
import remarkGfm from "remark-gfm";
import { AgentTimeline } from "../components/AgentTimeline";
import { PriceChart } from "../components/PriceChart";
import { Card, DemoBadge, Gauge, PageHeader, SectionTitle, Skeleton, StanceBadge, StatusBadge } from "../components/ui";
import { api, apiKey, download, type Instrument, type JobEvent, type Report } from "../lib/api";
import { money, num, pct, pctRaw, tone } from "../lib/format";

function useJobStream(id: string, active: boolean) {
  const [events, setEvents] = useState<JobEvent[]>([]);
  const qc = useQueryClient();
  useEffect(() => {
    if (!active) return;
    const k = apiKey.get();
    const es = new EventSource(`/api/research/${id}/stream${k ? `?api_key=${encodeURIComponent(k)}` : ""}`);
    const onEvent = (e: MessageEvent) => {
      const ev = JSON.parse(e.data) as JobEvent;
      setEvents((prev) => (prev.some((p) => p.id === ev.id) ? prev : [...prev, ev]));
      qc.invalidateQueries({ queryKey: ["job", id] });
    };
    ["log", "step", "done", "error"].forEach((t) => es.addEventListener(t, onEvent as EventListener));
    es.addEventListener("end", () => { es.close(); qc.invalidateQueries({ queryKey: ["job", id] }); qc.invalidateQueries({ queryKey: ["stats"] }); });
    return () => es.close();
  }, [id, active, qc]);
  return events;
}

const Metric = ({ label, value, cls }: { label: string; value: string; cls?: string }) => (
  <div className="rounded-xl bg-white/[.03] p-3"><p className="text-[11px] uppercase tracking-wider text-slate-500">{label}</p><p className={clsx("mt-1 text-lg font-semibold", cls ?? "text-white")}>{value}</p></div>
);

function InstrumentPanel({ ins }: { ins: Instrument }) {
  const i = ins.indicators, q = ins.quote;
  const range = i.high_52w - i.low_52w || 1;
  const pos = Math.max(0, Math.min(100, ((q.price - i.low_52w) / range) * 100));
  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="flex items-center gap-2 text-xl font-bold text-white">{ins.name} <span className="mono text-sm font-medium text-slate-400">{ins.symbol}</span> <DemoBadge source={q.source} /></p>
          <p className="mt-1 text-3xl font-bold text-white">{money(q.price, q.currency)} <span className={clsx("ml-2 text-base font-semibold", tone(q.change_pct))}>{pctRaw(q.change_pct)}</span></p>
        </div>
        <StanceBadge stance={ins.stance} />
      </div>
      <PriceChart data={ins.series} height={300} />
      <div className="flex gap-4 text-xs text-slate-400"><span><i className="mr-1 inline-block h-0.5 w-4 bg-cyan align-middle" />SMA 20</span><span><i className="mr-1 inline-block h-0.5 w-4 bg-warn align-middle" />SMA 50</span></div>
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <Metric label="1M return" value={pct(i.return_1m)} cls={tone(i.return_1m)} />
        <Metric label="3M return" value={pct(i.return_3m)} cls={tone(i.return_3m)} />
        <Metric label="1Y return" value={pct(i.return_1y)} cls={tone(i.return_1y)} />
        <Metric label="RSI (14)" value={num(i.rsi14, 0)} cls={i.rsi14 == null ? undefined : i.rsi14 > 70 ? "text-down" : i.rsi14 < 30 ? "text-up" : "text-white"} />
        <Metric label="Volatility" value={i.volatility != null ? `${(i.volatility * 100).toFixed(0)}%` : "—"} />
        <Metric label="Max drawdown" value={pct(i.max_drawdown, 0)} cls="text-down" />
        <Metric label="Trend" value={i.trend} cls={i.trend === "uptrend" ? "text-up" : i.trend === "downtrend" ? "text-down" : "text-warn"} />
        <Metric label="MACD hist." value={i.macd ? num(i.macd.histogram) : "—"} cls={tone(i.macd?.histogram)} />
      </div>
      <div>
        <div className="mb-1 flex justify-between text-xs text-slate-400"><span>52w low {num(i.low_52w)}</span><span>52w high {num(i.high_52w)}</span></div>
        <div className="relative h-2 rounded-full bg-gradient-to-r from-down/40 via-warn/40 to-up/40"><span className="absolute top-1/2 h-4 w-4 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-ink-900 bg-white" style={{ left: `${pos}%` }} /></div>
      </div>
    </div>
  );
}

const SWOT = [
  { k: "strengths", label: "Strengths", c: "text-up", bg: "bg-up/5 border-up/20" },
  { k: "weaknesses", label: "Weaknesses", c: "text-down", bg: "bg-down/5 border-down/20" },
  { k: "opportunities", label: "Opportunities", c: "text-cyan", bg: "bg-cyan/5 border-cyan/20" },
  { k: "threats", label: "Threats", c: "text-warn", bg: "bg-warn/5 border-warn/20" },
] as const;

function ReportBody({ r }: { r: Report }) {
  const [tab, setTab] = useState(0);
  const avg = r.instruments.length ? r.instruments.reduce((a, b) => a + b.score, 0) / r.instruments.length : r.sentiment.score;
  const rec = r.recommendation;
  return (
    <div className="space-y-6">
      {r.data_quality === "synthetic" && (
        <div className="flex items-start gap-3 rounded-xl border border-warn/30 bg-warn/10 p-4 text-sm text-warn">
          <AlertTriangle size={18} className="mt-0.5 shrink-0" />
          <p><b>Demo data.</b> The live market feed was unreachable, so prices are deterministic simulated series. Do not use this report for real decisions.</p>
        </div>
      )}
      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <SectionTitle icon={Target}>Executive summary</SectionTitle>
          <p className="leading-relaxed text-slate-200">{r.executive_summary}</p>
          <ul className="mt-4 space-y-2">{r.key_findings.map((f, i) => <li key={i} className="flex gap-2 text-sm text-slate-300"><span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-cyan" />{f}</li>)}</ul>
        </Card>
        <Card className="flex flex-col items-center justify-center text-center">
          <p className="mb-2 text-xs uppercase tracking-wider text-slate-400">Agent verdict</p>
          <Gauge value={avg} label={rec.stance} />
          <div className="mt-2 w-full"><div className="mb-1 flex justify-between text-xs text-slate-400"><span>Confidence</span><span>{rec.confidence}%</span></div>
            <div className="h-1.5 overflow-hidden rounded bg-white/10"><div className="h-full bg-gradient-to-r from-brand to-cyan" style={{ width: `${rec.confidence}%` }} /></div></div>
          <p className="mt-3 text-xs text-slate-400">Horizon: {rec.horizon}</p>
          <p className="mt-2 text-xs leading-relaxed text-slate-400">{rec.rationale}</p>
        </Card>
      </div>

      {r.instruments.length > 0 && (
        <Card>
          <div className="mb-4 flex flex-wrap gap-2">
            {r.instruments.map((ins, i) => <button key={ins.symbol} onClick={() => setTab(i)} className={clsx("mono rounded-lg border px-3 py-1.5 text-sm font-medium transition", tab === i ? "border-brand bg-brand/20 text-white" : "border-white/10 text-slate-400 hover:text-white")}>{ins.symbol}</button>)}
          </div>
          <InstrumentPanel ins={r.instruments[tab]} />
        </Card>
      )}

      {r.instruments.length > 1 && (
        <Card>
          <SectionTitle>Head-to-head</SectionTitle>
          <div className="overflow-x-auto"><table className="w-full min-w-[640px] text-sm">
            <thead><tr className="text-left text-xs uppercase tracking-wider text-slate-500"><th className="pb-2">Symbol</th><th>Price</th><th>3M</th><th>1Y</th><th>RSI</th><th>Vol.</th><th>Max DD</th><th>Score</th><th>Stance</th></tr></thead>
            <tbody>{r.instruments.map((x) => (
              <tr key={x.symbol} className="border-t border-white/5">
                <td className="mono py-2.5 font-semibold text-white">{x.symbol}</td><td>{money(x.quote.price, x.quote.currency)}</td>
                <td className={tone(x.indicators.return_3m)}>{pct(x.indicators.return_3m)}</td><td className={tone(x.indicators.return_1y)}>{pct(x.indicators.return_1y)}</td>
                <td>{num(x.indicators.rsi14, 0)}</td><td>{x.indicators.volatility != null ? `${(x.indicators.volatility * 100).toFixed(0)}%` : "—"}</td>
                <td className="text-down">{pct(x.indicators.max_drawdown, 0)}</td><td className={tone(x.score)}>{x.score.toFixed(2)}</td><td><StanceBadge stance={x.stance} /></td>
              </tr>))}</tbody></table></div>
        </Card>
      )}

      <div className="grid gap-4 md:grid-cols-2">
        {SWOT.map((s) => (
          <div key={s.k} className={clsx("rounded-2xl border p-5", s.bg)}>
            <p className={clsx("mb-3 flex items-center gap-2 text-sm font-semibold uppercase tracking-wider", s.c)}>{s.k === "strengths" || s.k === "opportunities" ? <TrendingUp size={16} /> : <TrendingDown size={16} />}{s.label}</p>
            <ul className="space-y-1.5 text-sm text-slate-300">{r.swot[s.k].map((t, i) => <li key={i}>• {t}</li>)}</ul>
          </div>
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <SectionTitle icon={ShieldAlert}>Risk register</SectionTitle>
          <ul className="space-y-3">{r.risks.map((k, i) => (
            <li key={i} className="flex gap-3"><span className={clsx("mt-0.5 h-fit rounded-md px-2 py-0.5 text-[10px] font-bold uppercase", k.severity === "high" ? "bg-down/20 text-down" : k.severity === "medium" ? "bg-warn/20 text-warn" : "bg-up/20 text-up")}>{k.severity}</span>
              <div><p className="text-sm font-medium text-white">{k.title}</p><p className="text-xs text-slate-400">{k.detail}</p></div></li>))}</ul>
        </Card>
        <Card>
          <SectionTitle icon={Newspaper} right={<span className="text-xs text-slate-400">Tone: <b className={r.sentiment.score > 0.15 ? "text-up" : r.sentiment.score < -0.15 ? "text-down" : "text-warn"}>{r.sentiment.label}</b></span>}>News & sentiment</SectionTitle>
          {r.sentiment.count > 0 && <div className="mb-4 flex h-2 overflow-hidden rounded-full bg-white/10">
            <div className="bg-up" style={{ flex: r.sentiment.positive }} /><div className="bg-slate-500" style={{ flex: r.sentiment.neutral }} /><div className="bg-down" style={{ flex: r.sentiment.negative }} /></div>}
          {r.news.length === 0 ? <p className="py-4 text-sm text-slate-500">No headlines were retrievable for this run.</p> :
            <ul className="max-h-72 space-y-2.5 overflow-auto pr-1">{r.news.map((n, i) => (
              <li key={i} className="text-sm"><a href={n.url} target="_blank" rel="noreferrer" className="group inline-flex items-start gap-1.5 text-slate-200 hover:text-cyan">
                <span className={clsx("mt-1.5 h-2 w-2 shrink-0 rounded-full", n.sentiment > 0.15 ? "bg-up" : n.sentiment < -0.15 ? "bg-down" : "bg-slate-500")} />{n.title}<ExternalLink size={12} className="mt-1 shrink-0 opacity-0 group-hover:opacity-100" /></a>
                <p className="ml-3.5 text-xs text-slate-500">{n.source}</p></li>))}</ul>}
        </Card>
      </div>

      <Card>
        <SectionTitle>Full brief</SectionTitle>
        <div className="prose-report">{r.sections.map((s) => (<div key={s.heading}><h2>{s.heading}</h2><ReactMarkdown remarkPlugins={[remarkGfm]}>{s.body}</ReactMarkdown></div>))}</div>
      </Card>

      {r.review_notes.length > 0 && (
        <Card><SectionTitle icon={AlertTriangle}>Reviewer notes</SectionTitle><ul className="space-y-1.5 text-sm text-slate-300">{r.review_notes.map((n, i) => <li key={i}>• {n}</li>)}</ul></Card>
      )}
      <p className="text-center text-xs text-slate-500">{r.disclaimer}</p>
    </div>
  );
}

export default function ReportView() {
  const { id = "" } = useParams();
  const nav = useNavigate();
  const qc = useQueryClient();
  const { data: job, error } = useQuery({ queryKey: ["job", id], queryFn: () => api.job(id), refetchInterval: (q) => (q.state.data && ["queued", "running"].includes(q.state.data.status) ? 3000 : false) });
  const active = !!job && (job.status === "queued" || job.status === "running");
  const live = useJobStream(id, active);
  const past = useQuery({ queryKey: ["events", id], queryFn: () => api.events(id), enabled: !!job && !active });
  const events = active ? live : past.data ?? live;

  if (error) return <Card><p className="text-down">{(error as Error).message}</p><Link to="/reports" className="btn-ghost mt-3">Back to reports</Link></Card>;
  if (!job) return <div className="space-y-4"><Skeleton className="h-10 w-1/2" /><Skeleton className="h-64" /></div>;
  const r = job.report;
  return (
    <div>
      <Link to="/reports" className="no-print mb-4 inline-flex items-center gap-1 text-sm text-slate-400 hover:text-white"><ArrowLeft size={14} /> Reports</Link>
      <PageHeader title={job.title || job.query} sub={r ? `${r.generated_at} · engine: ${r.engine} · ${job.depth}` : job.query}
        right={<div className="no-print flex flex-wrap items-center gap-2">
          {job.status === "completed" && <>
            <button className="btn-ghost" onClick={() => download(id, "md")}><Download size={14} /> Markdown</button>
            <button className="btn-ghost" onClick={() => download(id, "json")}><FileJson size={14} /> JSON</button>
            <button className="btn-ghost" onClick={() => window.print()}><Printer size={14} /> Print</button></>}
          {(job.status === "completed" || job.status === "failed") && <button className="btn-ghost" onClick={async () => { const n = await api.retryJob(id); qc.invalidateQueries({ queryKey: ["jobs"] }); nav(`/reports/${n.id}`); }}><RefreshCw size={14} /> Re-run</button>}
        </div>} />
      {active && (
        <div className="mx-auto max-w-3xl space-y-5">
          <Card>
            <div className="mb-3 flex items-center justify-between"><StatusBadge status={job.status} /><span className="text-sm font-semibold text-white">{job.progress}%</span></div>
            <div className="h-2 overflow-hidden rounded-full bg-white/10"><div className="h-full rounded-full bg-gradient-to-r from-brand to-cyan transition-all duration-700" style={{ width: `${Math.max(job.progress, 3)}%` }} /></div>
            <p className="mt-3 text-sm text-slate-400">Agents are working on: <span className="text-slate-200">{job.query}</span></p>
          </Card>
          <AgentTimeline job={job} events={events} />
        </div>
      )}
      {job.status === "failed" && <Card><p className="font-semibold text-down">Research failed</p><p className="mt-1 text-sm text-slate-400">{job.error}</p></Card>}
      {r && job.status === "completed" && <ReportBody r={r} />}
    </div>
  );
}
