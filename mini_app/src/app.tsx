import { useEffect, useState } from "react";

import { api } from "./api";
import { NavBar, TabKey } from "./components/NavBar";
import { DashboardPage } from "./pages/DashboardPage";
import { EventsPage } from "./pages/EventsPage";
import { InboxPage } from "./pages/InboxPage";
import { ListsPage } from "./pages/ListsPage";
import { NotesPage } from "./pages/NotesPage";
import { SearchPage } from "./pages/SearchPage";
import { TasksPage } from "./pages/TasksPage";
import { TodayPage } from "./pages/TodayPage";
import { CalendarPage } from "./pages/CalendarPage";
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

export function App() {
  const [tab, setTab] = useState<TabKey>("dashboard");
  const [dashboard, setDashboard] = useState<DashboardResponse | null>(null);
  const [inbox, setInbox] = useState<IncomingItem[]>([]);
  const [tasks, setTasks] = useState<TaskItem[]>([]);
  const [events, setEvents] = useState<EventItem[]>([]);
  const [reminders, setReminders] = useState<ReminderItem[]>([]);
  const [lists, setLists] = useState<ListEntity[]>([]);
  const [notes, setNotes] = useState<NoteItem[]>([]);
  const [replyLater, setReplyLater] = useState<ReplyLaterItem[]>([]);
  const [saved, setSaved] = useState<SavedItem[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastSyncAt, setLastSyncAt] = useState<string | null>(null);

  async function refresh() {
    setIsLoading(true);
    setError(null);
    try {
      const [dashboardData, inboxData, tasksData, eventsData, listsData, notesData] = await Promise.all([
        api.dashboard(),
        api.inbox(),
        api.tasks(),
        api.events(),
        api.lists(),
        api.notes(),
      ]);
      setDashboard(dashboardData);
      setInbox(inboxData);
      setTasks(tasksData);
      setEvents(eventsData.events);
      setReminders(eventsData.reminders);
      setLists(listsData);
      setNotes(notesData.notes);
      setReplyLater(notesData.reply_later);
      setSaved(notesData.saved);
      setLastSyncAt(new Date().toLocaleTimeString());
    } catch (refreshError) {
      setError(refreshError instanceof Error ? refreshError.message : "Unknown error");
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    refresh().catch(console.error);
  }, []);

  useEffect(() => {
    if (!searchQuery.trim()) {
      setSearchResults([]);
      return;
    }
    const timeout = setTimeout(() => {
      api.search(searchQuery).then((response) => setSearchResults(response.items)).catch((searchError) => {
        setError(searchError instanceof Error ? searchError.message : "Search failed");
      });
    }, 250);
    return () => clearTimeout(timeout);
  }, [searchQuery]);

  return (
    <main className="shell">
      <NavBar active={tab} onChange={setTab} aside={<button className="ghost" onClick={() => refresh()}>Refresh</button>} />
      {error ? <section className="errorBanner">{error}</section> : null}
      {lastSyncAt ? <p className="syncHint">Last sync: {lastSyncAt}</p> : null}
      {isLoading && !dashboard ? <div className="empty">Loading KeepIQ...</div> : null}
      {tab === "dashboard" ? <DashboardPage data={dashboard} /> : null}
      {tab === "inbox" ? <InboxPage items={inbox} refresh={refresh} /> : null}
      {tab === "today" ? <TodayPage tasks={tasks} reminders={reminders} events={events} inbox={inbox} /> : null}
      {tab === "tasks" ? <TasksPage tasks={tasks} refresh={refresh} /> : null}
      {tab === "calendar" ? <CalendarPage tasks={tasks} reminders={reminders} events={events} /> : null}
      {tab === "events" ? <EventsPage events={events} reminders={reminders} /> : null}
      {tab === "lists" ? <ListsPage lists={lists} /> : null}
      {tab === "notes" ? <NotesPage notes={notes} replyLater={replyLater} saved={saved} /> : null}
      {tab === "search" ? <SearchPage query={searchQuery} onQueryChange={setSearchQuery} results={searchResults} /> : null}
    </main>
  );
}
