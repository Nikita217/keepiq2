import { Card } from "../components/Card";
import { DashboardResponse } from "../types";

export function DashboardPage({ data }: { data: DashboardResponse | null }) {
  if (!data) return <div className="empty">Загрузка обзора…</div>;
  return (
    <div className="pageGrid">
      <Card title="Сегодня" meta="что сейчас происходит">
        <div className="metricRow">
          <div><strong>{data.today.tasks}</strong><span>tasks</span></div>
          <div><strong>{data.today.reminders}</strong><span>reminders</span></div>
          <div><strong>{data.today.events}</strong><span>events</span></div>
        </div>
      </Card>
      <Card title="Счётчики" meta="порядок без бюрократии">
        <ul className="listClean">
          <li>Inbox: {data.counters.inbox}</li>
          <li>Overdue: {data.counters.overdue}</li>
          <li>Reply later: {data.counters.reply_later}</li>
          <li>Notes: {data.counters.notes}</li>
          <li>Lists: {data.counters.lists}</li>
        </ul>
      </Card>
      <Card title="Скоро" meta="ближайшие события">
        <ul className="listClean">
          {data.soon_events.map((event) => <li key={event.id}>{event.title} {event.starts_at ? `• ${new Date(event.starts_at).toLocaleString()}` : ""}</li>)}
        </ul>
      </Card>
      <Card title="Ждут разбора" meta="ничего не потеряется">
        <ul className="listClean">
          {data.pending_inbox.map((item) => <li key={item.id}>{item.summary ?? "Без summary"} • {item.proposed_type ?? "unknown"}</li>)}
        </ul>
      </Card>
    </div>
  );
}
