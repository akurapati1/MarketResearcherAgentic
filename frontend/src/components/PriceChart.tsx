import { Area, Bar, CartesianGrid, ComposedChart, Line, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { SeriesPoint } from "../lib/api";
import { num } from "../lib/format";

export function PriceChart({ data, height = 320, showVolume = true }: { data: SeriesPoint[]; height?: number; showVolume?: boolean }) {
  const first = data[0]?.c ?? 0, last = data[data.length - 1]?.c ?? 0;
  const up = last >= first;
  const color = up ? "#34d399" : "#fb7185";
  const maxV = Math.max(...data.map((d) => d.v || 0), 1);
  return (
    <ResponsiveContainer width="100%" height={height}>
      <ComposedChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
        <defs>
          <linearGradient id="pc" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={color} stopOpacity={0.35} />
            <stop offset="100%" stopColor={color} stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid stroke="rgba(148,163,255,.08)" vertical={false} />
        <XAxis dataKey="t" tick={{ fill: "#7c86ad", fontSize: 11 }} tickLine={false} axisLine={false} minTickGap={50}
          tickFormatter={(t: string) => new Date(t).toLocaleDateString("en-US", { month: "short", year: "2-digit" })} />
        <YAxis yAxisId="p" domain={["auto", "auto"]} orientation="right" width={56} tick={{ fill: "#7c86ad", fontSize: 11 }} tickLine={false} axisLine={false}
          tickFormatter={(v: number) => num(v, 0)} />
        <YAxis yAxisId="v" hide domain={[0, maxV * 5]} />
        <Tooltip
          contentStyle={{ background: "#0a0f1f", border: "1px solid rgba(148,163,255,.25)", borderRadius: 12, fontSize: 12 }}
          labelStyle={{ color: "#a5b4fc" }}
          formatter={(v, n) => [num(Number(v)), n === "c" ? "Close" : n === "sma20" ? "SMA 20" : n === "sma50" ? "SMA 50" : "Volume"]}
        />
        {showVolume && <Bar yAxisId="v" dataKey="v" fill="rgba(129,140,248,.25)" isAnimationActive={false} />}
        <Area yAxisId="p" type="monotone" dataKey="c" stroke={color} strokeWidth={2} fill="url(#pc)" isAnimationActive={false} />
        <Line yAxisId="p" type="monotone" dataKey="sma20" stroke="#22d3ee" strokeWidth={1.3} dot={false} connectNulls isAnimationActive={false} />
        <Line yAxisId="p" type="monotone" dataKey="sma50" stroke="#fbbf24" strokeWidth={1.3} dot={false} connectNulls isAnimationActive={false} />
      </ComposedChart>
    </ResponsiveContainer>
  );
}
