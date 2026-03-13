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
    ? "\u0412\u044b\u043f\u043e\u043b\u043d\u0435\u043d\u043e \u0441\u0435\u0433\u043e\u0434\u043d\u044f"
    : item.isOverdue
      ? "\u041f\u0440\u043e\u0441\u0440\u043e\u0447\u0435\u043d\u043e"
      : item.when
        ? formatLongDateTime(item.when)
        : "\u041c\u043e\u0436\u043d\u043e \u0441\u0434\u0435\u043b\u0430\u0442\u044c \u0432 \u043b\u044e\u0431\u043e\u0439 \u043c\u043e\u043c\u0435\u043d\u0442";

  return (
    <article className={item.isCompleted ? "plannerCard completedCard" : "plannerCard"}>
      <button
        type="button"
        className={item.isCompleted ? "plannerCheck checked" : "plannerCheck"}
        aria-label={item.isCompleted ? "\u0412\u044b\u043f\u043e\u043b\u043d\u0435\u043d\u043e" : "\u041e\u0442\u043c\u0435\u0442\u0438\u0442\u044c \u0432\u044b\u043f\u043e\u043b\u043d\u0435\u043d\u043d\u044b\u043c"}
        aria-pressed={item.isCompleted}
        onClick={item.isCompleted ? undefined : onComplete}
        disabled={item.isCompleted}
      >
        <span />
      </button>

      <button type="button" className={item.isCompleted ? "plannerBody completed" : "plannerBody"} onClick={onOpen}>
        <div className="plannerTopline">
          <span className={`kindBadge kind-${item.kind}`}>{item.badge}</span>
          <span className="plannerTime">{item.when ? formatTime(item.when) : "\u0411\u0435\u0437 \u0432\u0440\u0435\u043c\u0435\u043d\u0438"}</span>
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
            <button type="button" className="ghost iconButton" onClick={onMoveUp} aria-label="\u041f\u0435\u0440\u0435\u043c\u0435\u0441\u0442\u0438\u0442\u044c \u0432\u044b\u0448\u0435">{"\u2191"}</button>
            <button type="button" className="ghost iconButton" onClick={onMoveDown} aria-label="\u041f\u0435\u0440\u0435\u043c\u0435\u0441\u0442\u0438\u0442\u044c \u043d\u0438\u0436\u0435">{"\u2193"}</button>
          </div>
        ) : null}

        {!arrangeMode && !item.isCompleted ? (
          <div className="quickStack">
            <button type="button" className="ghost quickButton" onClick={() => onQuickShift("evening")}>\u0412\u0435\u0447\u0435\u0440\u043e\u043c</button>
            <button type="button" className="ghost quickButton" onClick={() => onQuickShift("tomorrow")}>\u0417\u0430\u0432\u0442\u0440\u0430</button>
          </div>
        ) : null}
      </div>
    </article>
  );
}