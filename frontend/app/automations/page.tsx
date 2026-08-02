"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Play, Plus, Trash2, Zap } from "lucide-react";
import { useState } from "react";
import { CATEGORY_META } from "@/lib/categories";
import { api } from "@/lib/api";
import type { AutomationAction, AutomationCondition, AutomationRunResult } from "@/lib/types";

const CATEGORY_SLUGS = Object.keys(CATEGORY_META).filter((s) => s !== "uncategorized");

export default function AutomationsPage() {
  const qc = useQueryClient();
  const { data: automations = [] } = useQuery({ queryKey: ["automations"], queryFn: api.automations });
  const [runResult, setRunResult] = useState<AutomationRunResult | null>(null);

  const [name, setName] = useState("");
  const [condition, setCondition] = useState<AutomationCondition>({
    field: "category",
    op: "equals",
    value: "promotions",
  });
  const [action, setAction] = useState<AutomationAction>({ type: "archive", value: "" });

  const invalidate = () => {
    qc.invalidateQueries({ queryKey: ["automations"] });
    qc.invalidateQueries({ queryKey: ["emails"] });
    qc.invalidateQueries({ queryKey: ["insights"] });
  };

  const createM = useMutation({
    mutationFn: () =>
      api.createAutomation({ name, enabled: true, priority: 100, condition, action }),
    onSuccess: () => {
      setName("");
      invalidate();
    },
  });
  const deleteM = useMutation({
    mutationFn: (id: number) => api.deleteAutomation(id),
    onSuccess: invalidate,
  });
  const runM = useMutation({
    mutationFn: (dryRun: boolean) => api.runAutomations(dryRun),
    onSuccess: (res, dryRun) => {
      setRunResult(res);
      if (!dryRun) invalidate();
    },
  });

  return (
    <div className="h-screen overflow-auto thin-scroll">
      <header className="flex items-center gap-3 border-b border-hairline bg-surface px-6 py-4">
        <div>
          <h1 className="text-lg font-semibold">Automations</h1>
          <p className="text-sm text-muted">Rules that run against your mail. Set a condition, pick what happens.</p>
        </div>
        <div className="ml-auto flex gap-2">
          <button
            onClick={() => runM.mutate(true)}
            className="rounded-lg border border-hairline px-3 py-1.5 text-sm text-ink-2 hover:bg-surface-2"
          >
            Preview run
          </button>
          <button
            onClick={() => runM.mutate(false)}
            className="flex items-center gap-1.5 rounded-lg bg-accent px-3 py-1.5 text-sm font-medium text-white"
          >
            <Play size={15} /> Run now
          </button>
        </div>
      </header>

      <div className="mx-auto max-w-3xl p-6">
        {runResult && (
          <div className="mb-5 rounded-xl border border-hairline bg-accent-soft p-4 text-sm">
            <div className="font-medium text-accent">
              {runResult.dry_run ? "Preview" : "Applied"}: {runResult.matched} match(es)
              {!runResult.dry_run && `, ${runResult.applied} applied`}
            </div>
            <div className="mt-1 text-xs text-ink-2">
              {Object.entries(runResult.by_automation)
                .map(([k, v]) => `${k}: ${v}`)
                .join(" · ") || "no rules matched"}
            </div>
          </div>
        )}

        {/* Builder */}
        <section className="rounded-xl border border-hairline bg-surface p-4">
          <h2 className="mb-3 text-sm font-semibold">New automation</h2>
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Rule name (e.g. Archive promotions)"
            className="mb-3 w-full rounded-lg border border-hairline bg-plane px-3 py-2 text-sm outline-none focus:border-accent"
          />
          <div className="flex flex-wrap items-center gap-2 text-sm">
            <span className="text-muted">When</span>
            <Select
              value={condition.field}
              onChange={(v) => setCondition({ ...condition, field: v as AutomationCondition["field"] })}
              options={["category", "sender", "subject", "unread"]}
            />
            <Select
              value={condition.op}
              onChange={(v) => setCondition({ ...condition, op: v as AutomationCondition["op"] })}
              options={condition.field === "unread" ? ["is_true"] : ["equals", "contains"]}
            />
            {condition.field !== "unread" &&
              (condition.field === "category" ? (
                <Select
                  value={condition.value}
                  onChange={(v) => setCondition({ ...condition, value: v })}
                  options={CATEGORY_SLUGS}
                />
              ) : (
                <input
                  value={condition.value}
                  onChange={(e) => setCondition({ ...condition, value: e.target.value })}
                  placeholder="value"
                  className="rounded-lg border border-hairline bg-plane px-2 py-1.5 text-sm outline-none focus:border-accent"
                />
              ))}
          </div>
          <div className="mt-2 flex flex-wrap items-center gap-2 text-sm">
            <span className="text-muted">Then</span>
            <Select
              value={action.type}
              onChange={(v) => setAction({ ...action, type: v as AutomationAction["type"] })}
              options={["archive", "mark_read", "label", "recategorize"]}
            />
            {(action.type === "label" || action.type === "recategorize") &&
              (action.type === "recategorize" ? (
                <Select
                  value={action.value || CATEGORY_SLUGS[0]}
                  onChange={(v) => setAction({ ...action, value: v })}
                  options={CATEGORY_SLUGS}
                />
              ) : (
                <input
                  value={action.value}
                  onChange={(e) => setAction({ ...action, value: e.target.value })}
                  placeholder="label"
                  className="rounded-lg border border-hairline bg-plane px-2 py-1.5 text-sm outline-none focus:border-accent"
                />
              ))}
          </div>
          <button
            onClick={() => createM.mutate()}
            disabled={!name || createM.isPending}
            className="mt-4 flex items-center gap-1.5 rounded-lg bg-accent px-3 py-2 text-sm font-medium text-white disabled:opacity-50"
          >
            <Plus size={15} /> Add automation
          </button>
        </section>

        {/* List */}
        <section className="mt-5 space-y-2">
          {automations.length === 0 && (
            <p className="rounded-xl border border-dashed border-hairline p-8 text-center text-sm text-muted">
              No automations yet. Create one above.
            </p>
          )}
          {automations.map((a) => (
            <div
              key={a.id}
              className="flex items-center gap-3 rounded-xl border border-hairline bg-surface p-3"
            >
              <div className="grid h-9 w-9 place-items-center rounded-lg bg-accent-soft text-accent">
                <Zap size={17} />
              </div>
              <div className="min-w-0 flex-1">
                <div className="text-sm font-medium">{a.name}</div>
                <div className="text-xs text-muted">
                  When <b className="text-ink-2">{a.condition.field}</b> {a.condition.op}{" "}
                  <b className="text-ink-2">{a.condition.value || "true"}</b>, then {a.action.type}
                  {a.action.value ? ` "${a.action.value}"` : ""}
                </div>
              </div>
              <span className="text-xs text-muted">ran {a.run_count}×</span>
              <button
                onClick={() => deleteM.mutate(a.id)}
                className="rounded-md p-1.5 text-muted hover:bg-surface-2 hover:text-[var(--status-critical)]"
                aria-label="Delete automation"
              >
                <Trash2 size={15} />
              </button>
            </div>
          ))}
        </section>
      </div>
    </div>
  );
}

function Select({
  value,
  onChange,
  options,
}: {
  value: string;
  onChange: (v: string) => void;
  options: string[];
}) {
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="rounded-lg border border-hairline bg-plane px-2 py-1.5 text-sm capitalize outline-none focus:border-accent"
    >
      {options.map((o) => (
        <option key={o} value={o}>
          {o}
        </option>
      ))}
    </select>
  );
}
