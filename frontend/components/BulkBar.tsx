"use client";

import { Archive, CheckCheck, Loader2, Trash2, X } from "lucide-react";

// Appears when emails are selected. Bulk actions preview (dry-run) is handled by
// the caller; this is the control surface.
export function BulkBar({
  count,
  pending,
  onArchive,
  onMarkRead,
  onDelete,
  onClear,
}: {
  count: number;
  pending: boolean;
  onArchive: () => void;
  onMarkRead: () => void;
  onDelete: () => void;
  onClear: () => void;
}) {
  return (
    <div className="flex items-center gap-2 rounded-lg border border-hairline bg-accent-soft px-3 py-2 text-sm">
      <span className="font-medium text-accent">{count} selected</span>
      <div className="mx-1 h-4 w-px bg-hairline" />
      <BulkButton onClick={onArchive} icon={<Archive size={15} />} label="Archive" disabled={pending} />
      <BulkButton onClick={onMarkRead} icon={<CheckCheck size={15} />} label="Mark read" disabled={pending} />
      <BulkButton onClick={onDelete} icon={<Trash2 size={15} />} label="Delete" disabled={pending} />
      {pending && <Loader2 size={15} className="animate-spin text-accent" />}
      <button onClick={onClear} className="ml-auto rounded-md p-1 text-muted hover:bg-surface-2" aria-label="Clear selection">
        <X size={15} />
      </button>
    </div>
  );
}

function BulkButton({
  onClick,
  icon,
  label,
  disabled,
}: {
  onClick: () => void;
  icon: React.ReactNode;
  label: string;
  disabled: boolean;
}) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className="flex items-center gap-1.5 rounded-md px-2 py-1 text-ink-2 hover:bg-surface disabled:opacity-50"
    >
      {icon}
      {label}
    </button>
  );
}
