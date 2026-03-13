import { AppTab } from "../types";

type BottomNavProps = {
  active: AppTab;
  inboxCount: number;
  onChange: (tab: AppTab) => void;
};

const TABS: Array<{ key: AppTab; label: string; icon: string }> = [
  { key: "today", label: "\u0421\u0435\u0433\u043e\u0434\u043d\u044f", icon: "today" },
  { key: "inbox", label: "\u0412\u0445\u043e\u0434\u044f\u0449\u0438\u0435", icon: "inbox" },
  { key: "calendar", label: "\u041a\u0430\u043b\u0435\u043d\u0434\u0430\u0440\u044c", icon: "calendar" },
  { key: "library", label: "\u0421\u043f\u0438\u0441\u043a\u0438", icon: "library" },
  { key: "search", label: "\u041f\u043e\u0438\u0441\u043a", icon: "search" },
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
    <nav className="bottomNav" aria-label="\u041e\u0441\u043d\u043e\u0432\u043d\u0430\u044f \u043d\u0430\u0432\u0438\u0433\u0430\u0446\u0438\u044f">
      {TABS.map((tab) => (
        <button key={tab.key} type="button" className={tab.key === active ? "tabButton active" : "tabButton"} onClick={() => onChange(tab.key)}>
          <span className="tabIconWrap">
            <Icon name={tab.icon} />
            {tab.key === "inbox" && inboxCount > 0 ? <span className="tabBadge">{Math.min(inboxCount, 9)}</span> : null}
          </span>
          <span className="tabLabel">{tab.label}</span>
        </button>
      ))}
    </nav>
  );
}