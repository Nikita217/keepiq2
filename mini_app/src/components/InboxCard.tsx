import { IncomingItem } from "../types";
import { getTypeLabel } from "../utils/models";

function confidenceLabel(value: number | null): string {
  if (value === null) {
    return "Р±РµР· РѕС†РµРЅРєРё";
  }
  if (value >= 0.85) {
    return `СѓРІРµСЂРµРЅРЅРѕСЃС‚СЊ ${Math.round(value * 100)}%`;
  }
  if (value >= 0.65) {
    return `РЅСѓР¶РЅР° РїСЂРѕРІРµСЂРєР° ${Math.round(value * 100)}%`;
  }
  return `РЅРµ СѓРІРµСЂРµРЅ ${Math.round(value * 100)}%`;
}

const FALLBACK_ACTIONS = [
  { label: "РќР°РїРѕРјРёРЅР°РЅРёРµ", targetType: "reminder" },
  { label: "РЎРїРёСЃРѕРє", targetType: "list" },
  { label: "РЎРѕР±С‹С‚РёРµ", targetType: "event" },
  { label: "Р—Р°РјРµС‚РєР°", targetType: "note" },
];

export function InboxCard({
  item,
  onOpen,
  onResolve,
}: {
  item: IncomingItem;
  onOpen: () => void;
  onResolve: (payload: { targetType?: string; suggestedActionId?: number }) => void;
}) {
  const preview = item.raw_text ?? item.transcript_text ?? item.ocr_text ?? item.source_url ?? "РћСЂРёРіРёРЅР°Р» СЃРѕС…СЂР°РЅС‘РЅ РІРѕ РІР»РѕР¶РµРЅРёСЏС…";
  const actions = item.suggested_actions.length
    ? item.suggested_actions.slice(0, 4).map((action, index) => ({
        label: action.label,
        payload: { suggestedActionId: index, targetType: action.target_type ?? undefined },
      }))
    : FALLBACK_ACTIONS.map((action) => ({ label: action.label, payload: { targetType: action.targetType } }));

  return (
    <article className="inboxCard">
      <button type="button" className="inboxCardMain" onClick={onOpen}>
        <div className="inboxCardTop">
          <span className={item.needs_confirmation ? "confidencePill warning" : "confidencePill"}>{confidenceLabel(item.confidence)}</span>
          <span className="kindBadge subtle">{getTypeLabel(item.proposed_type ?? "incoming")}</span>
        </div>
        <strong>{item.summary ?? item.proposed_type ?? "Р’С…РѕРґСЏС‰РµРµ"}</strong>
        <p>{item.assistant_response ?? preview}</p>
        {item.clarification_question ? <div className="inlineHint">{item.clarification_question}</div> : null}
        <div className="chipRow">
          {item.entities.slice(0, 4).map((entity) => <span key={`${item.id}-${entity.entity_type}-${entity.value}`} className="chip">{entity.entity_type}: {entity.value}</span>)}
        </div>
      </button>
      <div className="actionGrid">
        {actions.map((action) => (
          <button key={`${item.id}-${action.label}`} type="button" onClick={() => onResolve(action.payload)}>
            {action.label}
          </button>
        ))}
      </div>
    </article>
  );
}

