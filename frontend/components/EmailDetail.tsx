"use client";

import { useQuery } from "@tanstack/react-query";
import { Info, Loader2, X } from "lucide-react";
import { CategoryChip, ConfidenceMeter, SourceBadge } from "@/components/CategoryChip";
import { CorrectionMenu } from "@/components/CorrectionMenu";
import { api } from "@/lib/api";
import { relativeTime } from "@/lib/format";
import type { Category } from "@/lib/types";

export function EmailDetail({
  id,
  categories,
  onClose,
  onCorrect,
  correcting,
}: {
  id: number;
  categories: Category[];
  onClose: () => void;
  onCorrect: (slug: string) => void;
  correcting: boolean;
}) {
  const { data: email, isLoading } = useQuery({
    queryKey: ["email", id],
    queryFn: () => api.email(id),
  });

  return (
    <aside className="flex w-[420px] shrink-0 flex-col border-l border-hairline bg-surface">
      <div className="flex items-center justify-between border-b border-hairline px-4 py-3">
        <span className="text-sm font-medium text-muted">Message</span>
        <button onClick={onClose} className="rounded-md p-1 text-muted hover:bg-surface-2" aria-label="Close">
          <X size={16} />
        </button>
      </div>

      {isLoading || !email ? (
        <div className="grid flex-1 place-items-center">
          <Loader2 className="animate-spin text-muted" />
        </div>
      ) : (
        <div className="min-h-0 flex-1 overflow-auto p-5 thin-scroll">
          <h2 className="text-base font-semibold leading-snug">{email.subject}</h2>
          <div className="mt-2 text-sm text-ink-2">
            <div className="font-medium">{email.sender_name || email.sender}</div>
            <div className="text-xs text-muted">{email.sender}</div>
            <div className="mt-0.5 text-xs text-muted">{relativeTime(email.received_at)}</div>
          </div>

          {/* Categorization explanation card */}
          <div className="mt-4 rounded-xl border border-hairline bg-plane p-3">
            <div className="flex items-center justify-between">
              <CategoryChip slug={email.category} size="md" />
              <CorrectionMenu current={email.category} categories={categories} onPick={onCorrect} />
            </div>
            <div className="mt-3 flex items-center gap-2">
              <SourceBadge source={email.category_source} />
              <ConfidenceMeter value={email.confidence} />
              {correcting && <Loader2 size={13} className="animate-spin text-accent" />}
            </div>
            <div className="mt-2 flex items-start gap-1.5 text-xs text-muted">
              <Info size={13} className="mt-0.5 shrink-0" />
              <span>{email.reason}</span>
            </div>
            {email.secondary.length > 0 && (
              <div className="mt-3 flex flex-wrap items-center gap-1.5 border-t border-hairline pt-3">
                <span className="text-xs text-muted">Also fits:</span>
                {email.secondary.map((s) => (
                  <CategoryChip key={s} slug={s} />
                ))}
              </div>
            )}
          </div>

          {email.labels.length > 0 && (
            <div className="mt-3 flex flex-wrap gap-1.5">
              {email.labels.map((l) => (
                <span key={l} className="rounded-md bg-surface-2 px-2 py-0.5 text-[11px] text-ink-2">
                  {l}
                </span>
              ))}
            </div>
          )}

          <div className="mt-5 whitespace-pre-wrap text-sm leading-relaxed text-ink-2">
            {email.body}
          </div>
        </div>
      )}
    </aside>
  );
}
