import { Card } from "../components/Card";
import { api } from "../api";
import { IncomingItem } from "../types";

const TARGET_TYPES = ["task", "note", "list", "event", "reply_later", "saved"];

export function InboxPage({ items, refresh }: { items: IncomingItem[]; refresh: () => void }) {
  async function confirm(id: string) {
    await api.resolveInbox(id, {});
    refresh();
  }

  async function saveAs(id: string, targetType: string) {
    await api.resolveInbox(id, { target_type: targetType });
    refresh();
  }

  return (
    <div className="stack">
      {items.map((item) => (
        <Card
          key={item.id}
          title={item.summary ?? item.proposed_type ?? "Incoming"}
          meta={`${item.incoming_type} • ${Math.round((item.confidence ?? 0) * 100)}% • ${item.resolved_object_type ?? item.proposed_type ?? "pending"}`}
        >
          <p>{item.raw_text ?? item.transcript_text ?? item.ocr_text ?? "Оригинал сохранён во вложениях"}</p>
          {item.assistant_response ? <p><strong>AI:</strong> {item.assistant_response}</p> : null}
          {item.clarification_question ? <p><strong>Уточнение:</strong> {item.clarification_question}</p> : null}
          <div className="pillRow">
            {item.entities.map((entity) => <span key={`${item.id}-${entity.entity_type}-${entity.value}`} className="pill">{entity.entity_type}: {entity.value}</span>)}
          </div>
          <div className="actionsRow">
            <button onClick={() => confirm(item.id)}>{item.needs_confirmation ? "Подтвердить" : "Применить ещё раз"}</button>
            {TARGET_TYPES.map((targetType) => (
              <button key={targetType} className="ghost" onClick={() => saveAs(item.id, targetType)}>{targetType}</button>
            ))}
          </div>
        </Card>
      ))}
    </div>
  );
}
