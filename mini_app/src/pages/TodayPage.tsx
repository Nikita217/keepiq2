import { EmptyState } from "../components/EmptyState";
import { PlannerItemCard } from "../components/PlannerItemCard";
import { ScreenHeader } from "../components/ScreenHeader";
import { TodayGroup } from "../types";

export function TodayPage({
  title,
  subtitle,
  groups,
  completedGroup,
  inboxCount,
  overdueCount,
  arrangeMode,
  onToggleArrange,
  onOpenItem,
  onCompleteItem,
  onQuickShift,
  onMoveUp,
  onMoveDown,
}: {
  title: string;
  subtitle: string;
  groups: TodayGroup[];
  completedGroup: TodayGroup | null;
  inboxCount: number;
  overdueCount: number;
  arrangeMode: boolean;
  onToggleArrange: () => void;
  onOpenItem: (itemKey: string) => void;
  onCompleteItem: (itemKey: string) => void;
  onQuickShift: (itemKey: string, preset: "evening" | "tomorrow") => void;
  onMoveUp: (itemKey: string) => void;
  onMoveDown: (itemKey: string) => void;
}) {
  const activeCount = groups.reduce((sum, group) => sum + group.items.length, 0);
  const completedCount = completedGroup?.items.length ?? 0;

  return (
    <div className="screenStack">
      <ScreenHeader
        eyebrow="\u0421\u0435\u0433\u043e\u0434\u043d\u044f"
        title={title}
        subtitle={subtitle}
        actions={
          <div className="headerButtonRow">
            <button type="button" className={arrangeMode ? "ghost activeGhost" : "ghost"} onClick={onToggleArrange}>
              \u041f\u043e\u0440\u044f\u0434\u043e\u043a
            </button>
          </div>
        }
        metrics={
          <>
            <span className="metricPill"><strong>{activeCount}</strong> \u0432 \u0444\u043e\u043a\u0443\u0441\u0435</span>
            <span className="metricPill"><strong>{inboxCount}</strong> \u0432\u043e \u0432\u0445\u043e\u0434\u044f\u0449\u0438\u0445</span>
            {overdueCount > 0 ? <span className="metricPill alert"><strong>{overdueCount}</strong> \u043f\u0440\u043e\u0441\u0440\u043e\u0447\u0435\u043d\u043e</span> : null}
            {completedCount > 0 ? <span className="metricPill subtle"><strong>{completedCount}</strong> \u0432\u044b\u043f\u043e\u043b\u043d\u0435\u043d\u043e</span> : null}
          </>
        }
      />

      {groups.length === 0 ? (
        <EmptyState
          title="\u041d\u0430 \u0441\u0435\u0433\u043e\u0434\u043d\u044f \u0432\u0441\u0451 \u0447\u0438\u0441\u0442\u043e"
          text="\u0417\u0434\u0435\u0441\u044c \u043f\u043e\u044f\u0432\u044f\u0442\u0441\u044f \u0434\u0435\u043b\u0430, \u0441\u043e\u0431\u044b\u0442\u0438\u044f, \u043d\u0430\u043f\u043e\u043c\u0438\u043d\u0430\u043d\u0438\u044f \u0438 \u043e\u0442\u043b\u043e\u0436\u0435\u043d\u043d\u044b\u0435 \u043e\u0442\u0432\u0435\u0442\u044b, \u043a\u0430\u043a \u0442\u043e\u043b\u044c\u043a\u043e \u043f\u043e\u044f\u0432\u0438\u0442\u0441\u044f \u0447\u0442\u043e-\u0442\u043e \u0432\u0430\u0436\u043d\u043e\u0435 \u043d\u0430 \u044d\u0442\u043e\u0442 \u0434\u0435\u043d\u044c."
        />
      ) : null}

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

      {completedGroup ? (
        <section className="sectionBlock">
          <div className="sectionHead">
            <h2>{completedGroup.label}</h2>
            <span>{completedGroup.items.length}</span>
          </div>
          <div className="plannerList">
            {completedGroup.items.map((item) => (
              <PlannerItemCard
                key={item.key}
                item={item}
                arrangeMode={false}
                onOpen={() => onOpenItem(item.key)}
                onComplete={() => undefined}
                onMoveUp={() => undefined}
                onMoveDown={() => undefined}
                onQuickShift={() => undefined}
              />
            ))}
          </div>
        </section>
      ) : null}
    </div>
  );
}