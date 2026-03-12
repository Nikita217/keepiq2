import { useMemo, useState } from "react";

import { EmptyState } from "../components/EmptyState";
import { ScreenHeader } from "../components/ScreenHeader";
import { CalendarEntry } from "../types";
import { dayKey, formatLongDateTime, isSameDay, startOfDay } from "../utils/date";
import { calendarMap, getTypeLabel } from "../utils/models";

const VIEW_LABELS = {
  day: "\u0414\u0435\u043d\u044c",
  week: "\u041d\u0435\u0434\u0435\u043b\u044f",
  month: "\u041c\u0435\u0441\u044f\u0446",
} as const;

const WEEKDAY_LABELS = [
  "\u041f\u043d",
  "\u0412\u0442",
  "\u0421\u0440",
  "\u0427\u0442",
  "\u041f\u0442",
  "\u0421\u0431",
  "\u0412\u0441",
];

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
        eyebrow={"\u041a\u0430\u043b\u0435\u043d\u0434\u0430\u0440\u044c"}
        title={"\u0414\u0430\u0442\u044b \u0431\u0435\u0437 \u0445\u0430\u043e\u0441\u0430"}
        subtitle={"\u041e\u0434\u0438\u043d \u043a\u0430\u043b\u0435\u043d\u0434\u0430\u0440\u043d\u044b\u0439 \u0441\u043b\u043e\u0439 \u0434\u043b\u044f \u0437\u0430\u0434\u0430\u0447, \u0441\u043e\u0431\u044b\u0442\u0438\u0439, \u043d\u0430\u043f\u043e\u043c\u0438\u043d\u0430\u043d\u0438\u0439 \u0438 reply later. \u041f\u0435\u0440\u0435\u043a\u043b\u044e\u0447\u0430\u0439\u0442\u0435\u0441\u044c \u043c\u0435\u0436\u0434\u0443 \u0434\u043d\u0435\u043c, \u043d\u0435\u0434\u0435\u043b\u0435\u0439 \u0438 \u043c\u0435\u0441\u044f\u0446\u0435\u043c \u0431\u0435\u0437 \u0440\u0430\u0437\u043d\u044b\u0445 \u044d\u043a\u0440\u0430\u043d\u043e\u0432 \u0434\u043b\u044f \u043a\u0430\u0436\u0434\u043e\u0433\u043e \u0442\u0438\u043f\u0430."}
        actions={
          <div className="headerButtonRow">
            {(["day", "week", "month"] as const).map((mode) => (
              <button key={mode} type="button" className={view === mode ? "ghost activeGhost" : "ghost"} onClick={() => setView(mode)}>
                {VIEW_LABELS[mode]}
              </button>
            ))}
          </div>
        }
      />

      {view === "month" ? (
        <section className="sectionBlock">
          <div className="monthHeader">
            <div>
              <h2>{monthCursor.toLocaleString("ru-RU", { month: "long", year: "numeric" })}</h2>
              <p className="sectionNote">{"\u041d\u0430\u0436\u043c\u0438\u0442\u0435 \u043d\u0430 \u0434\u0435\u043d\u044c, \u0447\u0442\u043e\u0431\u044b \u0443\u0432\u0438\u0434\u0435\u0442\u044c \u0432\u0441\u0435 \u043e\u0431\u044a\u0435\u043a\u0442\u044b \u043d\u0430 \u044d\u0442\u0443 \u0434\u0430\u0442\u0443."}</p>
            </div>
            <div className="monthNav">
              <button type="button" className="ghost monthNavButton" onClick={() => setMonthCursor(new Date(monthCursor.getFullYear(), monthCursor.getMonth() - 1, 1))}>{"<"}</button>
              <button type="button" className="ghost" onClick={() => setMonthCursor(new Date(today.getFullYear(), today.getMonth(), 1))}>{"\u0421\u0435\u0433\u043e\u0434\u043d\u044f"}</button>
              <button type="button" className="ghost monthNavButton" onClick={() => setMonthCursor(new Date(monthCursor.getFullYear(), monthCursor.getMonth() + 1, 1))}>{">"}</button>
            </div>
          </div>
          <div className="calendarBoard">
            <div className="calendarWeekdays">{WEEKDAY_LABELS.map((label) => <span key={label}>{label}</span>)}</div>
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
                      {items.slice(0, 2).map((item) => <span key={item.key} className={`calendarBadge badge-${item.kind}`}>{getTypeLabel(item.kind)}</span>)}
                    </div>
                  </button>
                );
              })}
            </div>
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
                  <small>{`${items.length} \u0448\u0442.`}</small>
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
          <h2>{"\u041f\u043b\u0430\u043d \u043d\u0430 \u0432\u044b\u0431\u0440\u0430\u043d\u043d\u0443\u044e \u0434\u0430\u0442\u0443"}</h2>
          <span>{selectedItems.length}</span>
        </div>
        {selectedItems.length === 0 ? <EmptyState title={"\u041f\u0443\u0441\u0442\u043e"} text={"\u041d\u0430 \u044d\u0442\u0443 \u0434\u0430\u0442\u0443 \u043f\u043e\u043a\u0430 \u043d\u0435\u0442 \u0430\u043a\u0442\u0438\u0432\u043d\u044b\u0445 \u043e\u0431\u044a\u0435\u043a\u0442\u043e\u0432."} /> : null}
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
