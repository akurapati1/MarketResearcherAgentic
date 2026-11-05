import { useQuery } from "@tanstack/react-query";
import { Plus, X } from "lucide-react";
import { useEffect, useState } from "react";
import { api } from "../lib/api";

export function useDebounced<T>(value: T, ms = 250) {
  const [v, setV] = useState(value);
  useEffect(() => { const t = setTimeout(() => setV(value), ms); return () => clearTimeout(t); }, [value, ms]);
  return v;
}

export function TickerPicker({ value, onChange, max = 5 }: { value: string[]; onChange: (v: string[]) => void; max?: number }) {
  const [text, setText] = useState("");
  const [open, setOpen] = useState(false);
  const q = useDebounced(text.trim());
  const { data = [] } = useQuery({ queryKey: ["search", q], queryFn: () => api.search(q), enabled: q.length > 0 });
  const add = (s: string) => {
    s = s.toUpperCase().trim();
    if (s && !value.includes(s) && value.length < max) onChange([...value, s]);
    setText(""); setOpen(false);
  };
  return (
    <div>
      <div className="mb-2 flex flex-wrap gap-2">
        {value.map((s) => (
          <span key={s} className="mono inline-flex items-center gap-1.5 rounded-lg border border-brand/40 bg-brand/15 px-2.5 py-1 text-xs font-medium text-indigo-200">
            {s}
            <button aria-label={`Remove ${s}`} onClick={() => onChange(value.filter((x) => x !== s))} className="opacity-60 hover:opacity-100"><X size={12} /></button>
          </span>
        ))}
      </div>
      <div className="relative">
        <input className="input" placeholder={value.length >= max ? `Max ${max} tickers` : "Add tickers — e.g. NVDA, Tesla, RELIANCE.NS"} value={text} disabled={value.length >= max}
          onChange={(e) => { setText(e.target.value); setOpen(true); }}
          onKeyDown={(e) => { if (e.key === "Enter" && text) { e.preventDefault(); add(data[0]?.symbol ?? text); } }}
          onBlur={() => setTimeout(() => setOpen(false), 150)} onFocus={() => setOpen(true)} />
        {open && q && data.length > 0 && (
          <ul className="glass absolute z-20 mt-2 max-h-64 w-full overflow-auto p-1.5">
            {data.map((h) => (
              <li key={h.symbol}>
                <button className="flex w-full items-center justify-between rounded-lg px-3 py-2 text-left text-sm hover:bg-white/5" onMouseDown={() => add(h.symbol)}>
                  <span><span className="mono font-semibold text-white">{h.symbol}</span> <span className="ml-2 text-slate-400">{h.name}</span></span>
                  <Plus size={14} className="text-cyan" />
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
