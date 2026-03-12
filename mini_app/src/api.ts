import { DashboardResponse, EventItem, IncomingItem, ListEntity, NoteItem, ReminderItem, ReplyLaterItem, SavedItem, SearchResult, TaskItem } from "./types";
import { getInitData } from "./telegram";

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

function buildHeaders(): HeadersInit {
  const initData = getInitData();
  return initData ? { "X-Telegram-Init-Data": initData } : { "X-Telegram-User-Id": "1" };
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...buildHeaders(),
      ...(init?.headers ?? {}),
    },
  });
  if (!response.ok) {
    throw new Error(`API error: ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export const api = {
  dashboard: () => request<DashboardResponse>("/dashboard"),
  inbox: () => request<IncomingItem[]>("/inbox"),
  tasks: () => request<TaskItem[]>("/tasks"),
  events: () => request<{ events: EventItem[]; reminders: ReminderItem[] }>("/events"),
  lists: () => request<ListEntity[]>("/lists"),
  notes: () => request<{ notes: NoteItem[]; reply_later: ReplyLaterItem[]; saved: SavedItem[] }>("/notes"),
  search: (q: string) => request<{ items: SearchResult[] }>("/search", { method: "POST", body: JSON.stringify({ q }) }),
  digests: () => request<{ morning: { title: string; lines: string[] }; evening: { title: string; lines: string[] } }>("/settings/digests"),
  updateInbox: (id: string, payload: Record<string, unknown>) => request<IncomingItem>(`/inbox/${id}`, { method: "PATCH", body: JSON.stringify(payload) }),
  updateTask: (id: string, payload: Record<string, unknown>) => request<TaskItem>(`/tasks/${id}`, { method: "PATCH", body: JSON.stringify(payload) }),
};
