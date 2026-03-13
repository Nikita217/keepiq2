import {
  CalendarEntry,
  DetailEntity,
  EventItem,
  FocusCardItem,
  IncomingItem,
  LibraryCardItem,
  ListEntity,
  NoteItem,
  ReminderItem,
  ReplyLaterItem,
  SavedItem,
  SearchResult,
  TaskItem,
  TodayGroup,
} from "../types";
import { dayKey, endOfDay, isSameDay, parseDate, startOfDay } from "./date";

const ACTIVE_TASK_STATUSES = new Set(["active", "scheduled", "waiting_reply", "inbox"]);
const ACTIVE_EVENT_STATUSES = new Set(["upcoming"]);
const ACTIVE_REMINDER_STATUSES = new Set(["active", "snoozed"]);
const ACTIVE_REPLY_STATUSES = new Set(["open"]);
const COMPLETED_TASK_STATUSES = new Set(["done"]);
const COMPLETED_EVENT_STATUSES = new Set(["done"]);
const COMPLETED_REMINDER_STATUSES = new Set(["done"]);
const COMPLETED_REPLY_STATUSES = new Set(["done"]);

function sortFocusItems(left: FocusCardItem, right: FocusCardItem): number {
  const leftDate = parseDate(left.when)?.getTime() ?? Number.MAX_SAFE_INTEGER;
  const rightDate = parseDate(right.when)?.getTime() ?? Number.MAX_SAFE_INTEGER;
  if (leftDate !== rightDate) {
    return leftDate - rightDate;
  }
  return left.title.localeCompare(right.title, "ru");
}

function getUpdatedAt(detail: DetailEntity): string | null {
  switch (detail.kind) {
    case "task":
    case "reminder":
    case "event":
    case "reply_later":
    case "note":
    case "list":
    case "saved":
      return detail.item.updated_at;
    default:
      return detail.item.created_at;
  }
}

export function getTypeLabel(kind: string): string {
  return {
    task: "\u0414\u0435\u043b\u043e",
    reminder: "\u041d\u0430\u043f\u043e\u043c\u0438\u043d\u0430\u043d\u0438\u0435",
    event: "\u0421\u043e\u0431\u044b\u0442\u0438\u0435",
    reply_later: "\u041e\u0442\u0432\u0435\u0442\u0438\u0442\u044c",
    note: "\u0417\u0430\u043c\u0435\u0442\u043a\u0430",
    list: "\u0421\u043f\u0438\u0441\u043e\u043a",
    saved: "\u0421\u043e\u0445\u0440\u0430\u043d\u0451\u043d\u043d\u043e\u0435",
    incoming: "\u0412\u0445\u043e\u0434\u044f\u0449\u0435\u0435",
    save_only: "\u0421\u043e\u0445\u0440\u0430\u043d\u0451\u043d\u043d\u043e\u0435",
  }[kind] ?? kind;
}

export function buildTodayGroups(
  tasks: TaskItem[],
  reminders: ReminderItem[],
  events: EventItem[],
  replyLater: ReplyLaterItem[],
  order: Map<string, number>,
): TodayGroup[] {
  const now = new Date();
  const todayStart = startOfDay(now);
  const todayEnd = endOfDay(now);
  const items: FocusCardItem[] = [
    ...tasks.filter((task) => ACTIVE_TASK_STATUSES.has(task.status)).flatMap((task) => {
      const when = task.due_at ?? task.scheduled_for;
      const at = parseDate(when);
      if (at && at > todayEnd) {
        return [];
      }
      return [{
        key: `task:${task.id}`,
        kind: "task" as const,
        title: task.title,
        description: task.description,
        when,
        status: task.status,
        source: task.source_incoming_item_id,
        badge: getTypeLabel("task"),
        detail: { kind: "task", item: task } satisfies DetailEntity,
        isOverdue: Boolean(at && at < todayStart),
        isCompleted: false,
      }];
    }),
    ...reminders.filter((reminder) => ACTIVE_REMINDER_STATUSES.has(reminder.status)).flatMap((reminder) => {
      const when = reminder.remind_at ?? reminder.remind_on;
      const at = parseDate(when);
      if (!at || at > todayEnd) {
        return [];
      }
      return [{
        key: `reminder:${reminder.id}`,
        kind: "reminder" as const,
        title: reminder.title,
        description: null,
        when,
        status: reminder.status,
        source: reminder.source_incoming_item_id,
        badge: getTypeLabel("reminder"),
        detail: { kind: "reminder", item: reminder } satisfies DetailEntity,
        isOverdue: at < todayStart,
        isCompleted: false,
      }];
    }),
    ...events.filter((event) => ACTIVE_EVENT_STATUSES.has(event.status)).flatMap((event) => {
      const at = parseDate(event.starts_at);
      if (!at || at > todayEnd) {
        return [];
      }
      return [{
        key: `event:${event.id}`,
        kind: "event" as const,
        title: event.title,
        description: event.description,
        when: event.starts_at,
        status: event.status,
        source: event.source_incoming_item_id,
        badge: getTypeLabel("event"),
        detail: { kind: "event", item: event } satisfies DetailEntity,
        isOverdue: at < todayStart,
        isCompleted: false,
      }];
    }),
    ...replyLater.filter((item) => ACTIVE_REPLY_STATUSES.has(item.status)).flatMap((item) => {
      const at = parseDate(item.reply_due_at);
      if (!at || at > todayEnd) {
        return [];
      }
      return [{
        key: `reply_later:${item.id}`,
        kind: "reply_later" as const,
        title: item.title,
        description: item.conversation_summary,
        when: item.reply_due_at,
        status: item.status,
        source: item.source_incoming_item_id,
        badge: getTypeLabel("reply_later"),
        detail: { kind: "reply_later", item } satisfies DetailEntity,
        isOverdue: at < todayStart,
        isCompleted: false,
      }];
    }),
  ];

  const groups: TodayGroup[] = [
    { key: "overdue", label: "\u041f\u0440\u043e\u0441\u0440\u043e\u0447\u0435\u043d\u043e", items: [] },
    { key: "morning", label: "\u0423\u0442\u0440\u043e", items: [] },
    { key: "day", label: "\u0414\u0435\u043d\u044c", items: [] },
    { key: "evening", label: "\u0412\u0435\u0447\u0435\u0440", items: [] },
    { key: "anytime", label: "\u0411\u0435\u0437 \u0432\u0440\u0435\u043c\u0435\u043d\u0438", items: [] },
  ];

  const sorted = [...items].sort((left, right) => {
    const leftRank = order.get(left.key) ?? Number.MAX_SAFE_INTEGER;
    const rightRank = order.get(right.key) ?? Number.MAX_SAFE_INTEGER;
    if (leftRank !== rightRank) {
      return leftRank - rightRank;
    }
    return sortFocusItems(left, right);
  });

  for (const item of sorted) {
    const date = parseDate(item.when);
    if (item.isOverdue) {
      groups[0].items.push(item);
      continue;
    }
    if (!date) {
      groups[4].items.push(item);
      continue;
    }
    const hour = date.getHours();
    if (hour < 12) {
      groups[1].items.push(item);
    } else if (hour < 18) {
      groups[2].items.push(item);
    } else {
      groups[3].items.push(item);
    }
  }

  return groups.filter((group) => group.items.length > 0);
}

export function buildCompletedTodayGroup(
  tasks: TaskItem[],
  reminders: ReminderItem[],
  events: EventItem[],
  replyLater: ReplyLaterItem[],
): TodayGroup | null {
  const today = new Date();
  const completedItems: FocusCardItem[] = [
    ...tasks.filter((task) => COMPLETED_TASK_STATUSES.has(task.status) && isSameDay(new Date(task.updated_at), today)).map((task) => ({
      key: `task:${task.id}`,
      kind: "task" as const,
      title: task.title,
      description: task.description,
      when: task.due_at ?? task.scheduled_for ?? task.updated_at,
      status: task.status,
      source: task.source_incoming_item_id,
      badge: getTypeLabel("task"),
      detail: { kind: "task", item: task } satisfies DetailEntity,
      isOverdue: false,
      isCompleted: true,
    })),
    ...reminders.filter((item) => COMPLETED_REMINDER_STATUSES.has(item.status) && isSameDay(new Date(item.updated_at), today)).map((item) => ({
      key: `reminder:${item.id}`,
      kind: "reminder" as const,
      title: item.title,
      description: null,
      when: item.remind_at ?? item.remind_on ?? item.updated_at,
      status: item.status,
      source: item.source_incoming_item_id,
      badge: getTypeLabel("reminder"),
      detail: { kind: "reminder", item } satisfies DetailEntity,
      isOverdue: false,
      isCompleted: true,
    })),
    ...events.filter((event) => COMPLETED_EVENT_STATUSES.has(event.status) && isSameDay(new Date(event.updated_at), today)).map((event) => ({
      key: `event:${event.id}`,
      kind: "event" as const,
      title: event.title,
      description: event.description,
      when: event.starts_at ?? event.updated_at,
      status: event.status,
      source: event.source_incoming_item_id,
      badge: getTypeLabel("event"),
      detail: { kind: "event", item: event } satisfies DetailEntity,
      isOverdue: false,
      isCompleted: true,
    })),
    ...replyLater.filter((item) => COMPLETED_REPLY_STATUSES.has(item.status) && isSameDay(new Date(item.updated_at), today)).map((item) => ({
      key: `reply_later:${item.id}`,
      kind: "reply_later" as const,
      title: item.title,
      description: item.conversation_summary,
      when: item.reply_due_at ?? item.updated_at,
      status: item.status,
      source: item.source_incoming_item_id,
      badge: getTypeLabel("reply_later"),
      detail: { kind: "reply_later", item } satisfies DetailEntity,
      isOverdue: false,
      isCompleted: true,
    })),
  ].sort((left, right) => {
    const leftUpdated = parseDate(getUpdatedAt(left.detail))?.getTime() ?? 0;
    const rightUpdated = parseDate(getUpdatedAt(right.detail))?.getTime() ?? 0;
    return rightUpdated - leftUpdated;
  });

  if (completedItems.length === 0) {
    return null;
  }

  return {
    key: "completed",
    label: "\u0412\u044b\u043f\u043e\u043b\u043d\u0435\u043d\u043e \u0441\u0435\u0433\u043e\u0434\u043d\u044f",
    items: completedItems,
  };
}

export function countOverdue(groups: TodayGroup[]): number {
  return groups.find((group) => group.key === "overdue")?.items.length ?? 0;
}

export function buildCalendarEntries(
  tasks: TaskItem[],
  reminders: ReminderItem[],
  events: EventItem[],
  replyLater: ReplyLaterItem[],
): CalendarEntry[] {
  const taskEntries: CalendarEntry[] = tasks
    .filter((task) => ACTIVE_TASK_STATUSES.has(task.status) && (task.due_at ?? task.scheduled_for))
    .map((task) => ({
      key: `task:${task.id}`,
      kind: "task",
      title: task.title,
      when: task.due_at ?? task.scheduled_for ?? "",
      status: task.status,
      detail: { kind: "task", item: task },
    }));

  const reminderEntries: CalendarEntry[] = reminders
    .filter((item) => ACTIVE_REMINDER_STATUSES.has(item.status) && (item.remind_at ?? item.remind_on))
    .map((item) => ({
      key: `reminder:${item.id}`,
      kind: "reminder",
      title: item.title,
      when: item.remind_at ?? item.remind_on ?? "",
      status: item.status,
      detail: { kind: "reminder", item },
    }));

  const eventEntries: CalendarEntry[] = events
    .filter((event) => ACTIVE_EVENT_STATUSES.has(event.status) && event.starts_at)
    .map((event) => ({
      key: `event:${event.id}`,
      kind: "event",
      title: event.title,
      when: event.starts_at ?? "",
      status: event.status,
      detail: { kind: "event", item: event },
    }));

  const replyEntries: CalendarEntry[] = replyLater
    .filter((item) => ACTIVE_REPLY_STATUSES.has(item.status) && item.reply_due_at)
    .map((item) => ({
      key: `reply_later:${item.id}`,
      kind: "reply_later",
      title: item.title,
      when: item.reply_due_at ?? "",
      status: item.status,
      detail: { kind: "reply_later", item },
    }));

  return [...taskEntries, ...reminderEntries, ...eventEntries, ...replyEntries].sort(
    (left, right) => new Date(left.when).getTime() - new Date(right.when).getTime(),
  );
}

export function buildLibraryItems(lists: ListEntity[], notes: NoteItem[], saved: SavedItem[]): LibraryCardItem[] {
  const listCards: LibraryCardItem[] = lists.map((list) => {
    const done = list.items.filter((item) => item.is_done).length;
    return {
      key: `list:${list.id}`,
      kind: "list",
      filterKind: "list",
      title: list.title,
      preview: list.description,
      meta: `${list.items.length} \u043f\u0443\u043d\u043a\u0442\u043e\u0432`,
      progress: list.items.length ? `${done}/${list.items.length} \u0432\u044b\u043f\u043e\u043b\u043d\u0435\u043d\u043e` : null,
      tags: [list.kind],
      updated_at: list.updated_at,
      detail: { kind: "list", item: list },
    };
  });

  const noteCards: LibraryCardItem[] = notes.map((note) => ({
    key: `note:${note.id}`,
    kind: "note",
    filterKind: note.kind === "idea" ? "idea" : "note",
    title: note.title,
    preview: note.body,
    meta: note.kind === "idea" ? "\u0418\u0434\u0435\u044f" : "\u0417\u0430\u043c\u0435\u0442\u043a\u0430",
    progress: null,
    tags: [note.kind],
    updated_at: note.updated_at,
    detail: { kind: "note", item: note },
  }));

  const savedCards: LibraryCardItem[] = saved.map((item) => ({
    key: `saved:${item.id}`,
    kind: "saved",
    filterKind: "saved",
    title: item.title,
    preview: item.summary ?? item.source_url,
    meta: item.source_url ? "\u0421\u0441\u044b\u043b\u043a\u0430 \u0438 \u043c\u0430\u0442\u0435\u0440\u0438\u0430\u043b" : "\u0421\u043e\u0445\u0440\u0430\u043d\u0451\u043d\u043d\u044b\u0439 \u043c\u0430\u0442\u0435\u0440\u0438\u0430\u043b",
    progress: null,
    tags: item.source_url ? ["link"] : ["saved"],
    updated_at: item.updated_at,
    detail: { kind: "saved", item },
  }));

  return [...listCards, ...noteCards, ...savedCards].sort(
    (left, right) => new Date(right.updated_at).getTime() - new Date(left.updated_at).getTime(),
  );
}

export function groupInbox(items: IncomingItem[]): { urgent: IncomingItem[]; quiet: IncomingItem[] } {
  const urgent = items.filter((item) => item.needs_confirmation || (item.confidence ?? 0) < 0.75);
  const quiet = items.filter((item) => !urgent.some((urgentItem) => urgentItem.id === item.id));
  return { urgent, quiet };
}

export function buildInboxSummary(items: IncomingItem[]): number {
  return items.length;
}

export function resolveSearchResult(result: SearchResult, bundle: {
  tasks: TaskItem[];
  reminders: ReminderItem[];
  events: EventItem[];
  replyLater: ReplyLaterItem[];
  notes: NoteItem[];
  lists: ListEntity[];
  saved: SavedItem[];
  inbox: IncomingItem[];
}): DetailEntity | null {
  if (result.object_type === "task") {
    const item = bundle.tasks.find((entry) => entry.id === result.object_id);
    return item ? { kind: "task", item } : null;
  }
  if (result.object_type === "reminder") {
    const item = bundle.reminders.find((entry) => entry.id === result.object_id);
    return item ? { kind: "reminder", item } : null;
  }
  if (result.object_type === "event") {
    const item = bundle.events.find((entry) => entry.id === result.object_id);
    return item ? { kind: "event", item } : null;
  }
  if (result.object_type === "reply_later") {
    const item = bundle.replyLater.find((entry) => entry.id === result.object_id);
    return item ? { kind: "reply_later", item } : null;
  }
  if (result.object_type === "note") {
    const item = bundle.notes.find((entry) => entry.id === result.object_id);
    return item ? { kind: "note", item } : null;
  }
  if (result.object_type === "list") {
    const item = bundle.lists.find((entry) => entry.id === result.object_id);
    return item ? { kind: "list", item } : null;
  }
  if (result.object_type === "save_only") {
    const item = bundle.saved.find((entry) => entry.id === result.object_id);
    return item ? { kind: "saved", item } : null;
  }
  if (result.object_type === "incoming") {
    const item = bundle.inbox.find((entry) => entry.id === result.object_id);
    return item ? { kind: "incoming", item } : null;
  }
  return null;
}

export function getEntityTitle(entity: DetailEntity): string {
  if (entity.kind === "incoming") {
    return entity.item.summary ?? entity.item.proposed_type ?? "\u0412\u0445\u043e\u0434\u044f\u0449\u0435\u0435";
  }
  return entity.item.title;
}

export function calendarMap(entries: CalendarEntry[]): Map<string, CalendarEntry[]> {
  const map = new Map<string, CalendarEntry[]>();
  for (const entry of entries) {
    const key = dayKey(new Date(entry.when));
    const existing = map.get(key) ?? [];
    existing.push(entry);
    existing.sort((left, right) => new Date(left.when).getTime() - new Date(right.when).getTime());
    map.set(key, existing);
  }
  return map;
}

export function availableTypeOptions(kind: DetailEntity["kind"]): Array<{ value: string; label: string }> {
  if (kind === "incoming") {
    return [
      { value: "task", label: getTypeLabel("task") },
      { value: "reminder", label: getTypeLabel("reminder") },
      { value: "event", label: getTypeLabel("event") },
      { value: "note", label: getTypeLabel("note") },
      { value: "list", label: getTypeLabel("list") },
      { value: "reply_later", label: getTypeLabel("reply_later") },
      { value: "save_only", label: getTypeLabel("save_only") },
      { value: "inbox_review", label: "\u041e\u0441\u0442\u0430\u0432\u0438\u0442\u044c \u0432\u043e \u0432\u0445\u043e\u0434\u044f\u0449\u0438\u0445" },
    ];
  }

  if (["task", "reminder", "event", "reply_later", "note"].includes(kind)) {
    return ["task", "reminder", "event", "reply_later", "note", "list", "save_only"].map((value) => ({
      value,
      label: getTypeLabel(value),
    }));
  }

  if (kind === "saved") {
    return ["saved", "note", "task", "reminder"].map((value) => ({
      value,
      label: value === "saved" ? getTypeLabel("saved") : getTypeLabel(value),
    }));
  }

  return [{ value: kind, label: getTypeLabel(kind) }];
}

export function canConvert(kind: DetailEntity["kind"]): boolean {
  return ["task", "reminder", "event", "reply_later", "note", "incoming", "saved"].includes(kind);
}