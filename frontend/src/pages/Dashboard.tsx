import { useQuery } from "@tanstack/react-query";
import { Activity, ArrowRight, CheckCircle2, FileText, Loader2, Sparkles, Star } from "lucide-react";
import { useState } from "react";
import { Bar, BarChart, Cell, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis } from "recharts";
import { Link, useNavigate } from "react-router-dom";
import { Card, DemoBadge, Empty, SectionTitle, Skeleton, Sparkline, Stat, StanceBadge, StatusBadge } from "../components/ui";
import { api } from "../lib/api";
import { ago, money, pctRaw, tone } from "../lib/format";

const IDEAS = ["Compare NVIDIA vs AMD for AI chips", "Is Tesla a buy after recent volatility?", "Outlook for Indian IT: TCS and Infosys", "Bitcoin momentum and risk assessment"];

export default function Dashboard() {
  const nav = useNavigate();
  const [q, setQ] = useState("");
  const stats = useQuery({ queryKey: ["stats"], queryFn: api.stats, refetchInterval: 8000 });
  const overview = useQuery({ queryKey: ["overview"], queryFn: api.overview, refetchInterval: 60000 });
  const recent = useQuery({ queryKey: ["jobs", "recent"], queryFn: () => api.jobs({ page_size: 6 }), refetchInterval: 5000 });
  const watch = useQuery({ queryKey: ["watchlist"], queryFn: api.watchlist });
  const s = stats.data;
  const stanceData = s ? [{ name: "Bullish", value: s.stance.Bullish, c: "#34d399" }, { name: "Neutral", value: s.stance.Neutral, c: "#fbbf24" }, { name: "Bearish", value: s.stance.Bearish, c: "#fb7185" }] : [];
  const stanceTotal = stanceData.reduce((a, b) => a + b.value, 0);

  return (
    <div className="space-y-6">
      <section className="glass relative overflow-hidden p-6 md:p-8">
        <div className="pointer-events-none absolute -right-20 -top-20 h-72 w-72 rounded-full bg-brand/25 blur-3xl" />
        <p className="text-xs font-semibold uppercase tracking-widest text-cyan">Agentic market intelligence</p>
        <h1 className="mt-2 text-3xl font-bold text-white md:text-4xl">What do you want to <span className="gradient-text">research</span> today?</h1>
        <form className="mt-5 flex flex-col gap-3 sm:flex-row" onSubmit={(e) => { e.preventDefault(); nav(`/new?q=${encodeURIComponent(q)}`); }}>
          <input className="input !py-3.5 text-base" placeholder="e.g. Compare Microsoft and Alphabet’s AI positioning" value={q} onChange={(e) => setQ(e.target.value)} />
          <button className="btn-primary justify-center whitespace-nowrap"><Sparkles size={16} /> Start research</button>
        </form>
        <div className="mt-4 flex flex-wrap gap-2">
          {IDEAS.map((i) => <button key={i} className="btn-ghost !text-xs" onClick={() => nav(`/new?q=${encodeURIComponent(i)}`)}>{i}</button>)}
        </div>
      </section>

      <section className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <Stat label="Reports" value={s?.total ?? "—"} icon={FileText} accent="#818cf8" sub={s ? `${s.completed} completed` : undefined} />
        <Stat label="In progress" value={s ? s.running + s.queued : "—"} icon={Loader2} accent="#22d3ee" sub={s ? `${s.queued} queued` : undefined} />
        <Stat label="Success rate" value={s && s.completed + s.failed ? `${Math.round((s.completed / (s.completed + s.failed)) * 100)}%` : "—"} icon={CheckCircle2} accent="#34d399" sub={s ? `${s.failed} failed` : undefined} />
        <Stat label="Watchlist" value={s?.watchlist ?? "—"} icon={Star} accent="#fbbf24" sub="tracked symbols" />
      </section>

      <section>
        <SectionTitle icon={Activity}>Markets</SectionTitle>
        <div className="grid grid-cols-2 gap-4 md:grid-cols-3 xl:grid-cols-6">
          {overview.isLoading ? Array.from({ length: 6 }).map((_, i) => <Skeleton key={i} className="h-28" />) :
            overview.data?.map((q) => (
              <Link key={q.symbol} to={`/explore/${encodeURIComponent(q.symbol)}`}>
                <Card hover className="!p-4">
                  <div className="flex items-center justify-between"><span className="mono text-xs font-medium text-slate-300">{q.symbol.replace("^", "")}</span><DemoBadge source={q.source} /></div>
                  <p className="mt-1 truncate text-[11px] text-slate-500">{q.name}</p>
                  <p className="mt-2 text-lg font-bold text-white">{money(q.price, q.currency)}</p>
                  <p className={`text-xs font-semibold ${tone(q.change_pct)}`}>{pctRaw(q.change_pct)}</p>
                  <div className="mt-1 -mb-1"><Sparkline data={q.spark} up={q.change_pct >= 0} height={34} /></div>
                </Card>
              </Link>
            ))}
        </div>
      </section>

      <section className="grid gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <SectionTitle icon={FileText} right={<Link to="/reports" className="flex items-center gap-1 text-xs text-cyan hover:underline">View all <ArrowRight size={12} /></Link>}>Recent research</SectionTitle>
          {recent.data && recent.data.items.length === 0 ? (
            <Empty icon={Sparkles} title="No research yet" hint="Kick off your first agentic research run — it takes seconds." action={<Link to="/new" className="btn-primary">New research</Link>} />
          ) : (
            <ul className="divide-y divide-white/5">
              {recent.data?.items.map((j) => (
                <li key={j.id}>
                  <Link to={`/reports/${j.id}`} className="flex items-center justify-between gap-3 rounded-lg px-2 py-3 hover:bg-white/5">
                    <div className="min-w-0">
                      <p className="truncate font-medium text-white">{j.title || j.query}</p>
                      <p className="mt-0.5 text-xs text-slate-500">{ago(j.created_at)} · {j.depth}{j.tickers.length ? ` · ${j.tickers.join(", ")}` : ""}</p>
                    </div>
                    <div className="flex shrink-0 items-center gap-2">{j.status === "completed" ? <StanceBadge stance={j.stance} confidence={j.confidence} /> : <StatusBadge status={j.status} />}</div>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </Card>

        <div className="space-y-6">
          <Card>
            <SectionTitle>Agent stance mix</SectionTitle>
            {stanceTotal === 0 ? <p className="py-6 text-center text-sm text-slate-500">Complete a report to see the distribution.</p> : (
              <div className="flex items-center gap-4">
                <div className="h-32 w-32">
                  <ResponsiveContainer><PieChart><Pie data={stanceData} dataKey="value" innerRadius={38} outerRadius={58} paddingAngle={3} stroke="none">{stanceData.map((d) => <Cell key={d.name} fill={d.c} />)}</Pie></PieChart></ResponsiveContainer>
                </div>
                <ul className="space-y-1.5 text-sm">{stanceData.map((d) => <li key={d.name} className="flex items-center gap-2"><span className="h-2.5 w-2.5 rounded-full" style={{ background: d.c }} />{d.name} <span className="text-slate-400">{d.value}</span></li>)}</ul>
              </div>
            )}
          </Card>
          <Card>
            <SectionTitle>Activity · 14 days</SectionTitle>
            <div className="h-28">
              <ResponsiveContainer><BarChart data={s?.activity ?? []}><XAxis dataKey="date" hide /><Tooltip cursor={{ fill: "rgba(148,163,255,.08)" }} contentStyle={{ background: "#0a0f1f", border: "1px solid rgba(148,163,255,.25)", borderRadius: 10, fontSize: 12 }} /><Bar dataKey="count" name="Reports" fill="#6366f1" radius={[4, 4, 0, 0]} /></BarChart></ResponsiveContainer>
            </div>
          </Card>
        </div>
      </section>

      {watch.data && watch.data.length > 0 && (
        <section>
          <SectionTitle icon={Star} right={<Link to="/watchlist" className="text-xs text-cyan hover:underline">Manage</Link>}>Watchlist</SectionTitle>
          <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
            {watch.data.slice(0, 4).map((w) => w.quote && (
              <Link key={w.id} to={`/explore/${encodeURIComponent(w.symbol)}`}><Card hover className="!p-4">
                <span className="mono text-sm font-semibold text-white">{w.symbol}</span>
                <p className="mt-1 text-lg font-bold text-white">{money(w.quote.price, w.quote.currency)}</p>
                <p className={`text-xs font-semibold ${tone(w.quote.change_pct)}`}>{pctRaw(w.quote.change_pct)}</p>
              </Card></Link>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
