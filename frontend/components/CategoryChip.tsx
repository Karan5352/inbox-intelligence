import { CATEGORY_META, categoryColor } from "@/lib/categories";

export function CategoryChip({ slug, size = "sm" }: { slug: string; size?: "sm" | "md" }) {
  const meta = CATEGORY_META[slug];
  const Icon = meta?.icon;
  const color = categoryColor(slug);
  const pad = size === "md" ? "px-2.5 py-1 text-xs" : "px-2 py-0.5 text-[11px]";
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full font-medium capitalize ${pad}`}
      style={{ color, backgroundColor: `${color}1a` }}
    >
      {Icon && <Icon size={size === "md" ? 13 : 11} />}
      {slug}
    </span>
  );
}

// Source of the label: rule / ml / correction / fallback. Text + color, never color alone.
export function SourceBadge({ source }: { source: string }) {
  const map: Record<string, { label: string; className: string }> = {
    rule: { label: "Rule", className: "text-ink-2 bg-surface-2" },
    ml: { label: "ML", className: "text-accent bg-accent-soft" },
    correction: { label: "You", className: "text-white bg-[var(--status-good)]" },
    fallback: { label: "-", className: "text-muted bg-surface-2" },
  };
  const s = map[source] ?? map.fallback;
  return (
    <span className={`rounded px-1.5 py-0.5 text-[10px] font-semibold ${s.className}`}>{s.label}</span>
  );
}

export function ConfidenceMeter({ value }: { value: number }) {
  const width = Math.round(value * 100);
  return (
    <span className="inline-flex items-center gap-1.5" title={`confidence ${width}%`}>
      <span className="h-1.5 w-12 overflow-hidden rounded-full bg-surface-2">
        <span
          className="block h-full rounded-full bg-accent"
          style={{ width: `${Math.max(width, 4)}%` }}
        />
      </span>
      <span className="text-[10px] tabular-nums text-muted">{width}%</span>
    </span>
  );
}
