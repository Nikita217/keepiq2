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
  onResolve: (item: IncomingItem, payload: { targetType?: string; suggestedActionId?: number }) => void;
}) {
  return (
    <div className="screenStack">
      <ScreenHeader
        eyebrow="Р’С…РѕРґСЏС‰РёРµ"
        title="РЎРїРѕРєРѕР№РЅС‹Р№ СЂР°Р·Р±РѕСЂ"
        subtitle="Р—РґРµСЃСЊ Р»РµР¶РёС‚ РІСЃС‘ РЅРѕРІРѕРµ, РЅРµСѓРІРµСЂРµРЅРЅРѕРµ Рё С‚СЂРµР±СѓСЋС‰РµРµ РїРѕРґС‚РІРµСЂР¶РґРµРЅРёСЏ. Р’СЃС‘ СЌС‚Рѕ РјРѕР¶РЅРѕ СЃРїРѕРєРѕР№РЅРѕ СЂР°Р·РѕР±СЂР°С‚СЊ, РЅРµ Р·Р°РіСЂРѕРјРѕР¶РґР°СЏ СЌРєСЂР°РЅ СЃРµРіРѕРґРЅСЏ."
        metrics={
          <>
            <span className="metricPill alert"><strong>{urgent.length}</strong> С‚СЂРµР±СѓСЋС‚ СЂРµС€РµРЅРёСЏ</span>
            <span className="metricPill"><strong>{quiet.length}</strong> РјРѕР¶РЅРѕ СЂР°Р·РѕР±СЂР°С‚СЊ РїРѕР·Р¶Рµ</span>
          </>
        }
      />

      {urgent.length === 0 && quiet.length === 0 ? (
        <EmptyState
          title="Р’С…РѕРґСЏС‰РёРµ РїСѓСЃС‚С‹"
          text="РќРѕРІС‹Рµ СЃРѕРѕР±С‰РµРЅРёСЏ, РіРѕР»РѕСЃРѕРІС‹Рµ, С„РѕС‚Рѕ Рё СЃСЃС‹Р»РєРё РїРѕСЏРІСЏС‚СЃСЏ Р·РґРµСЃСЊ РґРѕ РїРѕРґС‚РІРµСЂР¶РґРµРЅРёСЏ."
        />
      ) : null}

      {urgent.length ? (
        <section className="sectionBlock">
          <div className="sectionHead">
            <h2>РЎРЅР°С‡Р°Р»Р° СЂР°Р·Р±РµСЂРёС‚Рµ СЌС‚Рѕ</h2>
            <span>{urgent.length}</span>
          </div>
          <div className="cardList">
            {urgent.map((item) => <InboxCard key={item.id} item={item} onOpen={() => onOpen(item)} onResolve={(payload) => onResolve(item, payload)} />)}
          </div>
        </section>
      ) : null}

      {quiet.length ? (
        <section className="sectionBlock">
          <div className="sectionHead">
            <h2>РњРѕР¶РЅРѕ РѕСЃС‚Р°РІРёС‚СЊ РІРѕ РІС…РѕРґСЏС‰РёС…</h2>
            <span>{quiet.length}</span>
          </div>
          <div className="cardList">
            {quiet.map((item) => <InboxCard key={item.id} item={item} onOpen={() => onOpen(item)} onResolve={(payload) => onResolve(item, payload)} />)}
          </div>
        </section>
      ) : null}
    </div>
  );
}

