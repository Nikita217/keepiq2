import { startTransition, useMemo, useState } from "react";

import { api } from "./api";
import { BottomNav } from "./components/BottomNav";
import { DetailSheet } from "./components/DetailSheet";
import { EmptyState } from "./components/EmptyState";
import { useKeepIQData } from "./hooks/useKeepIQData";
import { useTodayOrder } from "./hooks/useTodayOrder";
import { CalendarPage } from "./pages/CalendarPage";
import { InboxPage } from "./pages/InboxPage";
import { LibraryPage } from "./pages/LibraryPage";
import { SearchPage } from "./pages/SearchPage";
import { TodayPage } from "./pages/TodayPage";
import { AppTab, DetailDraft, DetailEntity, IncomingItem } from "./types";
import { getTelegramFirstName } from "./telegram";
import { formatDayLabel, mergeDateAndTime, withTime } from "./utils/date";
import {
  buildCalendarEntries,
  buildCompletedTodayGroup,
  buildInboxSummary,
  buildLibraryItems,
  buildTodayGroups,
  canConvert,
  countOverdue,
  groupInbox,
  resolveSearchResult,
} from "./utils/models";

export function App() {
  const [tab, setTab] = useState<AppTab>("today");
  const [selectedEntity, setSelectedEntity] = useState<DetailEntity | null>(null);
  const [arrangeMode, setArrangeMode] = useState(false);
  const [isMutating, setIsMutating] = useState(false);
  const [mutationError, setMutationError] = useState<string | null>(null);
  const {
    inbox,
    tasks,
    events,
    reminders,
    lists,
    notes,
    replyLater,
    saved,
    searchQuery,
    setSearchQuery,
    searchResults,
    isLoading,
    error,
    refresh,
  } = useKeepIQData();

  const todayGroupsBase = useMemo(
    () => buildTodayGroups(tasks, reminders, events, replyLater, new Map<string, number>()),
    [tasks, reminders, events, replyLater],
  );
  const todayKeys = useMemo(() => todayGroupsBase.flatMap((group) => group.items.map((item) => item.key)), [todayGroupsBase]);
  const { orderMap, moveUp, moveDown } = useTodayOrder(todayKeys);
  const todayGroups = useMemo(
    () => buildTodayGroups(tasks, reminders, events, replyLater, orderMap),
    [tasks, reminders, events, replyLater, orderMap],
  );
  const completedTodayGroup = useMemo(
    () => buildCompletedTodayGroup(tasks, reminders, events, replyLater),
    [tasks, reminders, events, replyLater],
  );
  const todayItems = useMemo(
    () => [...todayGroups, ...(completedTodayGroup ? [completedTodayGroup] : [])].flatMap((group) => group.items),
    [todayGroups, completedTodayGroup],
  );
  const todayItemsByKey = useMemo(() => new Map(todayItems.map((item) => [item.key, item.detail])), [todayItems]);
  const calendarEntries = useMemo(() => buildCalendarEntries(tasks, reminders, events, replyLater), [tasks, reminders, events, replyLater]);
  const libraryItems = useMemo(() => buildLibraryItems(lists, notes, saved), [lists, notes, saved]);
  const inboxGroups = useMemo(() => groupInbox(inbox), [inbox]);
  const overdueCount = countOverdue(todayGroups);
  const pendingInboxCount = buildInboxSummary(inbox);
  const dayLabel = formatDayLabel(new Date());
  const userName = getTelegramFirstName();
  const title = userName ? `${userName}, вот ваш день` : "Вот ваш день";
  const subtitle = `${dayLabel}. Сначала всё, что важно на сегодня, а выполненное и входящее остаются под рукой, но не мешают.`;

  async function mutate(action: () => Promise<void>) {
    setMutationError(null);
    setIsMutating(true);
    try {
      await action();
      await refresh();
      setSelectedEntity(null);
    } catch (mutationFailure) {
      setMutationError(mutationFailure instanceof Error ? mutationFailure.message : "Не удалось выполнить действие");
      throw mutationFailure;
    } finally {
      setIsMutating(false);
    }
  }

  async function completeEntity(entity: DetailEntity) {
    if (entity.kind === "task") {
      await mutate(() => api.updateTask(entity.item.id, { status: "done" }).then(() => undefined));
      return;
    }
    if (entity.kind === "reminder") {
      await mutate(() => api.updateReminder(entity.item.id, { status: "done" }).then(() => undefined));
      return;
    }
    if (entity.kind === "event") {
      await mutate(() => api.updateEvent(entity.item.id, { status: "done" }).then(() => undefined));
      return;
    }
    if (entity.kind === "reply_later") {
      await mutate(() => api.updateReplyLater(entity.item.id, { status: "done" }).then(() => undefined));
    }
  }

  async function deleteEntity(entity: DetailEntity) {
    await mutate(async () => {
      if (entity.kind === "task") {
        await api.deleteTask(entity.item.id);
      } else if (entity.kind === "event") {
        await api.deleteEvent(entity.item.id);
      } else if (entity.kind === "reminder") {
        await api.deleteReminder(entity.item.id);
      } else if (entity.kind === "note") {
        await api.deleteNote(entity.item.id);
      } else if (entity.kind === "reply_later") {
        await api.deleteReplyLater(entity.item.id);
      } else if (entity.kind === "saved") {
        await api.deleteSaved(entity.item.id);
      } else if (entity.kind === "list") {
        await api.deleteList(entity.item.id);
      }
    });
  }

  async function saveEntity(entity: DetailEntity, draft: DetailDraft) {
    const normalizedType = draft.type === "saved" ? "save_only" : draft.type;
    const scheduledAt = mergeDateAndTime(draft.date, draft.time);

    await mutate(async () => {
      if (entity.kind === "incoming") {
        await api.resolveInbox(entity.item.id, {
          target_type: normalizedType,
          title: draft.title,
          description: draft.description || null,
          scheduled_at: scheduledAt,
          kind: draft.kind || null,
          source_url: draft.sourceUrl || null,
          list_items: draft.listItems.map((item) => item.text).filter(Boolean),
          force_confirmation: false,
        });
        return;
      }

      const currentType = entity.kind === "saved" ? "save_only" : entity.kind;
      if (canConvert(entity.kind) && normalizedType !== currentType) {
        await api.convertObject({
          source_type: currentType,
          source_id: entity.item.id,
          target_type: normalizedType,
          title: draft.title,
          description: draft.description,
          scheduled_at: scheduledAt,
          kind: draft.kind,
          source_url: draft.sourceUrl,
          list_items: draft.listItems.map((item) => item.text).filter(Boolean),
        });
        return;
      }

      if (entity.kind === "task") {
        await api.updateTask(entity.item.id, {
          title: draft.title,
          description: draft.description || null,
          due_at: scheduledAt,
          scheduled_for: scheduledAt,
          status: scheduledAt ? (entity.item.status === "done" ? "done" : "scheduled") : "active",
        });
        return;
      }
      if (entity.kind === "event") {
        await api.updateEvent(entity.item.id, {
          title: draft.title,
          description: draft.description || null,
          starts_at: scheduledAt,
        });
        return;
      }
      if (entity.kind === "reminder") {
        await api.updateReminder(entity.item.id, {
          title: draft.title,
          remind_at: scheduledAt,
          remind_on: scheduledAt ? scheduledAt.slice(0, 10) : null,
        });
        return;
      }
      if (entity.kind === "reply_later") {
        await api.updateReplyLater(entity.item.id, {
          title: draft.title,
          conversation_summary: draft.description || null,
          reply_due_at: scheduledAt,
        });
        return;
      }
      if (entity.kind === "note") {
        await api.updateNote(entity.item.id, {
          title: draft.title,
          body: draft.description || null,
          kind: draft.kind || "note",
        });
        return;
      }
      if (entity.kind === "saved") {
        await api.updateSaved(entity.item.id, {
          title: draft.title,
          summary: draft.description || null,
          source_url: draft.sourceUrl || null,
        });
        return;
      }
      if (entity.kind === "list") {
        await api.updateList(entity.item.id, {
          title: draft.title,
          description: draft.description || null,
          kind: draft.kind || "general",
          items: draft.listItems.map((item, index) => ({
            id: item.id,
            text: item.text,
            is_done: item.is_done,
            sort_order: index,
          })),
        });
      }
    });
  }

  async function quickShift(itemKey: string, preset: "evening" | "tomorrow") {
    const entity = todayItemsByKey.get(itemKey);
    if (!entity) {
      return;
    }
    const base = new Date();
    const next = preset === "evening" ? withTime(base, 19, 0) : withTime(new Date(base.getFullYear(), base.getMonth(), base.getDate() + 1), 10, 0);

    await mutate(async () => {
      if (entity.kind === "task") {
        await api.updateTask(entity.item.id, { due_at: next, scheduled_for: next, status: "scheduled" });
      } else if (entity.kind === "reminder") {
        await api.updateReminder(entity.item.id, { remind_at: next, remind_on: next.slice(0, 10) });
      } else if (entity.kind === "event") {
        await api.updateEvent(entity.item.id, { starts_at: next });
      } else if (entity.kind === "reply_later") {
        await api.updateReplyLater(entity.item.id, { reply_due_at: next });
      }
    });
  }

  async function resolveInboxItem(item: IncomingItem, payload: { targetType?: string; suggestedActionId?: number }) {
    await mutate(async () => {
      await api.resolveInbox(item.id, {
        target_type: payload.targetType,
        suggested_action_id: payload.suggestedActionId,
        force_confirmation: false,
      });
    });
  }

  function openTodayItem(itemKey: string) {
    const entity = todayItemsByKey.get(itemKey);
    if (entity) {
      setSelectedEntity(entity);
    }
  }

  function openSearchResult(index: number) {
    const result = searchResults[index];
    if (!result) {
      return;
    }
    const entity = resolveSearchResult(result, { tasks, reminders, events, replyLater, notes, lists, saved, inbox });
    if (entity) {
      setSelectedEntity(entity);
    }
  }

  return (
    <main className="appShell">
      <div className="contentWrap">
        {error ? <section className="errorBanner">{error}</section> : null}
        {mutationError ? <section className="errorBanner">{mutationError}</section> : null}
        {isLoading ? <EmptyState title="Загружаю KeepIQ" text="Собираю ваши объекты в новый today-first интерфейс." /> : null}

        {!isLoading && tab === "today" ? (
          <TodayPage
            title={title}
            subtitle={subtitle}
            groups={todayGroups}
            completedGroup={completedTodayGroup}
            inboxCount={pendingInboxCount}
            overdueCount={overdueCount}
            arrangeMode={arrangeMode}
            onToggleArrange={() => setArrangeMode((current) => !current)}
            onOpenItem={openTodayItem}
            onCompleteItem={(itemKey) => {
              const entity = todayItemsByKey.get(itemKey);
              if (entity) {
                completeEntity(entity).catch(console.error);
              }
            }}
            onQuickShift={(itemKey, preset) => quickShift(itemKey, preset).catch(console.error)}
            onMoveUp={moveUp}
            onMoveDown={moveDown}
          />
        ) : null}

        {!isLoading && tab === "inbox" ? (
          <InboxPage
            urgent={inboxGroups.urgent}
            quiet={inboxGroups.quiet}
            onOpen={(item) => setSelectedEntity({ kind: "incoming", item })}
            onResolve={(item, payload) => resolveInboxItem(item, payload).catch(console.error)}
          />
        ) : null}

        {!isLoading && tab === "calendar" ? (
          <CalendarPage entries={calendarEntries} onOpen={(entry) => setSelectedEntity(entry.detail)} />
        ) : null}

        {!isLoading && tab === "library" ? (
          <LibraryPage items={libraryItems} onOpen={(item) => setSelectedEntity(item.detail)} />
        ) : null}

        {!isLoading && tab === "search" ? (
          <SearchPage
            query={searchQuery}
            onQueryChange={setSearchQuery}
            results={searchResults}
            onOpen={(result) => {
              const index = searchResults.findIndex((item) => item.object_id === result.object_id && item.object_type === result.object_type);
              openSearchResult(index);
            }}
          />
        ) : null}
      </div>

      <BottomNav active={tab} inboxCount={pendingInboxCount} onChange={(nextTab) => startTransition(() => setTab(nextTab))} />
      <DetailSheet
        entity={selectedEntity}
        busy={isMutating}
        onClose={() => setSelectedEntity(null)}
        onSave={(entity, draft) => saveEntity(entity, draft).catch(console.error)}
        onDelete={(entity) => deleteEntity(entity).catch(console.error)}
        onComplete={(entity) => completeEntity(entity).catch(console.error)}
      />
    </main>
  );
}


