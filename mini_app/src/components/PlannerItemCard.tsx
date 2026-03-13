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
      <button type="button" className="plannerCheck" aria-label="\u041e\u0442\u043c\u0435\u0442\u0438\u0442\u044c \u0432\u044b\u043f\u043e\u043b\u043d\u0435\u043d\u043d\u044b\u043c" onClick={onComplete}>
        <span />
      </button>
      <button type="button" className="plannerBody" onClick={onOpen}>
        <div className="plannerTopline">
          <span className={`kindBadge kind-${item.kind}`}>{item.badge}</span>
          <span className="plannerTime">{item.when ? formatTime(item.when) : "\u0411\u0435\u0437 \u0432\u0440\u0435\u043c\u0435\u043d\u0438"}</span>
        </div>
        <strong>{item.title}</strong>
        {item.description ? <p>{item.description}</p> : null}
        <div className="plannerMeta">
          {item.isOverdue ? <span className="metaAlert">\u041f\u0440\u043e\u0441\u0440\u043e\u0447\u0435\u043d\u043e</span> : null}
          {item.when ? <span>{formatLongDateTime(item.when)}</span> : <span>\u041c\u043e\u0436\u043d\u043e \u0441\u0434\u0435\u043b\u0430\u0442\u044c \u0432 \u043b\u044e\u0431\u043e\u0439 \u043c\u043e\u043c\u0435\u043d\u0442</span>}
        </div>
      </button>
      <div className="plannerAside">
        {arrangeMode ? (
          <div className="reorderColumn">
            <button type="button" className="ghost iconButton" onClick={onMoveUp}>{"\u2191"}</button>
            <button type="button" className="ghost iconButton" onClick={onMoveDown}>{"\u2193"}</button>
          </div>
        ) : (
          <div className="quickStack">
            <button type="button" className="ghost quickButton" onClick={() => onQuickShift("evening")}>\u0412\u0435\u0447\u0435\u0440\u043e\u043c</button>
            <button type="button" className="ghost quickButton" onClick={() => onQuickShift("tomorrow")}>\u0417\u0430\u0432\u0442\u0440\u0430</button>
          </div>
        )}
      </div>
    </article>
  );
}
