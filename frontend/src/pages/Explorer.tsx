import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import clsx from "clsx";
import { Search, Sparkles, Star } from "lucide-react";
import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { PriceChart } from "../components/PriceChart";
import { useDebounced } from "../components/TickerPicker";
import { Card, DemoBadge, Empty, PageHeader, Skeleton } from "../components/ui";
import { api } from "../lib/api";
import { money, num, pct, pctRaw, tone } from "../lib/format";

const RANGES = ["1mo", "3mo", "6mo", "1y", "2y", "5y"];
const POPULAR = ["AAPL", "NVDA", "MSFT", "TSLA", "BTC-USD", "RELIANCE.NS", "^GSPC", "GC=F"];

export default function Explorer() {
  const { symbol } = useParams();
  const nav = useNavigate();
  const qc = useQueryClient();
  const [text, setText] = useState("");
  const [range, setRange] = useState("1y");
  const dq = useDebounced(text.trim());
  const hits = useQuery({ queryKey: ["search", dq], queryFn: () => api.search(dq), enabled: dq.length > 0 });
  const hist = useQuery({ queryKey: ["history", symbol, range], queryFn: () => api.history(symbol!, range), enabled: !!symbol });
  const add = useMutation({ mutationFn: () => api.addWatch(symbol!), onSuccess: () => { qc.invalidateQueries({ queryKey: ["watchlist"] }); qc.invalidateQueries({ queryKey: ["stats"] }); } });
  const q = hist.data?.quote, i = hist.data?.indicators;
  return (
    <div>
      <PageHeader title="Market Explorer" sub="Look up any instrument, inspect its trend, then hand it to the research agents." />
      <div className="relative mb-6 max-w-xl">
        <Search size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500" />
        <input className="input !pl-10" placeholder="Search symbol or company…" value={text} onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter" && text.trim()) { nav(`/explore/${encodeURIComponent(hits.data?.[0]?.symbol ?? text.trim().toUpperCase())}`); setText(""); } }} />
        {text && hits.data && hits.data.length > 0 && (
          <ul className="glass absolute z-20 mt-2 w-full p-1.5">{hits.data.map((h) => (
            <li key={h.symbol}><button className="flex w-full justify-between rounded-lg px-3 py-2 text-left text-sm hover:bg-white/5" onClick={() => { nav(`/explore/${encodeURIComponent(h.symbol)}`); setText(""); }}>
              <span><b className="mono text-white">{h.symbol}</b> <span className="ml-2 text-slate-400">{h.name}</span></span><span className="text-xs text-slate-500">{h.sector}</span></button></li>))}</ul>
        )}
      </div>
      {!symbol ? (
        <Card><Empty icon={Search} title="Pick an instrument" hint="Search above or jump into a popular one."
          action={<div className="flex max-w-lg flex-wrap justify-center gap-2">{POPULAR.map((s) => <Link key={s} to={`/explore/${encodeURIComponent(s)}`} className="btn-ghost mono">{s}</Link>)}</div>} /></Card>
      ) : hist.isLoading ? <Skeleton className="h-96" /> : hist.error ? <Card><p className="text-down">{(hist.error as Error).message}</p></Card> : q && i && (
        <div className="space-y-6">
          <Card>
            <div className="mb-4 flex flex-wrap items-start justify-between gap-4">
              <div>
                <p className="flex items-center gap-2 text-2xl font-bold text-white">{q.name} <span className="mono text-sm text-slate-400">{q.symbol}</span> <DemoBadge source={q.source} /></p>
                <p className="mt-1 text-4xl font-bold text-white">{money(q.price, q.currency)} <span className={clsx("ml-2 text-lg font-semibold", tone(q.change_pct))}>{pctRaw(q.change_pct)}</span></p>
              </div>
              <div className="flex flex-wrap gap-2">
                <button className="btn-ghost" onClick={() => add.mutate()} disabled={add.isPending || add.isSuccess}><Star size={14} /> {add.isSuccess ? "Added" : "Watch"}</button>
                <Link to={`/new?q=${encodeURIComponent(`Research outlook for ${q.name}`)}&t=${encodeURIComponent(q.symbol)}`} className="btn-primary"><Sparkles size={14} /> Research this</Link>
              </div>
            </div>
            {add.error && <p className="mb-2 text-sm text-warn">{(add.error as Error).message}</p>}
            <div className="mb-3 flex gap-1.5">{RANGES.map((r) => <button key={r} onClick={() => setRange(r)} className={clsx("rounded-lg px-3 py-1 text-xs font-medium uppercase", range === r ? "bg-brand text-white" : "bg-white/5 text-slate-400 hover:text-white")}>{r}</button>)}</div>
            <PriceChart data={hist.data!.series.map((s) => ({ t: s.t, c: s.c, v: s.v, sma20: s.sma20, sma50: s.sma50 }))} height={380} />
          </Card>
          <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
            {[["RSI (14)", num(i.rsi14, 0)], ["Trend", i.trend], ["1M", pct(i.return_1m)], ["3M", pct(i.return_3m)], ["1Y", pct(i.return_1y)],
              ["Volatility", i.volatility != null ? `${(i.volatility * 100).toFixed(0)}%` : "—"], ["52w high", num(i.high_52w)], ["52w low", num(i.low_52w)]].map(([l, v]) => (
              <Card key={l} className="!p-4"><p className="text-xs uppercase tracking-wider text-slate-500">{l}</p><p className="mt-1 text-xl font-semibold capitalize text-white">{v}</p></Card>))}
          </div>
        </div>
      )}
    </div>
  );
}
