import { IncomingItem } from "../types";
import { getTypeLabel } from "../utils/models";

function confidenceLabel(value: number | null): string {
  if (value === null) {
    return "\u0431\u0435\u0437 \u043e\u0446\u0435\u043d\u043a\u0438";
  }
  if (value >= 0.85) {
    return `\u0443\u0432\u0435\u0440\u0435\u043d\u043d\u043e\u0441\u0442\u044c ${Math.round(value * 100)}%`;
  }
  if (value >= 0.65) {
    return `\u043d\u0443\u0436\u043d\u0430 \u043f\u0440\u043e\u0432\u0435\u0440\u043a\u0430 ${Math.round(value * 100)}%`;
  }
  return `\u043d\u0435 \u0443\u0432\u0435\u0440\u0435\u043d ${Math.round(value * 100)}%`;
}

export function InboxCard({ item, onOpen, onResolve }: { item: IncomingItem; onOpen: () => void; onResolve: (targetType: string) => void }) {
  const preview = item.raw_text ?? item.transcript_text ?? item.ocr_text ?? item.source_url ?? "\u041e\u0440\u0438\u0433\u0438\u043d\u0430\u043b \u0441\u043e\u0445\u0440\u0430\u043d\u0451\u043d \u0432\u043e \u0432\u043b\u043e\u0436\u0435\u043d\u0438\u044f\u0445";

  return (
    <article className="inboxCard">
      <button type="button" className="inboxCardMain" onClick={onOpen}>
        <div className="inboxCardTop">
          <span className={item.needs_confirmation ? "confidencePill warning" : "confidencePill"}>{confidenceLabel(item.confidence)}</span>
          <span className="kindBadge subtle">{getTypeLabel(item.proposed_type ?? "incoming")}</span>
        </div>
        <strong>{item.summary ?? item.proposed_type ?? "\u0412\u0445\u043e\u0434\u044f\u0449\u0435\u0435"}</strong>
        <p>{item.assistant_response ?? preview}</p>
        {item.clarification_question ? <div className="inlineHint">{item.clarification_question}</div> : null}
        <div className="chipRow">
          {item.entities.slice(0, 4).map((entity) => <span key={`${item.id}-${entity.entity_type}-${entity.value}`} className="chip">{entity.entity_type}: {entity.value}</span>)}
        </div>
      </button>
      <div className="actionGrid">
        {item.suggested_actions.slice(0, 2).map((action) => (
          <button key={`${item.id}-${action.label}`} type="button" onClick={() => onResolve(action.target_type ?? item.proposed_type ?? "note")}>
            {action.label}
          </button>
        ))}
        <button type="button" className="ghost" onClick={() => onResolve("note")}>\u041a\u0430\u043a \u0437\u0430\u043c\u0435\u0442\u043a\u0443</button>
      </div>
    </article>
  );
}
