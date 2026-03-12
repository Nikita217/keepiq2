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
import { getInitData, getTelegramUserId, isInsideTelegram, isLocalDevHost } from "./telegram";

const API_URL = (import.meta.env.VITE_API_URL ?? "http://localhost:8000").replace(/\/$/, "");

function buildHeaders(init?: RequestInit): HeadersInit {
  const headers: Record<string, string> = {};
  const providedHeaders = new Headers(init?.headers ?? {});

  providedHeaders.forEach((value, key) => {
    headers[key] = value;
  });

  const hasBody = init?.body !== undefined && init?.body !== null;
  if (hasBody && !headers["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }

  const initData = getInitData();
  if (initData) {
    headers["X-Telegram-Init-Data"] = initData;
    return headers;
  }

  const telegramUserId = getTelegramUserId();
  if (telegramUserId) {
    headers["X-Telegram-User-Id"] = String(telegramUserId);
    return headers;
  }

  if (isLocalDevHost()) {
    headers["X-Telegram-User-Id"] = "1";
  }

  return headers;
}

function buildErrorMessage(response: Response, body: string): string {
  if (response.status === 401) {
    return isInsideTelegram()
      ? "Mini App did not pass Telegram authentication. Reopen it from the bot menu or /start button."
      : "This session is not authenticated. Open the app from Telegram. Local fallback works only on localhost.";
  }
  return `API error ${response.status}: ${body || response.statusText}`;
}

function buildNetworkErrorMessage(path: string, error: unknown): string {
  const hint = isInsideTelegram()
    ? "Open the Mini App again from Telegram and make sure the backend allows requests from the Pages domain."
    : "Check VITE_API_URL and backend CORS settings for the current Pages domain.";
  const details = error instanceof Error && error.message ? error.message : "Network request failed";
  return `Failed to fetch ${path}. ${hint} Details: ${details}`;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_URL}${path}`, {
      ...init,
      headers: buildHeaders(init),
    });
  } catch (error) {
    throw new Error(buildNetworkErrorMessage(path, error));
  }

  if (!response.ok) {
    const body = await response.text();
    throw new Error(buildErrorMessage(response, body));
  }
  if (response.status === 204) {
    return undefined as T;
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
  resolveInbox: (id: string, payload: Record<string, unknown>) => request<IncomingItem>(`/inbox/${id}/resolve`, { method: "POST", body: JSON.stringify(payload) }),
  updateTask: (id: string, payload: Record<string, unknown>) => request<TaskItem>(`/tasks/${id}`, { method: "PATCH", body: JSON.stringify(payload) }),
  deleteTask: (id: string) => request<void>(`/tasks/${id}`, { method: "DELETE" }),
};
