import { FocusCardItem } from "../types";
import { formatLongDateTime, formatTime } from "../utils/date";

export function PlannerItemCard({
  item,
  arrangeMode,
  onOpen,
  onComplete,
  onMoveUp,
  onMoveDown,
  onQuickShift,
}: {
  item: FocusCardItem;
  arrangeMode: boolean;
  onOpen: () => void;
  onComplete: () => void;
  onMoveUp: () => void;
  onMoveDown: () => void;
  onQuickShift: (preset: "evening" | "tomorrow") => void;
}) {
  const metaLabel = item.isCompleted
    ? "Выполнено сегодня"
    : item.isOverdue
      ? "Просрочено"
      : item.when
        ? formatLongDateTime(item.when)
        : "Можно сделать в любой момент";

  return (
    <article className={item.isCompleted ? "plannerCard completedCard" : "plannerCard"}>
      <button
        type="button"
        className={item.isCompleted ? "plannerCheck checked" : "plannerCheck"}
        aria-label={item.isCompleted ? "Выполнено" : "Отметить выполненным"}
        aria-pressed={item.isCompleted}
        onClick={item.isCompleted ? undefined : onComplete}
        disabled={item.isCompleted}
      >
        <span />
      </button>

      <button type="button" className={item.isCompleted ? "plannerBody completed" : "plannerBody"} onClick={onOpen}>
        <div className="plannerTopline">
          <span className={`kindBadge kind-${item.kind}`}>{item.badge}</span>
          <span className="plannerTime">{item.when ? formatTime(item.when) : "Без времени"}</span>
        </div>
        <strong>{item.title}</strong>
        {item.description ? <p>{item.description}</p> : null}
        <div className="plannerMeta">
          <span className={item.isOverdue && !item.isCompleted ? "metaAlert" : undefined}>{metaLabel}</span>
        </div>
      </button>

      <div className="plannerAside">
        {arrangeMode && !item.isCompleted ? (
          <div className="reorderColumn">
            <button type="button" className="ghost iconButton" onClick={onMoveUp} aria-label="Переместить выше">{"↑"}</button>
            <button type="button" className="ghost iconButton" onClick={onMoveDown} aria-label="Переместить ниже">{"↓"}</button>
          </div>
        ) : null}

        {!arrangeMode && !item.isCompleted ? (
          <div className="quickStack">
            <button type="button" className="ghost quickButton" onClick={() => onQuickShift("evening")}>Вечером</button>
            <button type="button" className="ghost quickButton" onClick={() => onQuickShift("tomorrow")}>Завтра</button>
          </div>
        ) : null}
      </div>
    </article>
  );
}