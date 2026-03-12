import { api } from "../api";
import { Card } from "../components/Card";
import { TaskItem } from "../types";

export function TasksPage({ tasks, refresh }: { tasks: TaskItem[]; refresh: () => void }) {
  async function markDone(id: string) {
    await api.updateTask(id, { status: "done" });
    refresh();
  }

  return (
    <div className="stack">
      {tasks.map((task) => (
        <Card key={task.id} title={task.title} meta={task.status}>
          <p>{task.description ?? "Без описания"}</p>
          <div className="actionsRow">
            <button onClick={() => markDone(task.id)}>Готово</button>
            <button className="ghost">Открыть источник</button>
          </div>
        </Card>
      ))}
    </div>
  );
}
