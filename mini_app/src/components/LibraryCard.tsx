import { LibraryCardItem } from "../types";
import { formatShortDate } from "../utils/date";

export function LibraryCard({ item, onOpen }: { item: LibraryCardItem; onOpen: () => void }) {
  return (
    <button type="button" className="libraryCard" onClick={onOpen}>
      <div className="libraryTop">
        <span className={`kindBadge kind-${item.kind}`}>{item.meta}</span>
        <span className="libraryDate">{formatShortDate(item.updated_at)}</span>
      </div>
      <strong>{item.title}</strong>
      {item.preview ? <p>{item.preview}</p> : null}
      <div className="libraryBottom">
        {item.progress ? <span>{item.progress}</span> : <span>{item.tags.join(" · ")}</span>}
      </div>
    </button>
  );
}
