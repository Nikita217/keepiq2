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
        eyebrow="Сегодня"
        title={title}
        subtitle={subtitle}
        actions={
          <div className="headerButtonRow">
            <button type="button" className={arrangeMode ? "ghost activeGhost" : "ghost"} onClick={onToggleArrange}>Порядок</button>
            <button type="button" className="ghost" onClick={onRefresh}>{isRefreshing ? "Обновляю..." : "Обновить"}</button>
          </div>
        }
        metrics={
          <>
            <span className="metricPill"><strong>{groups.reduce((sum, group) => sum + group.items.length, 0)}</strong> в фокусе</span>
            <span className="metricPill"><strong>{inboxCount}</strong> во входящих</span>
            <span className="metricPill alert"><strong>{overdueCount}</strong> просрочено</span>
            {lastSyncAt ? <span className="metricPill subtle">синхронизировано {lastSyncAt}</span> : null}
          </>
        }
      />

      {groups.length === 0 ? <EmptyState title="На сегодня всё чисто" text="Здесь появятся дела, события, напоминания и отложенные ответы, которые требуют внимания сегодня." /> : null}

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
