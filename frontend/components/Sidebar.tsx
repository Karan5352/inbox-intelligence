"use client";

import { useQuery } from "@tanstack/react-query";
import { Inbox, BarChart3, Zap, ShieldCheck, Settings } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { api } from "@/lib/api";
import { ThemeToggle } from "./ThemeToggle";

const NAV = [
  { href: "/", label: "Inbox", icon: Inbox },
  { href: "/insights", label: "Insights", icon: BarChart3 },
  { href: "/automations", label: "Automations", icon: Zap },
  { href: "/settings", label: "Settings", icon: Settings },
];

// Turn the raw backend id into something a person can read.
function modelLabel(backend: string): string {
  if (backend === "hashing-fallback") return "on-device keyword embeddings";
  const name = backend.split("/").pop() ?? backend;
  return `a local ${name} model`;
}

export function Sidebar() {
  const pathname = usePathname();
  const { data: health } = useQuery({ queryKey: ["health"], queryFn: api.health });
  const { data: learning } = useQuery({ queryKey: ["learning"], queryFn: api.learningStatus });

  return (
    <aside className="flex w-60 shrink-0 flex-col border-r border-hairline bg-surface px-3 py-4">
      <div className="px-2 pb-5">
        <div className="flex items-center gap-2">
          <div className="grid h-8 w-8 place-items-center rounded-lg bg-accent text-white">
            <Inbox size={18} />
          </div>
          <div className="leading-tight">
            <div className="text-sm font-semibold">Inbox Intelligence</div>
            <div className="text-[11px] text-muted">sorts your mail on-device</div>
          </div>
        </div>
      </div>

      <nav className="flex flex-col gap-1">
        {NAV.map(({ href, label, icon: Icon }) => {
          const active = pathname === href;
          return (
            <Link
              key={href}
              href={href}
              className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors ${
                active ? "bg-accent-soft font-medium text-accent" : "text-ink-2 hover:bg-surface-2"
              }`}
            >
              <Icon size={17} />
              {label}
            </Link>
          );
        })}
      </nav>

      <div className="mt-auto flex flex-col gap-2 pt-4">
        {health && (
          <Link
            href="/settings"
            className="block rounded-lg border border-hairline p-3 text-[11px] hover:bg-surface-2"
          >
            <div className="mb-2 flex items-center gap-1.5 font-medium text-ink-2">
              <ShieldCheck size={13} className="text-[var(--status-good)]" />
              {health.demo_mode ? "Sample data" : "Gmail (read-only)"}
            </div>
            <p className="text-muted">
              {health.demo_mode
                ? "Synthetic emails. Tap to use your own inbox."
                : "Reading your inbox over IMAP. Read-only, nothing is changed."}
            </p>
            <div className="mt-2 border-t border-hairline pt-2 text-muted">
              Sorted locally by <span className="text-ink-2">{modelLabel(health.embedding_backend)}</span>.
            </div>
            {learning && (
              <div className="mt-2 border-t border-hairline pt-2 text-muted">
                Compares against {learning.classifier_examples} labelled examples:{" "}
                {learning.from_prototypes} built-in, {learning.from_inbox} from this inbox,{" "}
                {learning.corrections} your corrections.
              </div>
            )}
          </Link>
        )}

        <ThemeToggle />
      </div>
    </aside>
  );
}
