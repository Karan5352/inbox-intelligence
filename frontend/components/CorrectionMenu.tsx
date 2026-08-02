"use client";

import { Check, ChevronDown } from "lucide-react";
import { useState } from "react";
import { CATEGORY_META } from "@/lib/categories";
import type { Category } from "@/lib/types";

// Dropdown to reassign an email's category - the entry point to the learning loop.
export function CorrectionMenu({
  current,
  categories,
  onPick,
}: {
  current: string;
  categories: Category[];
  onPick: (slug: string) => void;
}) {
  const [open, setOpen] = useState(false);
  const trainable = categories.filter((c) => c.slug !== "uncategorized");

  return (
    <div className="relative">
      <button
        onClick={() => setOpen((v) => !v)}
        onBlur={() => setTimeout(() => setOpen(false), 150)}
        className="flex items-center gap-1 rounded-md border border-hairline px-2 py-1 text-xs text-ink-2 hover:bg-surface-2"
      >
        Recategorize
        <ChevronDown size={13} />
      </button>
      {open && (
        <div className="absolute right-0 z-20 mt-1 max-h-72 w-52 overflow-auto rounded-lg border border-hairline bg-surface p-1 shadow-lg thin-scroll">
          {trainable.map((c) => {
            const Icon = CATEGORY_META[c.slug]?.icon;
            const active = c.slug === current;
            return (
              <button
                key={c.slug}
                onMouseDown={(e) => {
                  e.preventDefault();
                  onPick(c.slug);
                  setOpen(false);
                }}
                className="flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-left text-sm text-ink-2 hover:bg-surface-2"
              >
                {Icon && <Icon size={14} style={{ color: c.color }} />}
                <span className="flex-1 capitalize">{c.slug}</span>
                {active && <Check size={14} className="text-accent" />}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
