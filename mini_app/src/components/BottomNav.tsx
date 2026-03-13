import { AppTab } from "../types";

type BottomNavProps = {
  active: AppTab;
  inboxCount: number;
  onChange: (tab: AppTab) => void;
};

const TABS: Array<{ key: AppTab; label: string; icon: string }> = [
  { key: "today", label: "Сегодня", icon: "today" },
  { key: "inbox", label: "Входящие", icon: "inbox" },
  { key: "calendar", label: "Календарь", icon: "calendar" },
  { key: "library", label: "Списки", icon: "library" },
  { key: "search", label: "Поиск", icon: "search" },
];

function Icon({ name }: { name: string }) {
  if (name === "today") {
    return <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 4h12v16H6z" /><path d="M9 2v4" /><path d="M15 2v4" /><path d="M6 9h12" /></svg>;
  }
  if (name === "inbox") {
    return <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 6h16l-2 12H6z" /><path d="M8 12h8" /></svg>;
  }
  if (name === "calendar") {
    return <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 5h16v15H4z" /><path d="M8 3v4" /><path d="M16 3v4" /><path d="M4 10h16" /></svg>;
  }
  if (name === "library") {
    return <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 4h12v16H6z" /><path d="M9 8h6" /><path d="M9 12h6" /><path d="M9 16h4" /></svg>;
  }
  return <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="6" /><path d="M16 16l4 4" /></svg>;
}

export function BottomNav({ active, inboxCount, onChange }: BottomNavProps) {
  return (
    <nav className="bottomNav" aria-label="Основная навигация">
      {TABS.map((tab) => (
        <button key={tab.key} type="button" className={tab.key === active ? "tabButton active" : "tabButton"} onClick={() => onChange(tab.key)}>
          <span className="tabIconWrap">
            <Icon name={tab.icon} />
            {tab.key === "inbox" && inboxCount > 0 ? <span className="tabBadge">{Math.min(inboxCount, 9)}</span> : null}
          </span>
          <span>{tab.label}</span>
        </button>
      ))}
    </nav>
  );
}
