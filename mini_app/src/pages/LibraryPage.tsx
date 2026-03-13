import { useMemo, useState } from "react";

import { EmptyState } from "../components/EmptyState";
import { LibraryCard } from "../components/LibraryCard";
import { ScreenHeader } from "../components/ScreenHeader";
import { LibraryCardItem, LibraryFilter } from "../types";

const FILTERS: Array<{ key: LibraryFilter; label: string }> = [
  { key: "all", label: "\u0412\u0441\u0435" },
  { key: "list", label: "\u0421\u043f\u0438\u0441\u043a\u0438" },
  { key: "note", label: "\u0417\u0430\u043c\u0435\u0442\u043a\u0438" },
  { key: "idea", label: "\u0418\u0434\u0435\u0438" },
  { key: "saved", label: "\u0421\u043e\u0445\u0440\u0430\u043d\u0451\u043d\u043d\u043e\u0435" },
];

export function LibraryPage({ items, onOpen }: { items: LibraryCardItem[]; onOpen: (item: LibraryCardItem) => void }) {
  const [filter, setFilter] = useState<LibraryFilter>("all");
  const visibleItems = useMemo(() => items.filter((item) => (filter === "all" ? true : item.filterKind === filter)), [filter, items]);

  return (
    <div className="screenStack">
      <ScreenHeader
        eyebrow="\u0421\u043f\u0438\u0441\u043a\u0438 \u0438 \u0437\u0430\u043c\u0435\u0442\u043a\u0438"
        title="\u0421\u043e\u0445\u0440\u0430\u043d\u0451\u043d\u043d\u043e\u0435 \u0431\u0435\u0437 \u0448\u0443\u043c\u0430"
        subtitle="\u0417\u0434\u0435\u0441\u044c \u0436\u0438\u0432\u0443\u0442 \u043c\u0430\u0442\u0435\u0440\u0438\u0430\u043b\u044b \u0431\u0435\u0437 \u0436\u0451\u0441\u0442\u043a\u043e\u0439 \u0434\u0430\u0442\u044b: \u0437\u0430\u043c\u0435\u0442\u043a\u0438, \u0438\u0434\u0435\u0438, \u0447\u0435\u043a\u043b\u0438\u0441\u0442\u044b \u0438 \u043f\u0440\u043e\u0441\u0442\u043e \u0441\u043e\u0445\u0440\u0430\u043d\u0451\u043d\u043d\u044b\u0435 \u043c\u0430\u0442\u0435\u0440\u0438\u0430\u043b\u044b."
        metrics={<span className="metricPill"><strong>{items.length}</strong> \u043c\u0430\u0442\u0435\u0440\u0438\u0430\u043b\u043e\u0432</span>}
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
          title="\u041f\u043e\u043a\u0430 \u043f\u0443\u0441\u0442\u043e"
          text="\u0417\u0434\u0435\u0441\u044c \u043f\u043e\u044f\u0432\u044f\u0442\u0441\u044f \u0441\u043f\u0438\u0441\u043a\u0438, \u0437\u0430\u043c\u0435\u0442\u043a\u0438, \u0438\u0434\u0435\u0438 \u0438 \u0441\u043e\u0445\u0440\u0430\u043d\u0451\u043d\u043d\u044b\u0435 \u043c\u0430\u0442\u0435\u0440\u0438\u0430\u043b\u044b \u0431\u0435\u0437 \u0434\u0430\u0442\u044b."
        />
      ) : null}
      <div className="cardList">
        {visibleItems.map((item) => <LibraryCard key={item.key} item={item} onOpen={() => onOpen(item)} />)}
      </div>
    </div>
  );
}