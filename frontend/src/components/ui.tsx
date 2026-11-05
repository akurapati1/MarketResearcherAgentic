import clsx from "clsx";
import { type LucideIcon } from "lucide-react";
import type { ReactNode } from "react";
import { Area, AreaChart, ResponsiveContainer, YAxis } from "recharts";
import { stanceColor } from "../lib/format";

export function Card({ className, children, hover }: { className?: string; children: ReactNode; hover?: boolean }) {
  return <div className={clsx("glass p-5", hover && "glass-hover", className)}>{children}</div>;
}

export function SectionTitle({ icon: Icon, children, right }: { icon?: LucideIcon; children: ReactNode; right?: ReactNode }) {
  return (
    <div className="mb-4 flex items-center justify-between gap-3">
      <h3 className="flex items-center gap-2 text-sm font-semibold uppercase tracking-wider text-slate-300">
        {Icon && <Icon size={16} className="text-cyan" />} {children}
      </h3>
      {right}
    </div>
  );
}

export function Stat({ label, value, icon: Icon, accent = "#6366f1", sub }: { label: string; value: ReactNode; icon: LucideIcon; accent?: string; sub?: string }) {
  return (
    <Card hover className="fade-up">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs uppercase tracking-wider text-slate-400">{label}</p>
          <p className="mt-2 text-3xl font-bold text-white">{value}</p>
          {sub && <p className="mt-1 text-xs text-slate-400">{sub}</p>}
        </div>
        <div className="rounded-xl p-2.5" style={{ background: `${accent}22`, color: accent }}>
          <Icon size={20} />
        </div>
      </div>
    </Card>
  );
}

export function StanceBadge({ stance, confidence }: { stance?: string | null; confidence?: number | null }) {
  if (!stance) return null;
  return (
    <span className={clsx("inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-semibold", stanceColor(stance))}>
      {stance}{confidence != null && <span className="opacity-70">· {confidence}%</span>}
    </span>
  );
}

export function StatusBadge({ status }: { status: string }) {
  const map: Record<string, string> = {
    completed: "text-up bg-up/10 border-up/30", running: "text-cyan bg-cyan/10 border-cyan/30",
    queued: "text-slate-300 bg-slate-400/10 border-slate-400/30", failed: "text-down bg-down/10 border-down/30",
  };
  return (
    <span className={clsx("inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium capitalize", map[status])}>
      {status === "running" && <span className="pulse-dot h-1.5 w-1.5 rounded-full bg-cyan" />}
      {status}
    </span>
  );
}

export function DemoBadge({ source }: { source?: string }) {
  if (source !== "synthetic") return null;
  return <span className="rounded-md border border-warn/30 bg-warn/10 px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-warn" title="Deterministic demo data — live market feed unavailable">demo data</span>;
}

export function Sparkline({ data, up, height = 40 }: { data: number[]; up: boolean; height?: number }) {
  const color = up ? "#34d399" : "#fb7185";
  const id = `sp${Math.random().toString(36).slice(2, 8)}`;
  return (
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart data={data.map((v, i) => ({ i, v }))} margin={{ top: 2, bottom: 2, left: 0, right: 0 }}>
        <defs>
          <linearGradient id={id} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={color} stopOpacity={0.4} />
            <stop offset="100%" stopColor={color} stopOpacity={0} />
          </linearGradient>
        </defs>
        <YAxis hide domain={["dataMin", "dataMax"]} />
        <Area type="monotone" dataKey="v" stroke={color} strokeWidth={1.8} fill={`url(#${id})`} isAnimationActive={false} />
      </AreaChart>
    </ResponsiveContainer>
  );
}

export function Gauge({ value, min = -1, max = 1, label, size = 150 }: { value: number; min?: number; max?: number; label: string; size?: number }) {
  const t = Math.max(0, Math.min(1, (value - min) / (max - min)));
  const angle = Math.PI * (1 - t);
  const r = size / 2 - 12, cx = size / 2, cy = size / 2 + 4;
  const x = cx + r * Math.cos(angle), y = cy - r * Math.sin(angle);
  const arc = (a0: number, a1: number) => {
    const p = (a: number) => `${cx + r * Math.cos(a)} ${cy - r * Math.sin(a)}`;
    return `M ${p(a0)} A ${r} ${r} 0 0 1 ${p(a1)}`;
  };
  return (
    <div className="flex flex-col items-center">
      <svg width={size} height={size / 2 + 22} viewBox={`0 0 ${size} ${size / 2 + 22}`}>
        <path d={arc(Math.PI, 0)} stroke="#222d58" strokeWidth={10} fill="none" strokeLinecap="round" />
        <defs>
          <linearGradient id="gg" x1="0" x2="1"><stop offset="0" stopColor="#fb7185" /><stop offset=".5" stopColor="#fbbf24" /><stop offset="1" stopColor="#34d399" /></linearGradient>
        </defs>
        <path d={arc(Math.PI, angle)} stroke="url(#gg)" strokeWidth={10} fill="none" strokeLinecap="round" />
        <circle cx={x} cy={y} r={6} fill="#fff" stroke="#0a0f1f" strokeWidth={2} />
      </svg>
      <p className="-mt-3 text-lg font-bold text-white">{label}</p>
    </div>
  );
}

export function Empty({ icon: Icon, title, hint, action }: { icon: LucideIcon; title: string; hint?: string; action?: ReactNode }) {
  return (
    <div className="flex flex-col items-center justify-center py-14 text-center">
      <div className="mb-3 rounded-2xl bg-brand/10 p-4 text-brand"><Icon size={28} /></div>
      <p className="font-semibold text-white">{title}</p>
      {hint && <p className="mt-1 max-w-sm text-sm text-slate-400">{hint}</p>}
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}

export function Skeleton({ className }: { className?: string }) {
  return <div className={clsx("skeleton h-6", className)} />;
}

export function PageHeader({ title, sub, right }: { title: ReactNode; sub?: string; right?: ReactNode }) {
  return (
    <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
      <div>
        <h1 className="text-2xl font-bold text-white md:text-3xl">{title}</h1>
        {sub && <p className="mt-1 text-sm text-slate-400">{sub}</p>}
      </div>
      {right}
    </div>
  );
}
