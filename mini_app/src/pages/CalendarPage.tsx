import { useMemo, useState } from "react";

import { EmptyState } from "../components/EmptyState";
import { ScreenHeader } from "../components/ScreenHeader";
import { CalendarEntry } from "../types";
import { dayKey, formatLongDateTime, isSameDay, startOfDay } from "../utils/date";
import { calendarMap, getTypeLabel } from "../utils/models";

function buildMonthDays(cursor: Date): Date[] {
  const firstDay = new Date(cursor.getFullYear(), cursor.getMonth(), 1);
  const offset = (firstDay.getDay() + 6) % 7;
  const start = new Date(firstDay);
  start.setDate(firstDay.getDate() - offset);
  return Array.from({ length: 42 }, (_, index) => {
    const day = new Date(start);
    day.setDate(start.getDate() + index);
    return day;
  });
}

export function CalendarPage({ entries, onOpen }: { entries: CalendarEntry[]; onOpen: (entry: CalendarEntry) => void }) {
  const today = startOfDay(new Date());
  const [view, setView] = useState<"day" | "week" | "month">("month");
  const [selectedDate, setSelectedDate] = useState(today);
  const [monthCursor, setMonthCursor] = useState(new Date(today.getFullYear(), today.getMonth(), 1));
  const agenda = useMemo(() => calendarMap(entries), [entries]);
  const selectedItems = agenda.get(dayKey(selectedDate)) ?? [];
  const weekDays = Array.from({ length: 7 }, (_, index) => {
    const day = new Date(selectedDate);
    day.setDate(selectedDate.getDate() - ((selectedDate.getDay() + 6) % 7) + index);
    return day;
  });
  const monthDays = buildMonthDays(monthCursor);

  return (
    <div className="screenStack">
      <ScreenHeader
        eyebrow="Календарь"
        title="Даты без хаоса"
        subtitle="Один календарный слой для задач, событий, напоминаний и reply later. Переключайтесь между днём, неделей и месяцем без отдельного экрана для каждого типа."
        actions={
          <div className="headerButtonRow">
            {(["day", "week", "month"] as const).map((mode) => (
              <button key={mode} type="button" className={view === mode ? "ghost activeGhost" : "ghost"} onClick={() => setView(mode)}>
                {mode === "day" ? "День" : mode === "week" ? "Неделя" : "Месяц"}
              </button>
            ))}
          </div>
        }
      />

      {view === "month" ? (
        <section className="sectionBlock">
          <div className="sectionHead">
            <h2>{monthCursor.toLocaleString("ru-RU", { month: "long", year: "numeric" })}</h2>
            <div className="headerButtonRow">
              <button type="button" className="ghost" onClick={() => setMonthCursor(new Date(monthCursor.getFullYear(), monthCursor.getMonth() - 1, 1))}>{"<"}</button>
              <button type="button" className="ghost" onClick={() => setMonthCursor(new Date(today.getFullYear(), today.getMonth(), 1))}>Сегодня</button>
              <button type="button" className="ghost" onClick={() => setMonthCursor(new Date(monthCursor.getFullYear(), monthCursor.getMonth() + 1, 1))}>{">"}</button>
            </div>
          </div>
          <div className="calendarWeekdays">{["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"].map((label) => <span key={label}>{label}</span>)}</div>
          <div className="calendarGrid">
            {monthDays.map((day) => {
              const items = agenda.get(dayKey(day)) ?? [];
              return (
                <button
                  key={dayKey(day)}
                  type="button"
                  className={`calendarCell${day.getMonth() === monthCursor.getMonth() ? "" : " mutedCell"}${isSameDay(day, selectedDate) ? " selectedCell" : ""}${isSameDay(day, today) ? " todayCell" : ""}`}
                  onClick={() => setSelectedDate(day)}
                >
                  <strong>{day.getDate()}</strong>
                  <div className="calendarBadges">
                    {items.slice(0, 3).map((item) => <span key={item.key} className={`calendarBadge badge-${item.kind}`}>{getTypeLabel(item.kind)}</span>)}
                  </div>
                </button>
              );
            })}
          </div>
        </section>
      ) : null}

      {view === "week" ? (
        <section className="sectionBlock">
          <div className="weekStrip">
            {weekDays.map((day) => {
              const items = agenda.get(dayKey(day)) ?? [];
              return (
                <button key={dayKey(day)} type="button" className={isSameDay(day, selectedDate) ? "weekDay active" : "weekDay"} onClick={() => setSelectedDate(day)}>
                  <span>{day.toLocaleDateString("ru-RU", { weekday: "short" })}</span>
                  <strong>{day.getDate()}</strong>
                  <small>{items.length} шт.</small>
                </button>
              );
            })}
          </div>
        </section>
      ) : null}

      {view === "day" ? (
        <section className="sectionBlock">
          <div className="sectionHead">
            <h2>{selectedDate.toLocaleDateString("ru-RU", { weekday: "long", day: "numeric", month: "long" })}</h2>
          </div>
        </section>
      ) : null}

      <section className="sectionBlock">
        <div className="sectionHead">
          <h2>План на выбранную дату</h2>
          <span>{selectedItems.length}</span>
        </div>
        {selectedItems.length === 0 ? <EmptyState title="Пусто" text="На эту дату пока нет активных объектов." /> : null}
        <div className="agendaList">
          {selectedItems.map((item) => (
            <button key={item.key} type="button" className="agendaCard" onClick={() => onOpen(item)}>
              <div className="agendaCardTop">
                <span className={`kindBadge kind-${item.kind}`}>{getTypeLabel(item.kind)}</span>
                <span>{formatLongDateTime(item.when)}</span>
              </div>
              <strong>{item.title}</strong>
              <p>{item.status}</p>
            </button>
          ))}
        </div>
      </section>
    </div>
  );
}
