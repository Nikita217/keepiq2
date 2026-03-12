import {
  DashboardResponse,
  EventItem,
  IncomingItem,
  ListEntity,
  NoteItem,
  ReminderItem,
  ReplyLaterItem,
  SavedItem,
  SearchResult,
  TaskItem,
} from "./types";
import { getInitData, getTelegramUserId, isInsideTelegram } from "./telegram";

const API_URL = (import.meta.env.VITE_API_URL ?? "http://localhost:8000").replace(/\/$/, "");

function buildHeaders(): HeadersInit {
  const initData = getInitData();
  if (initData) {
    return { "X-Telegram-Init-Data": initData };
  }

  const telegramUserId = getTelegramUserId();
  if (telegramUserId) {
    return { "X-Telegram-User-Id": String(telegramUserId) };
  }

  return { "X-Telegram-User-Id": "1" };
}

function buildErrorMessage(response: Response, body: string): string {
  if (response.status === 401) {
    return isInsideTelegram()
      ? "Mini App did not pass Telegram authentication. Reopen it from the bot menu or /start button."
      : "This session is not authenticated. Open the app from Telegram or use local dev fallback.";
  }
  return `API error ${response.status}: ${body || response.statusText}`;
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
    const body = await response.text();
    throw new Error(buildErrorMessage(response, body));
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