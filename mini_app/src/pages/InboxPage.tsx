import { Card } from "../components/Card";
import { api } from "../api";
import { IncomingItem } from "../types";

export function InboxPage({ items, refresh }: { items: IncomingItem[]; refresh: () => void }) {
  async function confirm(id: string) {
    await api.updateInbox(id, { needs_confirmation: false, parse_status: "confirmed" });
    refresh();
  }

  return (
    <div className="stack">
      {items.map((item) => (
        <Card key={item.id} title={item.summary ?? item.proposed_type ?? "Incoming"} meta={`${item.incoming_type} • ${Math.round((item.confidence ?? 0) * 100)}%`}>
          <p>{item.raw_text ?? item.transcript_text ?? item.ocr_text ?? "Оригинал сохранён во вложениях"}</p>
          <div className="pillRow">
            {item.entities.map((entity) => <span key={`${item.id}-${entity.entity_type}-${entity.value}`} className="pill">{entity.entity_type}: {entity.value}</span>)}
          </div>
          <div className="actionsRow">
            <button onClick={() => confirm(item.id)}>Подтвердить</button>
            <button className="ghost">Исправить в Mini App</button>
          </div>
        </Card>
      ))}
    </div>
  );
}
