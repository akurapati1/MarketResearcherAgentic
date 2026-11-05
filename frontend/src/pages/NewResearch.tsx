import { useMutation, useQueryClient } from "@tanstack/react-query";
import clsx from "clsx";
import { Gauge as GaugeIcon, Microscope, Rocket, Sparkles, Zap } from "lucide-react";
import { useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { TickerPicker } from "../components/TickerPicker";
import { Card, PageHeader } from "../components/ui";
import { api } from "../lib/api";

const DEPTHS = [
  { key: "quick", label: "Quick scan", desc: "Plan → collect → analyse → write. Seconds.", icon: Zap },
  { key: "standard", label: "Standard", desc: "Adds a reviewer pass for data-quality checks.", icon: GaugeIcon },
  { key: "deep", label: "Deep dive", desc: "Full pipeline with invalidation triggers.", icon: Microscope },
] as const;

const TEMPLATES = [
  { t: "Compare NVIDIA vs AMD for AI chips", k: ["NVDA", "AMD"] },
  { t: "Is Tesla a buy after recent volatility?", k: ["TSLA"] },
  { t: "Big tech earnings-season outlook: Apple, Microsoft, Alphabet", k: ["AAPL", "MSFT", "GOOGL"] },
  { t: "Indian IT services outlook: TCS vs Infosys", k: ["TCS.NS", "INFY.NS"] },
  { t: "Bitcoin and Ethereum risk/return assessment", k: ["BTC-USD", "ETH-USD"] },
  { t: "Energy sector positioning: Exxon vs Reliance", k: ["XOM", "RELIANCE.NS"] },
];

export default function NewResearch() {
  const [sp] = useSearchParams();
  const nav = useNavigate();
  const qc = useQueryClient();
  const [query, setQuery] = useState(sp.get("q") ?? "");
  const [tickers, setTickers] = useState<string[]>(sp.get("t")?.split(",").filter(Boolean) ?? []);
  const [depth, setDepth] = useState<string>("standard");
  const m = useMutation({
    mutationFn: () => api.createJob({ query: query.trim(), tickers, depth }),
    onSuccess: (job) => { qc.invalidateQueries({ queryKey: ["jobs"] }); qc.invalidateQueries({ queryKey: ["stats"] }); nav(`/reports/${job.id}`); },
  });
  const valid = query.trim().length >= 3;
  return (
    <div className="mx-auto max-w-4xl">
      <PageHeader title={<>New <span className="gradient-text">research</span></>} sub="Describe what you want to know. A team of agents plans, gathers data, analyses and writes the brief." />
      <div className="grid gap-6 lg:grid-cols-5">
        <Card className="space-y-6 lg:col-span-3">
          <div>
            <label className="mb-2 block text-sm font-medium text-slate-300" htmlFor="q">Research question</label>
            <textarea id="q" className="input min-h-32 resize-y" maxLength={2000} placeholder="e.g. How does Microsoft’s AI strategy compare with Alphabet’s, and what are the risks for each?" value={query} onChange={(e) => setQuery(e.target.value)} />
            <p className="mt-1 text-right text-xs text-slate-500">{query.length}/2000</p>
          </div>
          <div>
            <label className="mb-2 block text-sm font-medium text-slate-300">Instruments <span className="text-slate-500">(optional — agents also detect companies in your question)</span></label>
            <TickerPicker value={tickers} onChange={setTickers} />
          </div>
          <div>
            <label className="mb-2 block text-sm font-medium text-slate-300">Depth</label>
            <div className="grid gap-3 sm:grid-cols-3">
              {DEPTHS.map(({ key, label, desc, icon: Icon }) => (
                <button key={key} type="button" onClick={() => setDepth(key)}
                  className={clsx("rounded-xl border p-3 text-left transition-all", depth === key ? "border-brand bg-brand/15 shadow-[0_0_24px_-8px_rgba(99,102,241,.8)]" : "border-white/10 bg-white/[.02] hover:border-white/25")}>
                  <Icon size={18} className={depth === key ? "text-cyan" : "text-slate-400"} />
                  <p className="mt-2 text-sm font-semibold text-white">{label}</p>
                  <p className="mt-0.5 text-xs text-slate-400">{desc}</p>
                </button>
              ))}
            </div>
          </div>
          {m.error && <p className="rounded-lg border border-down/30 bg-down/10 p-3 text-sm text-down">{(m.error as Error).message}</p>}
          <button className="btn-primary w-full justify-center !py-3" disabled={!valid || m.isPending} onClick={() => m.mutate()}>
            <Rocket size={16} /> {m.isPending ? "Launching agents…" : "Launch research"}
          </button>
        </Card>
        <div className="space-y-3 lg:col-span-2">
          <p className="flex items-center gap-2 text-sm font-semibold text-slate-300"><Sparkles size={16} className="text-cyan" /> Start from a template</p>
          {TEMPLATES.map((t) => (
            <button key={t.t} onClick={() => { setQuery(t.t); setTickers(t.k); }} className="glass glass-hover block w-full p-3.5 text-left">
              <p className="text-sm font-medium text-white">{t.t}</p>
              <p className="mono mt-1 text-xs text-slate-500">{t.k.join(" · ")}</p>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
