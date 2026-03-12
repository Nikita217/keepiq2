import { Card } from "../components/Card";
import { EventItem, ReminderItem } from "../types";

export function EventsPage({ events, reminders }: { events: EventItem[]; reminders: ReminderItem[] }) {
  return (
    <div className="pageGrid">
      <Card title="События" meta="концерты, брони, встречи">
        <ul className="listClean">
          {events.map((event) => <li key={event.id}>{event.title} {event.starts_at ? `• ${new Date(event.starts_at).toLocaleString()}` : ""}</li>)}
        </ul>
      </Card>
      <Card title="Напоминания" meta="все активные напоминания">
        <ul className="listClean">
          {reminders.map((reminder) => <li key={reminder.id}>{reminder.title} • {reminder.status}</li>)}
        </ul>
      </Card>
    </div>
  );
}
