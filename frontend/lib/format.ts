export function relativeTime(iso: string): string {
  const then = new Date(iso).getTime();
  const diff = Date.now() - then;
  const mins = Math.round(diff / 60000);
  if (mins < 1) return "now";
  if (mins < 60) return `${mins}m`;
  const hrs = Math.round(mins / 60);
  if (hrs < 24) return `${hrs}h`;
  const days = Math.round(hrs / 24);
  if (days < 7) return `${days}d`;
  return new Date(iso).toLocaleDateString(undefined, { month: "short", day: "numeric" });
}

export function initials(name: string, fallback: string): string {
  const src = name?.trim() || fallback;
  const parts = src.split(/[\s@.]+/).filter(Boolean);
  return (parts[0]?.[0] ?? "?").toUpperCase() + (parts[1]?.[0] ?? "").toUpperCase();
}

export function pct(x: number): string {
  return `${Math.round(x * 100)}%`;
}

const SOURCE_LABELS: Record<string, string> = {
  rule: "Rule",
  ml: "ML",
  correction: "You",
  fallback: "-",
};

export function sourceLabel(source: string): string {
  return SOURCE_LABELS[source] ?? source;
}
