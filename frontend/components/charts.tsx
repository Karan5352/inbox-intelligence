"use client";

import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  LabelList,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { categoryColor } from "@/lib/categories";
import type { Insights } from "@/lib/types";

const AXIS = { fontSize: 11, fill: "var(--viz-muted)" };

// Shared themed tooltip - text wears ink tokens, never the series color.
function ChartTooltip({ active, payload, label, fmt }: any) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-lg border border-hairline bg-surface px-3 py-2 text-xs shadow-lg">
      {label != null && <div className="mb-1 font-medium text-ink">{label}</div>}
      {payload.map((p: any) => (
        <div key={p.name} className="flex items-center gap-2 text-ink-2">
          <span className="inline-block h-2 w-2 rounded-sm" style={{ background: p.color || p.fill }} />
          <span className="capitalize">{p.name}</span>
          <span className="ml-auto tabular-nums text-ink">{fmt ? fmt(p.value) : p.value}</span>
        </div>
      ))}
    </div>
  );
}

// Magnitude by category → single sequential blue, ranked, with direct value labels.
export function CategoryBar({ data }: { data: Insights["by_category"] }) {
  const rows = [...data].sort((a, b) => b.count - a.count);
  return (
    <ResponsiveContainer width="100%" height={Math.max(rows.length * 34, 120)}>
      <BarChart data={rows} layout="vertical" margin={{ left: 8, right: 28, top: 4, bottom: 4 }}>
        <CartesianGrid horizontal={false} stroke="var(--viz-grid)" />
        <XAxis type="number" hide />
        <YAxis
          type="category"
          dataKey="name"
          width={92}
          tickLine={false}
          axisLine={false}
          tick={AXIS}
        />
        <Tooltip cursor={{ fill: "var(--surface-2)" }} content={<ChartTooltip />} />
        <Bar dataKey="count" radius={[0, 4, 4, 0]} barSize={16}>
          {rows.map((r) => (
            <Cell key={r.category} fill={categoryColor(r.category)} />
          ))}
          <LabelList dataKey="count" position="right" fontSize={11} fill="var(--ink-2)" />
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

// Volume over time → single blue area series (no legend; the card title names it).
export function VolumeArea({ data }: { data: Insights["volume_by_day"] }) {
  return (
    <ResponsiveContainer width="100%" height={200}>
      <AreaChart data={data} margin={{ left: 4, right: 8, top: 8, bottom: 4 }}>
        <defs>
          <linearGradient id="vol" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="var(--series-1)" stopOpacity={0.35} />
            <stop offset="100%" stopColor="var(--series-1)" stopOpacity={0.02} />
          </linearGradient>
        </defs>
        <CartesianGrid vertical={false} stroke="var(--viz-grid)" />
        <XAxis
          dataKey="date"
          tickLine={false}
          axisLine={false}
          tick={AXIS}
          tickFormatter={(d) => d.slice(5)}
          minTickGap={24}
        />
        <YAxis tickLine={false} axisLine={false} tick={AXIS} width={28} allowDecimals={false} />
        <Tooltip content={<ChartTooltip />} />
        <Area
          type="monotone"
          dataKey="count"
          name="emails"
          stroke="var(--series-1)"
          strokeWidth={2}
          fill="url(#vol)"
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}

// Accuracy trend → single line, y as %, one dot per snapshot.
export function AccuracyLine({ data }: { data: Insights["accuracy_trend"] }) {
  const rows = data.map((d, i) => ({ ...d, idx: i }));
  return (
    <ResponsiveContainer width="100%" height={200}>
      <LineChart data={rows} margin={{ left: 4, right: 12, top: 8, bottom: 4 }}>
        <CartesianGrid vertical={false} stroke="var(--viz-grid)" />
        <XAxis
          dataKey="num_corrections"
          tickLine={false}
          axisLine={false}
          tick={AXIS}
          label={{ value: "corrections", position: "insideBottom", offset: -2, fontSize: 10, fill: "var(--viz-muted)" }}
        />
        <YAxis
          domain={[0, 1]}
          tickFormatter={(v) => `${Math.round(v * 100)}%`}
          tickLine={false}
          axisLine={false}
          tick={AXIS}
          width={36}
        />
        <Tooltip content={<ChartTooltip fmt={(v: number) => `${Math.round(v * 100)}%`} />} />
        <Line
          type="monotone"
          dataKey="accuracy"
          name="accuracy"
          stroke="var(--series-1)"
          strokeWidth={2}
          dot={{ r: 3, fill: "var(--series-1)" }}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}

// Label source split (rule / ML / correction) → categorical slots, legend + labels.
const SOURCE_COLOR: Record<string, string> = {
  rule: "var(--series-1)",
  ml: "var(--series-2)",
  correction: "var(--status-good)",
  fallback: "var(--series-3)",
};

export function SourceSplit({ data }: { data: Record<string, number> }) {
  const entries = Object.entries(data);
  const total = entries.reduce((s, [, v]) => s + v, 0) || 1;
  return (
    <div>
      <div className="flex h-4 w-full overflow-hidden rounded-full bg-surface-2">
        {entries.map(([k, v]) => (
          <div
            key={k}
            style={{ width: `${(v / total) * 100}%`, background: SOURCE_COLOR[k] ?? "var(--series-3)" }}
            className="h-full"
            title={`${k}: ${v}`}
          />
        ))}
      </div>
      <div className="mt-3 flex flex-wrap gap-x-4 gap-y-1 text-xs text-ink-2">
        {entries.map(([k, v]) => (
          <span key={k} className="flex items-center gap-1.5">
            <span
              className="inline-block h-2.5 w-2.5 rounded-sm"
              style={{ background: SOURCE_COLOR[k] ?? "var(--series-3)" }}
            />
            <span className="capitalize">{k}</span>
            <span className="tabular-nums text-muted">{Math.round((v / total) * 100)}%</span>
          </span>
        ))}
      </div>
    </div>
  );
}
