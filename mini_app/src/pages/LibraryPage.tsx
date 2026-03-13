import { useMemo, useState } from "react";

import { EmptyState } from "../components/EmptyState";
import { LibraryCard } from "../components/LibraryCard";
import { ScreenHeader } from "../components/ScreenHeader";
import { LibraryCardItem, LibraryFilter } from "../types";

const FILTERS: Array<{ key: LibraryFilter; label: string }> = [
  { key: "all", label: "Все" },
  { key: "list", label: "Списки" },
  { key: "note", label: "Заметки" },
  { key: "idea", label: "Идеи" },
  { key: "saved", label: "Сохранённое" },
];

export function LibraryPage({ items, onOpen }: { items: LibraryCardItem[]; onOpen: (item: LibraryCardItem) => void }) {
  const [filter, setFilter] = useState<LibraryFilter>("all");
  const visibleItems = useMemo(() => items.filter((item) => (filter === "all" ? true : item.filterKind === filter)), [filter, items]);

  return (
    <div className="screenStack">
      <ScreenHeader
        eyebrow="Списки и заметки"
        title="Сохранённое без шума"
        subtitle="Здесь живут материалы без жёсткой даты: заметки, идеи, чеклисты и просто сохранённые материалы."
        metrics={<span className="metricPill"><strong>{items.length}</strong> материалов</span>}
      />

      <div className="segmentWrap">
        {FILTERS.map((item) => (
          <button key={item.key} type="button" className={filter === item.key ? "segment active" : "segment"} onClick={() => setFilter(item.key)}>
            {item.label}
          </button>
        ))}
      </div>

      {visibleItems.length === 0 ? (
        <EmptyState
          title="Пока пусто"
          text="Здесь появятся списки, заметки, идеи и сохранённые материалы без даты."
        />
      ) : null}
      <div className="cardList">
        {visibleItems.map((item) => <LibraryCard key={item.key} item={item} onOpen={() => onOpen(item)} />)}
      </div>
    </div>
  );
}