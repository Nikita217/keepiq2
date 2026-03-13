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
        eyebrow="Входящие"
        title="Спокойный разбор"
        subtitle="Здесь лежит всё новое, неуверенное и требующее подтверждения. Всё это можно спокойно разобрать, не загромождая экран сегодня."
        metrics={
          <>
            <span className="metricPill alert"><strong>{urgent.length}</strong> требуют решения</span>
            <span className="metricPill"><strong>{quiet.length}</strong> можно разобрать позже</span>
          </>
        }
      />

      {urgent.length === 0 && quiet.length === 0 ? (
        <EmptyState
          title="Входящие пусты"
          text="Новые сообщения, голосовые, фото и ссылки появятся здесь до подтверждения."
        />
      ) : null}

      {urgent.length ? (
        <section className="sectionBlock">
          <div className="sectionHead">
            <h2>Сначала разберите это</h2>
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
            <h2>Можно оставить во входящих</h2>
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