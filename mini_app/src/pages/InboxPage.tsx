import { api } from "../api";
import { Card } from "../components/Card";
import { IncomingItem } from "../types";

export function InboxPage({ items, refresh }: { items: IncomingItem[]; refresh: () => void }) {
  async function applySuggestion(id: string, suggestedActionId: number) {
    await api.resolveInbox(id, { suggested_action_id: suggestedActionId });
    refresh();
  }

  return (
    <div className="stack">
      {items.map((item) => (
        <Card
          key={item.id}
          title={item.summary ?? item.proposed_type ?? "Входящее"}
          meta={item.resolved_object_type ?? item.proposed_type ?? "ждёт решения"}
        >
          <p>{item.assistant_response ?? item.raw_text ?? item.transcript_text ?? item.ocr_text ?? "Оригинал сохранён во вложениях"}</p>
          {item.clarification_question ? <p><strong>Уточнение:</strong> {item.clarification_question}</p> : null}
          <div className="pillRow">
            {item.entities.map((entity) => <span key={`${item.id}-${entity.entity_type}-${entity.value}`} className="pill">{entity.entity_type}: {entity.value}</span>)}
          </div>
          {item.suggested_actions.length ? (
            <div className="actionsRow wrapRow">
              {item.suggested_actions.map((action, index) => (
                <button key={`${item.id}-${action.label}-${index}`} className={index === 0 ? "" : "ghost"} onClick={() => applySuggestion(item.id, index)}>
                  {action.label}
                </button>
              ))}
            </div>
          ) : null}
        </Card>
      ))}
    </div>
  );
}
