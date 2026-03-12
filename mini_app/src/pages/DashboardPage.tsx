import { Card } from "../components/Card";
import { DashboardResponse } from "../types";

export function DashboardPage({ data }: { data: DashboardResponse | null }) {
  if (!data) return <div className="empty">Загрузка обзора…</div>;
  return (
    <div className="pageGrid">
      <Card title="Сегодня" meta="что сейчас в фокусе">
        <div className="metricRow">
          <div><strong>{data.today.tasks}</strong><span>задач</span></div>
          <div><strong>{data.today.reminders}</strong><span>напоминаний</span></div>
          <div><strong>{data.today.events}</strong><span>событий</span></div>
        </div>
      </Card>
      <Card title="Сводка" meta="порядок без бюрократии">
        <ul className="listClean">
          <li>Входящих на разборе: {data.counters.inbox}</li>
          <li>Просрочено: {data.counters.overdue}</li>
          <li>Нужно ответить позже: {data.counters.reply_later}</li>
          <li>Заметок: {data.counters.notes}</li>
          <li>Списков: {data.counters.lists}</li>
        </ul>
      </Card>
      <Card title="Скоро" meta="ближайшие события">
        <ul className="listClean">
          {data.soon_events.map((event) => <li key={event.id}>{event.title} {event.starts_at ? `• ${new Date(event.starts_at).toLocaleString()}` : ""}</li>)}
        </ul>
      </Card>
      <Card title="Ждут разбора" meta="ничего не потеряется">
        <ul className="listClean">
          {data.pending_inbox.map((item) => <li key={item.id}>{item.summary ?? "Без описания"} • {item.proposed_type ?? "не определено"}</li>)}
        </ul>
      </Card>
    </div>
  );
}
