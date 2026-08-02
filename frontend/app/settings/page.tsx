"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Database, Mail, RefreshCw, ShieldCheck } from "lucide-react";
import { api } from "@/lib/api";

function modelLabel(backend?: string): string {
  if (!backend) return "loading";
  if (backend === "hashing-fallback") return "on-device keyword embeddings (no model download)";
  const name = backend.split("/").pop() ?? backend;
  return `a local ${name} model`;
}

export default function SettingsPage() {
  const qc = useQueryClient();
  const { data: health } = useQuery({ queryKey: ["health"], queryFn: api.health });
  const { data: learning } = useQuery({ queryKey: ["learning"], queryFn: api.learningStatus });
  const refresh = () => {
    for (const k of ["emails", "categories", "insights", "learning"]) {
      qc.invalidateQueries({ queryKey: [k] });
    }
  };
  const syncM = useMutation({ mutationFn: () => api.sync(), onSuccess: refresh });
  const resetM = useMutation({ mutationFn: () => api.sync({ reset: true }), onSuccess: refresh });
  const resortM = useMutation({ mutationFn: () => api.recategorize(), onSuccess: refresh });

  const onGmail = health && !health.demo_mode;
  const busy = syncM.isPending || resetM.isPending;
  const result = resetM.data ?? syncM.data;

  return (
    <div className="h-screen overflow-auto thin-scroll">
      <header className="border-b border-hairline bg-surface px-6 py-4">
        <h1 className="text-lg font-semibold">Settings</h1>
        <p className="text-sm text-muted">What data this is running on, and how to point it at your own.</p>
      </header>

      <div className="mx-auto max-w-2xl space-y-5 p-6">
        {/* Current state */}
        <section className="rounded-xl border border-hairline bg-surface p-5">
          <div className="flex items-start gap-3">
            <div className="grid h-10 w-10 place-items-center rounded-lg bg-accent-soft text-accent">
              {onGmail ? <Mail size={18} /> : <Database size={18} />}
            </div>
            <div className="flex-1">
              <div className="flex items-center gap-2 text-sm font-semibold">
                {onGmail ? "Connected to Gmail" : "Running on sample data"}
                <ShieldCheck size={14} className="text-[var(--status-good)]" />
              </div>
              <p className="mt-1 text-sm text-muted">
                {onGmail
                  ? "Reading your inbox over IMAP, read-only. Nothing is deleted, moved, or marked."
                  : "A few hundred synthetic emails. No real inbox is connected, so this is safe to show anyone."}
              </p>
              <p className="mt-2 text-xs text-muted">
                Sorted locally by {modelLabel(health?.embedding_backend)}. Nothing is sent to an
                outside service.
              </p>
              {learning && (
                <p className="mt-1 text-xs text-muted">
                  It sorts by similarity to {learning.classifier_examples} labelled examples:{" "}
                  {learning.from_prototypes} built-in prototypes, {learning.from_inbox} auto-labelled
                  from this inbox by the rules, and {learning.corrections} of your own corrections.
                </p>
              )}
            </div>
            <div className="flex flex-col gap-2">
              <button
                onClick={() => syncM.mutate()}
                disabled={busy}
                className="flex items-center justify-center gap-1.5 rounded-lg border border-hairline px-3 py-1.5 text-sm text-ink-2 hover:bg-surface-2 disabled:opacity-50"
              >
                <RefreshCw size={14} className={syncM.isPending ? "animate-spin" : ""} />
                {syncM.isPending ? "Syncing…" : "Sync new mail"}
              </button>
              <button
                onClick={() => resetM.mutate()}
                disabled={busy}
                title="Clear the inbox and reload it from the current source"
                className="rounded-lg px-3 py-1.5 text-xs text-muted hover:bg-surface-2 disabled:opacity-50"
              >
                {resetM.isPending ? "Resetting…" : "Reset and reload"}
              </button>
            </div>
          </div>
          <p className="mt-3 text-xs text-muted">
            Every number in Insights is counted from the emails loaded here, so it reflects
            whichever source is active. Sync adds new mail; reset clears first, so the stats show
            only this source.
          </p>
          {result && (
            <p className="mt-2 rounded-lg bg-accent-soft px-3 py-2 text-xs text-accent">
              {result.reset ? "Reset and pulled" : "Pulled"} {result.added} email(s) from{" "}
              {result.source}.
            </p>
          )}
          {(syncM.isError || resetM.isError) && (
            <p className="mt-2 rounded-lg px-3 py-2 text-xs text-[var(--status-critical)]">
              {((syncM.error ?? resetM.error) as Error).message}
            </p>
          )}
        </section>

        {/* Learning */}
        <section className="rounded-xl border border-hairline bg-surface p-5">
          <div className="flex items-start justify-between gap-3">
            <div>
              <h2 className="text-sm font-semibold">Apply what it has learned</h2>
              <p className="mt-1 text-sm text-muted">
                Correcting an email teaches the model instantly, and new mail is sorted with what it
                knows. The emails already in your inbox keep their labels until you re-sort. Re-sorting
                also lets it learn from the mail the rules were confident about, so it adapts to how
                your inbox actually looks.
              </p>
            </div>
            <button
              onClick={() => resortM.mutate()}
              disabled={resortM.isPending}
              className="shrink-0 rounded-lg border border-hairline px-3 py-1.5 text-sm text-ink-2 hover:bg-surface-2 disabled:opacity-50"
            >
              {resortM.isPending ? "Re-sorting…" : "Re-sort inbox"}
            </button>
          </div>
          {resortM.data && (
            <p className="mt-3 rounded-lg bg-accent-soft px-3 py-2 text-xs text-accent">
              Re-sorted {resortM.data.recategorized} email(s). Your corrections were kept as-is.
            </p>
          )}
        </section>

        {/* Connect your own inbox */}
        <section className="rounded-xl border border-hairline bg-surface p-5">
          <h2 className="text-sm font-semibold">Use your own Gmail</h2>
          <p className="mt-1 text-sm text-muted">
            The connection is read-only and uses a Gmail app password, not your real password, so it
            is revocable and limited in scope. Run these once on the machine hosting the backend.
          </p>
          <ol className="mt-4 space-y-3 text-sm">
            <Step n={1} title="Turn on 2-Step Verification">
              Google account, then Security. App passwords are only available once 2-Step
              Verification is on.
            </Step>
            <Step n={2} title="Create an app password">
              Google account, Security, App passwords. Pick &quot;Mail&quot; and copy the 16-character
              code.
            </Step>
            <Step n={3} title="Add it to backend/.env">
              <pre className="mt-1 overflow-x-auto rounded-lg bg-plane p-3 text-xs text-ink-2">
{`DEMO_MODE=false
GMAIL_ADDRESS=you@gmail.com
GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx`}
              </pre>
            </Step>
            <Step n={4} title="Restart the backend, then Reset and reload">
              Restart <code className="rounded bg-plane px-1">make api</code>. It pulls your inbox on
              startup; use Reset and reload above to clear the sample data so the stats are only
              yours.
            </Step>
          </ol>
          <p className="mt-4 text-xs text-muted">
            To go back to sample data, set <code className="rounded bg-plane px-1">DEMO_MODE=true</code>{" "}
            and restart.
          </p>
        </section>
      </div>
    </div>
  );
}

function Step({ n, title, children }: { n: number; title: string; children: React.ReactNode }) {
  return (
    <li className="flex gap-3">
      <span className="grid h-6 w-6 shrink-0 place-items-center rounded-full bg-surface-2 text-xs font-semibold text-ink-2">
        {n}
      </span>
      <div>
        <div className="font-medium">{title}</div>
        <div className="text-muted">{children}</div>
      </div>
    </li>
  );
}
