import { EmptyState } from "../components/EmptyState";
import { PlannerItemCard } from "../components/PlannerItemCard";
import { ScreenHeader } from "../components/ScreenHeader";
import { TodayGroup } from "../types";

export function TodayPage({
  title,
  subtitle,
  groups,
  inboxCount,
  overdueCount,
  lastSyncAt,
  isRefreshing,
  arrangeMode,
  onToggleArrange,
  onRefresh,
  onOpenItem,
  onCompleteItem,
  onQuickShift,
  onMoveUp,
  onMoveDown,
}: {
  title: string;
  subtitle: string;
  groups: TodayGroup[];
  inboxCount: number;
  overdueCount: number;
  lastSyncAt: string | null;
  isRefreshing: boolean;
  arrangeMode: boolean;
  onToggleArrange: () => void;
  onRefresh: () => void;
  onOpenItem: (itemKey: string) => void;
  onCompleteItem: (itemKey: string) => void;
  onQuickShift: (itemKey: string, preset: "evening" | "tomorrow") => void;
  onMoveUp: (itemKey: string) => void;
  onMoveDown: (itemKey: string) => void;
}) {
  return (
    <div className="screenStack">
      <ScreenHeader
        eyebrow="\u0421\u0435\u0433\u043e\u0434\u043d\u044f"
        title={title}
        subtitle={subtitle}
        actions={
          <div className="headerButtonRow">
            <button type="button" className={arrangeMode ? "ghost activeGhost" : "ghost"} onClick={onToggleArrange}>\u041f\u043e\u0440\u044f\u0434\u043e\u043a</button>
            <button type="button" className="ghost" onClick={onRefresh}>{isRefreshing ? "\u041e\u0431\u043d\u043e\u0432\u043b\u044f\u044e..." : "\u041e\u0431\u043d\u043e\u0432\u0438\u0442\u044c"}</button>
          </div>
        }
        metrics={
          <>
            <span className="metricPill"><strong>{groups.reduce((sum, group) => sum + group.items.length, 0)}</strong> \u0432 \u0444\u043e\u043a\u0443\u0441\u0435</span>
            <span className="metricPill"><strong>{inboxCount}</strong> \u0432\u043e \u0432\u0445\u043e\u0434\u044f\u0449\u0438\u0445</span>
            <span className="metricPill alert"><strong>{overdueCount}</strong> \u043f\u0440\u043e\u0441\u0440\u043e\u0447\u0435\u043d\u043e</span>
            {lastSyncAt ? <span className="metricPill subtle">\u0441\u0438\u043d\u0445\u0440\u043e\u043d\u0438\u0437\u0438\u0440\u043e\u0432\u0430\u043d\u043e {lastSyncAt}</span> : null}
          </>
        }
      />

      {groups.length === 0 ? <EmptyState title="\u041d\u0430 \u0441\u0435\u0433\u043e\u0434\u043d\u044f \u0432\u0441\u0451 \u0447\u0438\u0441\u0442\u043e" text="\u0417\u0434\u0435\u0441\u044c \u043f\u043e\u044f\u0432\u044f\u0442\u0441\u044f \u0434\u0435\u043b\u0430, \u0441\u043e\u0431\u044b\u0442\u0438\u044f, \u043d\u0430\u043f\u043e\u043c\u0438\u043d\u0430\u043d\u0438\u044f \u0438 \u043e\u0442\u043b\u043e\u0436\u0435\u043d\u043d\u044b\u0435 \u043e\u0442\u0432\u0435\u0442\u044b, \u043a\u043e\u0442\u043e\u0440\u044b\u0435 \u0442\u0440\u0435\u0431\u0443\u044e\u0442 \u0432\u043d\u0438\u043c\u0430\u043d\u0438\u044f \u0441\u0435\u0433\u043e\u0434\u043d\u044f." /> : null}

      {groups.map((group) => (
        <section key={group.key} className="sectionBlock">
          <div className="sectionHead">
            <h2>{group.label}</h2>
            <span>{group.items.length}</span>
          </div>
          <div className="plannerList">
            {group.items.map((item) => (
              <PlannerItemCard
                key={item.key}
                item={item}
                arrangeMode={arrangeMode}
                onOpen={() => onOpenItem(item.key)}
                onComplete={() => onCompleteItem(item.key)}
                onMoveUp={() => onMoveUp(item.key)}
                onMoveDown={() => onMoveDown(item.key)}
                onQuickShift={(preset) => onQuickShift(item.key, preset)}
              />
            ))}
          </div>
        </section>
      ))}
    </div>
  );
}
