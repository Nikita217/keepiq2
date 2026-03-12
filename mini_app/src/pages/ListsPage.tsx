import { Card } from "../components/Card";
import { ListEntity } from "../types";

export function ListsPage({ lists }: { lists: ListEntity[] }) {
  return (
    <div className="stack">
      {lists.map((list) => (
        <Card key={list.id} title={list.title} meta={list.kind}>
          <ul className="listClean">{list.items.map((item) => <li key={item.id}>{item.is_done ? "✓" : "○"} {item.text}</li>)}</ul>
        </Card>
      ))}
    </div>
  );
}
