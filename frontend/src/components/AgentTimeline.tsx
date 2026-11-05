import clsx from "clsx";
import { BrainCircuit, CheckCircle2, Database, Eye, LineChart, Loader2, PenLine, XCircle } from "lucide-react";
import type { Job, JobEvent } from "../lib/api";

const AGENTS = [
  { key: "planner", label: "Planner", desc: "Breaks the request into research questions", icon: BrainCircuit, stage: "planning" },
  { key: "collector", label: "Collector", desc: "Pulls prices, indicators and headlines in parallel", icon: Database, stage: "collecting" },
  { key: "analyst", label: "Analyst", desc: "Scores momentum, sentiment, SWOT and risk", icon: LineChart, stage: "analysing" },
  { key: "writer", label: "Writer", desc: "Drafts the research brief", icon: PenLine, stage: "writing" },
  { key: "reviewer", label: "Reviewer", desc: "Fact-checks and flags data quality", icon: Eye, stage: "reviewing" },
];
const ORDER = ["planning", "collecting", "analysing", "writing", "reviewing", "done"];

export function AgentTimeline({ job, events }: { job: Job; events: JobEvent[] }) {
  const cur = ORDER.indexOf(job.stage);
  const agents = job.depth === "quick" ? AGENTS.slice(0, 4) : AGENTS;
  return (
    <div className="space-y-3">
      {agents.map((a, i) => {
        const done = job.status === "completed" || (cur > i && job.status !== "failed") || (job.status === "failed" && cur > i);
        const active = job.status === "running" && cur === i;
        const failed = job.status === "failed" && cur === i;
        const logs = events.filter((e) => e.agent === a.key && e.kind === "log").slice(-3);
        const Icon = a.icon;
        return (
          <div key={a.key} className={clsx("glass flex gap-4 p-4 transition-all", active && "border-cyan/50 shadow-[0_0_30px_-10px_rgba(34,211,238,.6)]", !done && !active && !failed && "opacity-50")}>
            <div className={clsx("flex h-10 w-10 shrink-0 items-center justify-center rounded-xl", done ? "bg-up/15 text-up" : active ? "bg-cyan/15 text-cyan" : failed ? "bg-down/15 text-down" : "bg-white/5 text-slate-400")}>
              {failed ? <XCircle size={20} /> : done ? <CheckCircle2 size={20} /> : active ? <Loader2 size={20} className="animate-spin" /> : <Icon size={20} />}
            </div>
            <div className="min-w-0 flex-1">
              <p className="font-semibold text-white">{a.label} <span className="ml-1 text-xs font-normal text-slate-400">{a.desc}</span></p>
              <ul className="mt-1 space-y-0.5">
                {logs.map((l) => <li key={l.id} className="truncate text-xs text-slate-400">› {l.message}</li>)}
              </ul>
            </div>
          </div>
        );
      })}
    </div>
  );
}
