import { useEffect, useState } from "react";

import { Card } from "../components/Card";
import { EventItem, ReminderItem, TaskItem } from "../types";

type AgendaEntry = {
  id: string;
  title: string;
  kind: "task" | "event" | "reminder";
  status: string;
  at: string | null;
};

const KIND_LABELS: Record<AgendaEntry["kind"], string> = {
  task: "задача",
  event: "событие",
  reminder: "напоминание",
};

function dateKeyFromValue(value: string | null): string | null {
  if (!value) {
    return null;
  }
  const date = new Date(value);
  const year = date.getFullYear();
  const month = `${date.getMonth() + 1}`.padStart(2, "0");
  const day = `${date.getDate()}`.padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function dateKeyFromDate(date: Date): string {
  const year = date.getFullYear();
  const month = `${date.getMonth() + 1}`.padStart(2, "0");
  const day = `${date.getDate()}`.padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function buildAgenda(tasks: TaskItem[], events: EventItem[], reminders: ReminderItem[]) {
  const result: Record<string, AgendaEntry[]> = {};

  for (const task of tasks) {
    const at = task.due_at ?? task.scheduled_for;
    const key = dateKeyFromValue(at);
    if (!key) {
      continue;
    }
    result[key] = result[key] ?? [];
    result[key].push({ id: task.id, title: task.title, kind: "task", status: task.status, at });
  }

  for (const event of events) {
    const key = dateKeyFromValue(event.starts_at);
    if (!key) {
      continue;
    }
    result[key] = result[key] ?? [];
    result[key].push({ id: event.id, title: event.title, kind: "event", status: event.status, at: event.starts_at });
  }

  for (const reminder of reminders) {
    const at = reminder.remind_at ?? reminder.remind_on;
    const key = dateKeyFromValue(at);
    if (!key) {
      continue;
    }
    result[key] = result[key] ?? [];
    result[key].push({ id: reminder.id, title: reminder.title, kind: "reminder", status: reminder.status, at });
  }

  for (const key of Object.keys(result)) {
    result[key].sort((left, right) => {
      if (!left.at && !right.at) {
        return left.title.localeCompare(right.title);
      }
      if (!left.at) {
        return 1;
      }
      if (!right.at) {
        return -1;
      }
      return new Date(left.at).getTime() - new Date(right.at).getTime();
    });
  }

  return result;
}

function buildMonthDays(monthCursor: Date): Date[] {
  const firstDay = new Date(monthCursor.getFullYear(), monthCursor.getMonth(), 1);
  const offset = (firstDay.getDay() + 6) % 7;
  const start = new Date(firstDay);
  start.setDate(firstDay.getDate() - offset);

  return Array.from({ length: 42 }, (_, index) => {
    const day = new Date(start);
    day.setDate(start.getDate() + index);
    return day;
  });
}

export function CalendarPage({ tasks, events, reminders }: { tasks: TaskItem[]; events: EventItem[]; reminders: ReminderItem[] }) {
  const today = new Date();
  const [monthCursor, setMonthCursor] = useState(new Date(today.getFullYear(), today.getMonth(), 1));
  const [selectedDate, setSelectedDate] = useState(dateKeyFromDate(today));

  const agenda = buildAgenda(tasks, events, reminders);
  const monthDays = buildMonthDays(monthCursor);
  const selectedItems = agenda[selectedDate] ?? [];

  useEffect(() => {
    const firstVisibleDay = monthDays.find((day) => day.getMonth() === monthCursor.getMonth());
    if (!firstVisibleDay) {
      return;
    }
    const key = dateKeyFromDate(firstVisibleDay);
    if (!agenda[selectedDate] && !monthDays.some((day) => dateKeyFromDate(day) === selectedDate)) {
      setSelectedDate(key);
    }
  }, [monthCursor, monthDays, agenda, selectedDate]);

  return (
    <div className="pageGrid calendarLayout">
      <Card title="Календарь" meta={monthCursor.toLocaleString(undefined, { month: "long", year: "numeric" })}>
        <div className="toolbarRow">
          <div className="segmentedRow">
            <button className="ghost" onClick={() => setMonthCursor(new Date(monthCursor.getFullYear(), monthCursor.getMonth() - 1, 1))}>← Месяц</button>
            <button className="ghost" onClick={() => setMonthCursor(new Date(today.getFullYear(), today.getMonth(), 1))}>Сегодня</button>
            <button className="ghost" onClick={() => setMonthCursor(new Date(monthCursor.getFullYear(), monthCursor.getMonth() + 1, 1))}>Месяц →</button>
          </div>
          <p className="syncHint">Здесь собраны задачи, события и напоминания по датам.</p>
        </div>
        <div className="calendarWeekdays">
          {["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"].map((label) => <span key={label}>{label}</span>)}
        </div>
        <div className="calendarGrid">
          {monthDays.map((day) => {
            const key = dateKeyFromDate(day);
            const items = agenda[key] ?? [];
            const isCurrentMonth = day.getMonth() === monthCursor.getMonth();
            const isSelected = key === selectedDate;
            const isToday = key === dateKeyFromDate(today);
            return (
              <button
                key={key}
                className={`calendarCell${isCurrentMonth ? "" : " mutedCell"}${isSelected ? " selectedCell" : ""}${isToday ? " todayCell" : ""}`}
                onClick={() => setSelectedDate(key)}
              >
                <strong>{day.getDate()}</strong>
                <div className="calendarBadges">
                  {items.slice(0, 3).map((item) => <span key={`${item.kind}-${item.id}`} className={`calendarBadge badge-${item.kind}`}>{KIND_LABELS[item.kind]}</span>)}
                </div>
              </button>
            );
          })}
        </div>
      </Card>

      <Card title="План на день" meta={new Date(selectedDate).toLocaleDateString()}>
        <ul className="listClean">
          {selectedItems.length ? selectedItems.map((item) => (
            <li key={`${item.kind}-${item.id}`}>
              <strong>{item.title}</strong>
              <div className="pillRow">
                <span className="pill">{KIND_LABELS[item.kind]}</span>
                <span className="pill">{item.status}</span>
                {item.at ? <span className="pill">{new Date(item.at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</span> : null}
              </div>
            </li>
          )) : <li>На эту дату ничего не запланировано.</li>}
        </ul>
      </Card>
    </div>
  );
}
