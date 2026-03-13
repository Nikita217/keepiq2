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
        eyebrow="Сегодня"
        title={title}
        subtitle={subtitle}
        actions={
          <div className="headerButtonRow">
            <button type="button" className={arrangeMode ? "ghost activeGhost" : "ghost"} onClick={onToggleArrange}>
              Порядок
            </button>
          </div>
        }
        metrics={
          <>
            <span className="metricPill"><strong>{activeCount}</strong> в фокусе</span>
            <span className="metricPill"><strong>{inboxCount}</strong> во входящих</span>
            {overdueCount > 0 ? <span className="metricPill alert"><strong>{overdueCount}</strong> просрочено</span> : null}
            {completedCount > 0 ? <span className="metricPill subtle"><strong>{completedCount}</strong> выполнено</span> : null}
          </>
        }
      />

      {groups.length === 0 ? (
        <EmptyState
          title="На сегодня всё чисто"
          text="Здесь появятся дела, события, напоминания и отложенные ответы, как только появится что-то важное на этот день."
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