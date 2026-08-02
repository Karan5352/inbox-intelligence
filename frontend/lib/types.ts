// TypeScript mirrors of the backend pydantic schemas.

export interface Email {
  id: number;
  message_id: string;
  sender: string;
  sender_name: string;
  subject: string;
  snippet: string;
  received_at: string;
  is_read: boolean;
  is_archived: boolean;
  labels: string[];
  category: string;
  category_source: "rule" | "ml" | "fallback" | "correction";
  confidence: number;
  reason: string;
  secondary: string[];
}

export interface EmailDetail extends Email {
  body: string;
}

export interface EmailPage {
  items: Email[];
  total: number;
  limit: number;
  offset: number;
}

export interface Category {
  slug: string;
  name: string;
  color: string;
  icon: string;
  description: string;
  count: number;
  unread: number;
}

export interface LearningStatus {
  classifier_examples: number;
  from_prototypes: number;
  from_inbox: number;
  corrections: number;
  embedding_backend: string;
  latest_accuracy: number | null;
}

export type BulkActionType =
  | "archive"
  | "unarchive"
  | "mark_read"
  | "mark_unread"
  | "label"
  | "delete"
  | "recategorize";

export interface BulkActionResult {
  action: string;
  dry_run: boolean;
  affected: number;
  email_ids: number[];
  message: string;
}

export interface AutomationCondition {
  field: "category" | "sender" | "subject" | "unread";
  op: "equals" | "contains" | "is_true";
  value: string;
}

export interface AutomationAction {
  type: "label" | "archive" | "mark_read" | "recategorize";
  value: string;
}

export interface Automation {
  id: number;
  name: string;
  enabled: boolean;
  priority: number;
  condition: AutomationCondition;
  action: AutomationAction;
  run_count: number;
  created_at: string;
}

export interface AutomationRunResult {
  dry_run: boolean;
  matched: number;
  applied: number;
  by_automation: Record<string, number>;
}

export interface Insights {
  total_emails: number;
  unread: number;
  archived: number;
  needs_reply: number;
  by_category: {
    category: string;
    name: string;
    color: string;
    count: number;
    unread: number;
  }[];
  top_senders: { sender: string; sender_name: string; count: number }[];
  volume_by_day: { date: string; count: number }[];
  accuracy_trend: {
    label: string;
    accuracy: number;
    num_corrections: number;
    created_at: string;
  }[];
  rule_vs_ml: Record<string, number>;
}

export interface Health {
  status: string;
  app: string;
  demo_mode: boolean;
  embedding_backend: string;
}
