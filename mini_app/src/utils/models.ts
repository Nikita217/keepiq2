import {
  CalendarEntry,
  DetailEntity,
  EventItem,
  FocusCardItem,
  FocusKind,
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
import { dayKey, endOfDay, parseDate, startOfDay } from "./date";

const ACTIVE_TASK_STATUSES = new Set(["active", "scheduled", "waiting_reply", "inbox"]);
const ACTIVE_EVENT_STATUSES = new Set(["upcoming"]);
const ACTIVE_REMINDER_STATUSES = new Set(["active", "snoozed"]);
const ACTIVE_REPLY_STATUSES = new Set(["open"]);

export function getTypeLabel(kind: string): string {
  return {
    task: "Дело",
    reminder: "Напоминание",
    event: "Событие",
    reply_later: "Ответить",
    note: "Заметка",
    list: "Список",
    saved: "Сохранённое",
    incoming: "Входящее",
    save_only: "Сохранённое",
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
      }];
    }),
  ];

  const groups: TodayGroup[] = [
    { key: "overdue", label: "Просрочено", items: [] },
    { key: "morning", label: "Утро", items: [] },
    { key: "day", label: "День", items: [] },
    { key: "evening", label: "Вечер", items: [] },
    { key: "anytime", label: "Без времени", items: [] },
  ];

  const sorted = items.sort((left, right) => {
    const leftRank = order.get(left.key) ?? Number.MAX_SAFE_INTEGER;
    const rightRank = order.get(right.key) ?? Number.MAX_SAFE_INTEGER;
    if (leftRank !== rightRank) {
      return leftRank - rightRank;
    }
    const leftDate = parseDate(left.when)?.getTime() ?? Number.MAX_SAFE_INTEGER;
    const rightDate = parseDate(right.when)?.getTime() ?? Number.MAX_SAFE_INTEGER;
    if (leftDate !== rightDate) {
      return leftDate - rightDate;
    }
    return left.title.localeCompare(right.title, "ru");
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
      meta: `${list.items.length} пунктов`,
      progress: list.items.length ? `${done}/${list.items.length} выполнено` : null,
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
    meta: note.kind === "idea" ? "Идея" : "Заметка",
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
    meta: item.source_url ? "Ссылка и материал" : "Сохранённый материал",
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
  return items.filter((item) => item.needs_confirmation).length;
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
    return entity.item.summary ?? entity.item.proposed_type ?? "Входящее";
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
      { value: "inbox_review", label: "Оставить во входящих" },
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

  return [
    { value: kind, label: getTypeLabel(kind) },
  ];
}

export function canConvert(kind: DetailEntity["kind"]): boolean {
  return ["task", "reminder", "event", "reply_later", "note", "incoming"].includes(kind);
}
