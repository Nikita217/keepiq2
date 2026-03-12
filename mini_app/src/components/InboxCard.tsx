import { IncomingItem } from "../types";
import { getTypeLabel } from "../utils/models";

function confidenceLabel(value: number | null): string {
  if (value === null) {
    return "без оценки";
  }
  if (value >= 0.85) {
    return `уверенность ${Math.round(value * 100)}%`;
  }
  if (value >= 0.65) {
    return `нужна проверка ${Math.round(value * 100)}%`;
  }
  return `не уверен ${Math.round(value * 100)}%`;
}

export function InboxCard({ item, onOpen, onResolve }: { item: IncomingItem; onOpen: () => void; onResolve: (targetType: string) => void }) {
  const preview = item.raw_text ?? item.transcript_text ?? item.ocr_text ?? item.source_url ?? "Оригинал сохранён во вложениях";

  return (
    <article className="inboxCard">
      <button type="button" className="inboxCardMain" onClick={onOpen}>
        <div className="inboxCardTop">
          <span className={item.needs_confirmation ? "confidencePill warning" : "confidencePill"}>{confidenceLabel(item.confidence)}</span>
          <span className="kindBadge subtle">{getTypeLabel(item.proposed_type ?? "incoming")}</span>
        </div>
        <strong>{item.summary ?? item.proposed_type ?? "Входящее"}</strong>
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
        <button type="button" className="ghost" onClick={() => onResolve("note")}>Как заметку</button>
      </div>
    </article>
  );
}
