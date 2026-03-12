import type { ReactNode } from "react";

export type TabKey = "dashboard" | "inbox" | "today" | "tasks" | "calendar" | "events" | "lists" | "notes" | "search";

const TABS: Array<{ key: TabKey; label: string }> = [
  { key: "dashboard", label: "Главная" },
  { key: "inbox", label: "Входящие" },
  { key: "today", label: "Сегодня" },
  { key: "tasks", label: "Задачи" },
  { key: "calendar", label: "Календарь" },
  { key: "events", label: "События" },
  { key: "lists", label: "Списки" },
  { key: "notes", label: "Заметки" },
  { key: "search", label: "Поиск" },
];

export function NavBar({ active, onChange, aside }: { active: TabKey; onChange: (tab: TabKey) => void; aside?: ReactNode }) {
  return (
    <header className="topbar">
      <div>
        <p className="eyebrow">Личный AI-задачник</p>
        <h1>KeepIQ</h1>
      </div>
      <div className="topbarAside">{aside}</div>
      <nav className="navGrid navGridWide">
        {TABS.map((tab) => (
          <button key={tab.key} className={tab.key === active ? "navChip active" : "navChip"} onClick={() => onChange(tab.key)}>
            {tab.label}
          </button>
        ))}
      </nav>
    </header>
  );
}
