import { startTransition, useDeferredValue, useEffect, useEffectEvent, useState } from "react";

import { api } from "../api";
import { AppDataBundle, SearchResult } from "../types";

const EMPTY_BUNDLE: AppDataBundle = {
  dashboard: null,
  inbox: [],
  tasks: [],
  events: [],
  reminders: [],
  lists: [],
  notes: [],
  replyLater: [],
  saved: [],
};

export function useKeepIQData() {
  const [bundle, setBundle] = useState<AppDataBundle>(EMPTY_BUNDLE);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastSyncAt, setLastSyncAt] = useState<string | null>(null);
  const deferredQuery = useDeferredValue(searchQuery.trim());

  const refresh = useEffectEvent(async () => {
    setError(null);
    setIsRefreshing(true);
    try {
      const [dashboard, inbox, tasks, eventsPayload, lists, notesPayload] = await Promise.all([
        api.dashboard(),
        api.inbox(),
        api.tasks(),
        api.events(),
        api.lists(),
        api.notes(),
      ]);
      startTransition(() => {
        setBundle({
          dashboard,
          inbox,
          tasks,
          events: eventsPayload.events,
          reminders: eventsPayload.reminders,
          lists,
          notes: notesPayload.notes,
          replyLater: notesPayload.reply_later,
          saved: notesPayload.saved,
        });
        setLastSyncAt(new Date().toLocaleTimeString("ru-RU", { hour: "2-digit", minute: "2-digit" }));
      });
    } catch (refreshError) {
      setError(refreshError instanceof Error ? refreshError.message : "Не удалось синхронизировать данные");
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  });

  useEffect(() => {
    refresh().catch(console.error);
  }, [refresh]);

  useEffect(() => {
    if (!deferredQuery) {
      setSearchResults([]);
      return;
    }

    const timeout = window.setTimeout(() => {
      api.search(deferredQuery)
        .then((response) => {
          startTransition(() => {
            setSearchResults(response.items);
          });
        })
        .catch((searchError) => {
          setError(searchError instanceof Error ? searchError.message : "Ошибка поиска");
        });
    }, 200);

    return () => window.clearTimeout(timeout);
  }, [deferredQuery]);

  return {
    ...bundle,
    searchQuery,
    setSearchQuery,
    searchResults,
    isLoading,
    isRefreshing,
    error,
    lastSyncAt,
    refresh,
  };
}
