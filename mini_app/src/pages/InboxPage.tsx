import { EmptyState } from "../components/EmptyState";
import { InboxCard } from "../components/InboxCard";
import { ScreenHeader } from "../components/ScreenHeader";
import { IncomingItem } from "../types";

export function InboxPage({
  urgent,
  quiet,
  onOpen,
  onResolve,
}: {
  urgent: IncomingItem[];
  quiet: IncomingItem[];
  onOpen: (item: IncomingItem) => void;
  onResolve: (item: IncomingItem, targetType: string) => void;
}) {
  return (
    <div className="screenStack">
      <ScreenHeader
        eyebrow="\u0412\u0445\u043e\u0434\u044f\u0449\u0438\u0435"
        title="\u0421\u043f\u043e\u043a\u043e\u0439\u043d\u044b\u0439 \u0440\u0430\u0437\u0431\u043e\u0440"
        subtitle="\u0417\u0434\u0435\u0441\u044c \u043b\u0435\u0436\u0438\u0442 \u0432\u0441\u0451 \u043d\u043e\u0432\u043e\u0435, \u043d\u0435\u0443\u0432\u0435\u0440\u0435\u043d\u043d\u043e\u0435 \u0438 \u0442\u0440\u0435\u0431\u0443\u044e\u0449\u0435\u0435 \u043f\u043e\u0434\u0442\u0432\u0435\u0440\u0436\u0434\u0435\u043d\u0438\u044f. \u0412\u0441\u0451 \u044d\u0442\u043e \u043c\u043e\u0436\u043d\u043e \u0441\u043f\u043e\u043a\u043e\u0439\u043d\u043e \u0440\u0430\u0437\u043e\u0431\u0440\u0430\u0442\u044c, \u043d\u0435 \u0437\u0430\u0433\u0440\u043e\u043c\u043e\u0436\u0434\u0430\u044f \u044d\u043a\u0440\u0430\u043d \u0441\u0435\u0433\u043e\u0434\u043d\u044f."
        metrics={
          <>
            <span className="metricPill alert"><strong>{urgent.length}</strong> \u0442\u0440\u0435\u0431\u0443\u044e\u0442 \u0440\u0435\u0448\u0435\u043d\u0438\u044f</span>
            <span className="metricPill"><strong>{quiet.length}</strong> \u043c\u043e\u0436\u043d\u043e \u0440\u0430\u0437\u043e\u0431\u0440\u0430\u0442\u044c \u043f\u043e\u0437\u0436\u0435</span>
          </>
        }
      />

      {urgent.length === 0 && quiet.length === 0 ? (
        <EmptyState
          title="\u0412\u0445\u043e\u0434\u044f\u0449\u0438\u0435 \u043f\u0443\u0441\u0442\u044b"
          text="\u041d\u043e\u0432\u044b\u0435 \u0441\u043e\u043e\u0431\u0449\u0435\u043d\u0438\u044f, \u0433\u043e\u043b\u043e\u0441\u043e\u0432\u044b\u0435, \u0444\u043e\u0442\u043e \u0438 \u0441\u0441\u044b\u043b\u043a\u0438 \u043f\u043e\u044f\u0432\u044f\u0442\u0441\u044f \u0437\u0434\u0435\u0441\u044c \u0434\u043e \u043f\u043e\u0434\u0442\u0432\u0435\u0440\u0436\u0434\u0435\u043d\u0438\u044f."
        />
      ) : null}

      {urgent.length ? (
        <section className="sectionBlock">
          <div className="sectionHead">
            <h2>\u0421\u043d\u0430\u0447\u0430\u043b\u0430 \u0440\u0430\u0437\u0431\u0435\u0440\u0438\u0442\u0435 \u044d\u0442\u043e</h2>
            <span>{urgent.length}</span>
          </div>
          <div className="cardList">
            {urgent.map((item) => <InboxCard key={item.id} item={item} onOpen={() => onOpen(item)} onResolve={(targetType) => onResolve(item, targetType)} />)}
          </div>
        </section>
      ) : null}

      {quiet.length ? (
        <section className="sectionBlock">
          <div className="sectionHead">
            <h2>\u041c\u043e\u0436\u043d\u043e \u043e\u0441\u0442\u0430\u0432\u0438\u0442\u044c \u0432\u043e \u0432\u0445\u043e\u0434\u044f\u0449\u0438\u0445</h2>
            <span>{quiet.length}</span>
          </div>
          <div className="cardList">
            {quiet.map((item) => <InboxCard key={item.id} item={item} onOpen={() => onOpen(item)} onResolve={(targetType) => onResolve(item, targetType)} />)}
          </div>
        </section>
      ) : null}
    </div>
  );
}