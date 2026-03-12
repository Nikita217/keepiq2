export type DashboardResponse = {
  today: { tasks: number; reminders: number; events: number };
  counters: { inbox: number; overdue: number; reply_later: number; notes: number; lists: number };
  soon_events: Array<{ id: string; title: string; starts_at: string | null }>;
  pending_inbox: Array<{ id: string; summary: string | null; proposed_type: string | null; confidence: number | null }>;
};

export type IncomingItem = {
  id: string;
  incoming_type: string;
  parse_status: string;
  summary: string | null;
  proposed_type: string | null;
  confidence: number | null;
  needs_confirmation: boolean;
  raw_text: string | null;
  transcript_text: string | null;
  ocr_text: string | null;
  source_url: string | null;
  assistant_response: string | null;
  clarification_question: string | null;
  resolved_object_type: string | null;
  created_at: string;
  entities: Array<{ entity_type: string; value: string; confidence: number | null }>;
};

export type TaskItem = {
  id: string;
  title: string;
  description: string | null;
  status: string;
  due_at: string | null;
  scheduled_for: string | null;
  priority: string;
  source_incoming_item_id: string | null;
};

export type EventItem = {
  id: string;
  title: string;
  description: string | null;
  starts_at: string | null;
  place_name: string | null;
  address: string | null;
  booking_reference: string | null;
  status: string;
  source_incoming_item_id: string | null;
};

export type ReminderItem = {
  id: string;
  title: string;
  status: string;
  remind_at: string | null;
  remind_on: string | null;
  snoozed_until: string | null;
  source_incoming_item_id: string | null;
};

export type ListItem = { id: string; text: string; is_done: boolean; sort_order: number };
export type ListEntity = { id: string; title: string; kind: string; description: string | null; items: ListItem[] };
export type NoteItem = { id: string; title: string; body: string | null; kind: string };
export type SavedItem = { id: string; title: string; summary: string | null; source_url: string | null };
export type ReplyLaterItem = { id: string; title: string; conversation_summary: string | null; reply_due_at: string | null; status: string; suggested_replies: Record<string, string> };
export type SearchResult = { object_type: string; object_id: string; title: string; snippet: string | null; status: string | null };
