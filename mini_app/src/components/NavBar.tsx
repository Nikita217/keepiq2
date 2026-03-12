import type { ReactNode } from "react";

export type TabKey = "dashboard" | "inbox" | "today" | "tasks" | "calendar" | "events" | "lists" | "notes" | "search";

const TABS: Array<{ key: TabKey; label: string }> = [
  { key: "dashboard", label: "Home" },
  { key: "inbox", label: "Inbox" },
  { key: "today", label: "Today" },
  { key: "tasks", label: "Tasks" },
  { key: "calendar", label: "Calendar" },
  { key: "events", label: "Time" },
  { key: "lists", label: "Lists" },
  { key: "notes", label: "Notes" },
  { key: "search", label: "Search" },
];

export function NavBar({ active, onChange, aside }: { active: TabKey; onChange: (tab: TabKey) => void; aside?: ReactNode }) {
  return (
    <header className="topbar">
      <div>
        <p className="eyebrow">Personal AI inbox</p>
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
