import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Sparkles, Star, Trash2 } from "lucide-react";
import { useState } from "react";
import { Link } from "react-router-dom";
import { TickerPicker } from "../components/TickerPicker";
import { Card, DemoBadge, Empty, PageHeader, Skeleton, Sparkline } from "../components/ui";
import { api } from "../lib/api";
import { money, pctRaw, tone } from "../lib/format";

export default function Watchlist() {
  const qc = useQueryClient();
  const [pick, setPick] = useState<string[]>([]);
  const { data, isLoading } = useQuery({ queryKey: ["watchlist"], queryFn: api.watchlist, refetchInterval: 60000 });
  const inv = () => { qc.invalidateQueries({ queryKey: ["watchlist"] }); qc.invalidateQueries({ queryKey: ["stats"] }); };
  const add = useMutation({ mutationFn: (s: string) => api.addWatch(s), onSuccess: () => { setPick([]); inv(); } });
  const del = useMutation({ mutationFn: api.removeWatch, onSuccess: inv });
  return (
    <div>
      <PageHeader title="Watchlist" sub="Symbols you track. Launch research on the whole list in one click." right={data && data.length > 0 ?
        <Link className="btn-primary" to={`/new?q=${encodeURIComponent("Weekly review of my watchlist")}&t=${data.slice(0, 5).map((d) => d.symbol).join(",")}`}><Sparkles size={14} /> Research watchlist</Link> : undefined} />
      <Card className="mb-6 max-w-xl">
        <TickerPicker value={pick} max={1} onChange={(v) => { setPick(v); if (v[0]) add.mutate(v[0]); }} />
        {add.error && <p className="mt-2 text-sm text-warn">{(add.error as Error).message}</p>}
      </Card>
      {isLoading ? <Skeleton className="h-48" /> : !data?.length ? <Card><Empty icon={Star} title="Your watchlist is empty" hint="Add a symbol above to start tracking it." /></Card> : (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {data.map((w) => (
            <Card key={w.id} hover className="group">
              <div className="flex items-start justify-between">
                <Link to={`/explore/${encodeURIComponent(w.symbol)}`}>
                  <p className="mono text-lg font-bold text-white">{w.symbol} {w.quote && <DemoBadge source={w.quote.source} />}</p>
                  <p className="text-xs text-slate-500">{w.quote?.name}</p>
                </Link>
                <button aria-label={`Remove ${w.symbol}`} className="rounded-lg p-1.5 text-slate-500 hover:bg-down/10 hover:text-down" onClick={() => del.mutate(w.symbol)}><Trash2 size={15} /></button>
              </div>
              {w.quote ? <>
                <p className="mt-3 text-2xl font-bold text-white">{money(w.quote.price, w.quote.currency)} <span className={`ml-1 text-sm font-semibold ${tone(w.quote.change_pct)}`}>{pctRaw(w.quote.change_pct)}</span></p>
                <div className="mt-2"><Sparkline data={w.quote.spark} up={w.quote.change_pct >= 0} height={52} /></div></> : <p className="mt-3 text-sm text-slate-500">Quote unavailable</p>}
              <Link to={`/new?q=${encodeURIComponent(`Research outlook for ${w.quote?.name ?? w.symbol}`)}&t=${w.symbol}`} className="btn-ghost mt-3 w-full justify-center"><Sparkles size={14} /> Research</Link>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
