import { useState } from "react";

import { api } from "../api";
import { Card } from "../components/Card";
import { TaskItem } from "../types";

function isOpenTask(task: TaskItem) {
  return task.status !== "done" && task.status !== "archived";
}

function toDateInputValue(value: string | null): string {
  if (!value) {
    return "";
  }
  const date = new Date(value);
  const local = new Date(date.getTime() - date.getTimezoneOffset() * 60000);
  return local.toISOString().slice(0, 16);
}

function fromDateInputValue(value: string): string | null {
  if (!value) {
    return null;
  }
  return new Date(value).toISOString();
}

export function TasksPage({ tasks, refresh }: { tasks: TaskItem[]; refresh: () => void }) {
  const [filter, setFilter] = useState<"open" | "all">("open");
  const [draftDates, setDraftDates] = useState<Record<string, string>>({});

  const visibleTasks = [...tasks]
    .filter((task) => (filter === "open" ? isOpenTask(task) : true))
    .sort((left, right) => {
      const leftDate = left.due_at ?? left.scheduled_for;
      const rightDate = right.due_at ?? right.scheduled_for;
      if (!leftDate && !rightDate) {
        return left.title.localeCompare(right.title);
      }
      if (!leftDate) {
        return 1;
      }
      if (!rightDate) {
        return -1;
      }
      return new Date(leftDate).getTime() - new Date(rightDate).getTime();
    });

  async function markDone(id: string) {
    await api.updateTask(id, { status: "done" });
    refresh();
  }

  async function reopen(id: string) {
    await api.updateTask(id, { status: "active" });
    refresh();
  }

  async function saveDeadline(task: TaskItem) {
    const value = draftDates[task.id] ?? toDateInputValue(task.due_at ?? task.scheduled_for);
    await api.updateTask(task.id, {
      due_at: fromDateInputValue(value),
      scheduled_for: fromDateInputValue(value),
      status: task.status === "done" ? task.status : "scheduled",
    });
    refresh();
  }

  async function clearDeadline(task: TaskItem) {
    await api.updateTask(task.id, {
      due_at: null,
      scheduled_for: null,
      status: task.status === "done" ? "done" : "active",
    });
    refresh();
  }

  async function removeTask(id: string) {
    await api.deleteTask(id);
    refresh();
  }

  return (
    <div className="stack">
      <Card title="Task Controls" meta={`${visibleTasks.length} shown`}>
        <div className="toolbarRow">
          <div className="segmentedRow">
            <button className={filter === "open" ? "navChip active" : "navChip"} onClick={() => setFilter("open")}>Невыполненные</button>
            <button className={filter === "all" ? "navChip active" : "navChip"} onClick={() => setFilter("all")}>Все задачи</button>
          </div>
          <p className="syncHint">Можно отметить задачу выполненной, изменить срок или удалить её полностью.</p>
        </div>
      </Card>

      {visibleTasks.map((task) => {
        const deadline = task.due_at ?? task.scheduled_for;
        const draftValue = draftDates[task.id] ?? toDateInputValue(deadline);
        return (
          <Card key={task.id} title={task.title} meta={`${task.status}${deadline ? ` • ${new Date(deadline).toLocaleString()}` : " • без срока"}`}>
            <p>{task.description ?? "Без описания"}</p>
            <div className="fieldRow">
              <input
                type="datetime-local"
                value={draftValue}
                onChange={(event) => setDraftDates((current) => ({ ...current, [task.id]: event.target.value }))}
              />
              <button onClick={() => saveDeadline(task)}>Сохранить срок</button>
              <button className="ghost" onClick={() => clearDeadline(task)}>Очистить</button>
            </div>
            <div className="actionsRow wrapRow">
              {task.status === "done" ? (
                <button className="ghost" onClick={() => reopen(task.id)}>Вернуть в работу</button>
              ) : (
                <button onClick={() => markDone(task.id)}>Готово</button>
              )}
              <button className="ghost danger" onClick={() => removeTask(task.id)}>Удалить</button>
              <span className="pill">source: {task.source_incoming_item_id ?? "manual"}</span>
            </div>
          </Card>
        );
      })}
    </div>
  );
}
