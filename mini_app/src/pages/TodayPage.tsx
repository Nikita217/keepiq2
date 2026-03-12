import { Card } from "../components/Card";
import { EventItem, IncomingItem, ReminderItem, TaskItem } from "../types";

export function TodayPage({ tasks, reminders, events, inbox }: { tasks: TaskItem[]; reminders: ReminderItem[]; events: EventItem[]; inbox: IncomingItem[] }) {
  return (
    <div className="pageGrid">
      <Card title="Tasks" meta="что нужно довести сегодня">
        <ul className="listClean">{tasks.slice(0, 8).map((task) => <li key={task.id}>{task.title} • {task.status}</li>)}</ul>
      </Card>
      <Card title="Reminders" meta="что всплывёт сегодня">
        <ul className="listClean">{reminders.slice(0, 8).map((reminder) => <li key={reminder.id}>{reminder.title}</li>)}</ul>
      </Card>
      <Card title="Events" meta="привязано ко времени">
        <ul className="listClean">{events.slice(0, 8).map((event) => <li key={event.id}>{event.title} {event.starts_at ? `• ${new Date(event.starts_at).toLocaleString()}` : ""}</li>)}</ul>
      </Card>
      <Card title="Need attention" meta="inbox + reply later">
        <ul className="listClean">{inbox.filter((item) => item.needs_confirmation).slice(0, 8).map((item) => <li key={item.id}>{item.summary ?? item.proposed_type}</li>)}</ul>
      </Card>
    </div>
  );
}
