"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Loader2, RefreshCw, Search } from "lucide-react";
import { useMemo, useState } from "react";
import { BulkBar } from "@/components/BulkBar";
import { CategoryChip, ConfidenceMeter, SourceBadge } from "@/components/CategoryChip";
import { EmailDetail } from "@/components/EmailDetail";
import { CATEGORY_META, categoryColor } from "@/lib/categories";
import { api } from "@/lib/api";
import { initials, relativeTime } from "@/lib/format";
import type { BulkActionType } from "@/lib/types";

export default function InboxPage() {
  const qc = useQueryClient();
  const [category, setCategory] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [unreadOnly, setUnreadOnly] = useState(false);
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [activeId, setActiveId] = useState<number | null>(null);
  const [confirm, setConfirm] = useState<{ action: BulkActionType; message: string } | null>(null);

  const catQ = useQuery({ queryKey: ["categories"], queryFn: api.categories });
  const emailQ = useQuery({
    queryKey: ["emails", { category, search, unreadOnly }],
    queryFn: () =>
      api.emails({ category, search, unread: unreadOnly ? true : null, limit: 100 }),
  });

  const invalidate = () => {
    for (const k of ["emails", "categories", "insights", "learning"]) {
      qc.invalidateQueries({ queryKey: [k] });
    }
  };

  const correctM = useMutation({
    mutationFn: ({ id, slug }: { id: number; slug: string }) => api.correct(id, slug),
    onSuccess: () => {
      invalidate();
      if (activeId) qc.invalidateQueries({ queryKey: ["email", activeId] });
    },
  });

  const syncM = useMutation({ mutationFn: () => api.sync(), onSuccess: invalidate });

  // Bulk: preview first (dry-run) → confirm → apply. Showcases the safe-by-default design.
  const previewM = useMutation({
    mutationFn: (action: BulkActionType) =>
      api.bulk({ action, email_ids: [...selected], dry_run: true }),
    onSuccess: (res, action) => setConfirm({ action, message: res.message }),
  });
  const applyM = useMutation({
    mutationFn: (action: BulkActionType) =>
      api.bulk({ action, email_ids: [...selected], dry_run: false }),
    onSuccess: () => {
      setSelected(new Set());
      setConfirm(null);
      invalidate();
    },
  });

  const emails = emailQ.data?.items ?? [];
  const allSelected = emails.length > 0 && emails.every((e) => selected.has(e.id));

  function toggle(id: number) {
    setSelected((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  }
  function toggleAll() {
    setSelected(allSelected ? new Set() : new Set(emails.map((e) => e.id)));
  }

  const categories = useMemo(() => catQ.data ?? [], [catQ.data]);
  const bulkPending = previewM.isPending || applyM.isPending;

  return (
    <div className="flex h-screen flex-col">
      {/* Header */}
      <header className="flex items-center gap-3 border-b border-hairline bg-surface px-5 py-3">
        <h1 className="text-lg font-semibold">Inbox</h1>
        <span className="text-sm text-muted">
          {emailQ.data?.total ?? 0} messages
        </span>
        <div className="ml-auto flex items-center gap-2">
          <div className="relative">
            <Search size={15} className="absolute left-2.5 top-2 text-muted" />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search mail…"
              className="w-56 rounded-lg border border-hairline bg-plane py-1.5 pl-8 pr-3 text-sm outline-none focus:border-accent"
            />
          </div>
          <button
            onClick={() => setUnreadOnly((v) => !v)}
            className={`rounded-lg border px-3 py-1.5 text-sm ${
              unreadOnly ? "border-accent bg-accent-soft text-accent" : "border-hairline text-ink-2"
            }`}
          >
            Unread
          </button>
          <button
            onClick={() => syncM.mutate()}
            disabled={syncM.isPending}
            title="Fetch the latest mail from the active source"
            className="flex items-center gap-1.5 rounded-lg border border-hairline px-3 py-1.5 text-sm text-ink-2 hover:bg-surface-2 disabled:opacity-50"
          >
            <RefreshCw size={14} className={syncM.isPending ? "animate-spin" : ""} />
            Sync
          </button>
        </div>
      </header>

      <div className="flex min-h-0 flex-1">
        {/* Category rail */}
        <nav className="w-52 shrink-0 overflow-auto border-r border-hairline bg-surface p-2 thin-scroll">
          <RailItem
            label="All mail"
            active={category === null}
            onClick={() => setCategory(null)}
          />
          {categories
            .filter((c) => c.count > 0)
            .map((c) => {
              const Icon = CATEGORY_META[c.slug]?.icon;
              return (
                <RailItem
                  key={c.slug}
                  label={c.slug}
                  count={c.count}
                  unread={c.unread}
                  color={c.color}
                  icon={Icon ? <Icon size={15} style={{ color: c.color }} /> : null}
                  active={category === c.slug}
                  onClick={() => setCategory(c.slug)}
                />
              );
            })}
        </nav>

        {/* Email list */}
        <section className="flex min-w-0 flex-1 flex-col">
          <div className="flex items-center gap-3 border-b border-hairline px-4 py-2">
            <input
              type="checkbox"
              checked={allSelected}
              onChange={toggleAll}
              className="h-4 w-4 accent-[var(--accent)]"
              aria-label="Select all"
            />
            {selected.size > 0 ? (
              <BulkBar
                count={selected.size}
                pending={bulkPending}
                onArchive={() => previewM.mutate("archive")}
                onMarkRead={() => previewM.mutate("mark_read")}
                onDelete={() => previewM.mutate("delete")}
                onClear={() => setSelected(new Set())}
              />
            ) : (
              <span className="text-xs text-muted">Select messages for bulk actions</span>
            )}
          </div>

          {confirm && (
            <div className="flex items-center gap-3 border-b border-hairline bg-accent-soft px-4 py-2 text-sm">
              <span className="text-ink">{confirm.message}</span>
              <button
                onClick={() => applyM.mutate(confirm.action)}
                className="ml-auto rounded-md bg-accent px-3 py-1 text-xs font-medium text-white"
              >
                Confirm
              </button>
              <button onClick={() => setConfirm(null)} className="text-xs text-muted">
                Cancel
              </button>
            </div>
          )}

          <div className="min-h-0 flex-1 overflow-auto thin-scroll">
            {emailQ.isLoading ? (
              <Centered>
                <Loader2 className="animate-spin text-muted" />
              </Centered>
            ) : emails.length === 0 ? (
              <Centered>
                <div className="flex flex-col items-center gap-3 text-center">
                  <p className="text-sm text-muted">
                    {category || search || unreadOnly
                      ? "No messages match this view."
                      : "Your inbox is empty. Load some mail to get started."}
                  </p>
                  {!category && !search && !unreadOnly && (
                    <button
                      onClick={() => syncM.mutate()}
                      disabled={syncM.isPending}
                      className="flex items-center gap-1.5 rounded-lg bg-accent px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
                    >
                      <RefreshCw size={15} className={syncM.isPending ? "animate-spin" : ""} />
                      {syncM.isPending ? "Loading…" : "Load inbox"}
                    </button>
                  )}
                </div>
              </Centered>
            ) : (
              emails.map((e) => (
                <button
                  key={e.id}
                  onClick={() => setActiveId(e.id)}
                  className={`flex w-full items-center gap-3 border-b border-hairline px-4 py-2.5 text-left hover:bg-surface-2 ${
                    activeId === e.id ? "bg-surface-2" : ""
                  } ${e.is_read ? "" : "bg-[var(--accent-soft)]/30"}`}
                >
                  <input
                    type="checkbox"
                    checked={selected.has(e.id)}
                    onChange={() => toggle(e.id)}
                    onClick={(ev) => ev.stopPropagation()}
                    className="h-4 w-4 accent-[var(--accent)]"
                    aria-label={`Select ${e.subject}`}
                  />
                  <div
                    className="grid h-8 w-8 shrink-0 place-items-center rounded-full text-[11px] font-semibold text-white"
                    style={{ backgroundColor: categoryColor(e.category) }}
                  >
                    {initials(e.sender_name, e.sender)}
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <span className={`truncate text-sm ${e.is_read ? "text-ink-2" : "font-semibold"}`}>
                        {e.sender_name || e.sender}
                      </span>
                      <span className="ml-auto shrink-0 text-[11px] text-muted">
                        {relativeTime(e.received_at)}
                      </span>
                    </div>
                    <div className="truncate text-sm text-ink">{e.subject}</div>
                    <div className="truncate text-xs text-muted">{e.snippet}</div>
                  </div>
                  <div className="flex w-40 shrink-0 flex-col items-end gap-1">
                    <CategoryChip slug={e.category} />
                    <div className="flex items-center gap-1.5">
                      <SourceBadge source={e.category_source} />
                      <ConfidenceMeter value={e.confidence} />
                    </div>
                  </div>
                </button>
              ))
            )}
          </div>
        </section>

        {/* Detail panel */}
        {activeId && (
          <EmailDetail
            id={activeId}
            categories={categories}
            onClose={() => setActiveId(null)}
            onCorrect={(slug) => correctM.mutate({ id: activeId, slug })}
            correcting={correctM.isPending}
          />
        )}
      </div>
    </div>
  );
}

function RailItem({
  label,
  count,
  unread,
  active,
  onClick,
  icon,
}: {
  label: string;
  count?: number;
  unread?: number;
  color?: string;
  active: boolean;
  onClick: () => void;
  icon?: React.ReactNode;
}) {
  return (
    <button
      onClick={onClick}
      className={`flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm capitalize ${
        active ? "bg-accent-soft font-medium text-accent" : "text-ink-2 hover:bg-surface-2"
      }`}
    >
      {icon}
      <span className="flex-1 text-left">{label}</span>
      {unread ? (
        <span className="rounded-full bg-accent px-1.5 text-[10px] font-semibold text-white">
          {unread}
        </span>
      ) : count ? (
        <span className="text-[11px] tabular-nums text-muted">{count}</span>
      ) : null}
    </button>
  );
}

function Centered({ children }: { children: React.ReactNode }) {
  return <div className="grid h-full place-items-center">{children}</div>;
}
