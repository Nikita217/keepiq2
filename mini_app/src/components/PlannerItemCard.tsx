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
  return (
    <article className="plannerCard">
      <button type="button" className="plannerCheck" aria-label="Отметить выполненным" onClick={onComplete}>
        <span />
      </button>
      <button type="button" className="plannerBody" onClick={onOpen}>
        <div className="plannerTopline">
          <span className={`kindBadge kind-${item.kind}`}>{item.badge}</span>
          <span className="plannerTime">{item.when ? formatTime(item.when) : "Без времени"}</span>
        </div>
        <strong>{item.title}</strong>
        {item.description ? <p>{item.description}</p> : null}
        <div className="plannerMeta">
          {item.isOverdue ? <span className="metaAlert">Просрочено</span> : null}
          {item.when ? <span>{formatLongDateTime(item.when)}</span> : <span>Можно сделать в любой момент</span>}
        </div>
      </button>
      <div className="plannerAside">
        {arrangeMode ? (
          <div className="reorderColumn">
            <button type="button" className="ghost iconButton" onClick={onMoveUp}>{"↑"}</button>
            <button type="button" className="ghost iconButton" onClick={onMoveDown}>{"↓"}</button>
          </div>
        ) : (
          <div className="quickStack">
            <button type="button" className="ghost quickButton" onClick={() => onQuickShift("evening")}>Вечером</button>
            <button type="button" className="ghost quickButton" onClick={() => onQuickShift("tomorrow")}>Завтра</button>
          </div>
        )}
      </div>
    </article>
  );
}
