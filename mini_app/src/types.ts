export type DashboardResponse = {
  today: { tasks: number; reminders: number; events: number };
  counters: { inbox: number; overdue: number; reply_later: number; notes: number; lists: number };
  soon_events: Array<{ id: string; title: string; starts_at: string | null }>;
  pending_inbox: Array<{ id: string; summary: string | null; proposed_type: string | null; confidence: number | null }>;
};

export type SuggestedAction = {
  label: string;
  action: string | null;
  target_type: string | null;
  scheduled_for: string | null;
  metadata: Record<string, unknown>;
};

export type IncomingEntity = { entity_type: string; value: string; confidence: number | null };

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
  suggested_actions: SuggestedAction[];
  created_at: string;
  entities: IncomingEntity[];
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
  created_at: string;
  updated_at: string;
};

export type EventItem = {
  id: string;
  title: string;
  description: string | null;
  starts_at: string | null;
  ends_at: string | null;
  place_name: string | null;
  address: string | null;
  booking_reference: string | null;
  status: string;
  source_incoming_item_id: string | null;
  created_at: string;
  updated_at: string;
};

export type ReminderItem = {
  id: string;
  title: string;
  status: string;
  remind_at: string | null;
  remind_on: string | null;
  snoozed_until: string | null;
  source_incoming_item_id: string | null;
  task_id: string | null;
  event_id: string | null;
  created_at: string;
  updated_at: string;
};

export type ListItem = { id: string; text: string; is_done: boolean; sort_order: number; created_at: string; updated_at: string };
export type ListEntity = {
  id: string;
  title: string;
  kind: string;
  description: string | null;
  source_incoming_item_id: string | null;
  items: ListItem[];
  created_at: string;
  updated_at: string;
};

export type NoteItem = {
  id: string;
  title: string;
  body: string | null;
  status: string;
  kind: string;
  source_incoming_item_id: string | null;
  created_at: string;
  updated_at: string;
};

export type SavedItem = {
  id: string;
  title: string;
  summary: string | null;
  source_url: string | null;
  source_incoming_item_id: string | null;
  created_at: string;
  updated_at: string;
};

export type ReplyLaterItem = {
  id: string;
  title: string;
  conversation_summary: string | null;
  reply_due_at: string | null;
  status: string;
  suggested_replies: Record<string, string>;
  source_incoming_item_id: string | null;
  created_at: string;
  updated_at: string;
};

export type SearchResult = {
  object_type: string;
  object_id: string;
  title: string;
  snippet: string | null;
  status: string | null;
};

export type AppTab = "today" | "inbox" | "calendar" | "library" | "search";

export type FocusKind = "task" | "reminder" | "event" | "reply_later";
export type LibraryKind = "note" | "list" | "saved";
export type DetailKind = FocusKind | LibraryKind | "incoming";

export type DetailEntity =
  | { kind: "task"; item: TaskItem }
  | { kind: "reminder"; item: ReminderItem }
  | { kind: "event"; item: EventItem }
  | { kind: "reply_later"; item: ReplyLaterItem }
  | { kind: "note"; item: NoteItem }
  | { kind: "list"; item: ListEntity }
  | { kind: "saved"; item: SavedItem }
  | { kind: "incoming"; item: IncomingItem };

export type FocusCardItem = {
  key: string;
  kind: FocusKind;
  title: string;
  description: string | null;
  when: string | null;
  status: string;
  source: string | null;
  badge: string;
  detail: DetailEntity;
  isOverdue: boolean;
};

export type TodayGroup = {
  key: "overdue" | "morning" | "day" | "evening" | "anytime";
  label: string;
  items: FocusCardItem[];
};

export type LibraryFilter = "all" | "list" | "note" | "idea" | "saved";

export type LibraryCardItem = {
  key: string;
  kind: LibraryKind;
  filterKind: LibraryFilter;
  title: string;
  preview: string | null;
  meta: string;
  progress: string | null;
  tags: string[];
  updated_at: string;
  detail: DetailEntity;
};

export type CalendarEntry = {
  key: string;
  kind: FocusKind;
  title: string;
  when: string;
  status: string;
  detail: DetailEntity;
};

export type DetailDraft = {
  title: string;
  description: string;
  date: string;
  time: string;
  type: string;
  kind: string;
  sourceUrl: string;
  status: string;
  listItems: Array<{ id?: string; text: string; is_done: boolean }>;
};

export type AppDataBundle = {
  dashboard: DashboardResponse | null;
  inbox: IncomingItem[];
  tasks: TaskItem[];
  events: EventItem[];
  reminders: ReminderItem[];
  lists: ListEntity[];
  notes: NoteItem[];
  replyLater: ReplyLaterItem[];
  saved: SavedItem[];
};
