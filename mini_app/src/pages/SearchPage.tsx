import { EmptyState } from "../components/EmptyState";
import { ScreenHeader } from "../components/ScreenHeader";
import { SearchResult } from "../types";
import { getTypeLabel } from "../utils/models";

export function SearchPage({
  query,
  onQueryChange,
  results,
  onOpen,
}: {
  query: string;
  onQueryChange: (value: string) => void;
  results: SearchResult[];
  onOpen: (result: SearchResult) => void;
}) {
  return (
    <div className="screenStack">
      <ScreenHeader
        eyebrow="\u041f\u043e\u0438\u0441\u043a"
        title="\u041d\u0430\u0439\u0442\u0438 \u0441\u0442\u0430\u0440\u043e\u0435 \u0437\u0430 \u0441\u0435\u043a\u0443\u043d\u0434\u044b"
        subtitle="\u041f\u043e\u0438\u0441\u043a \u0441\u0442\u0430\u043d\u043e\u0432\u0438\u0442\u0441\u044f \u0433\u043b\u0430\u0432\u043d\u044b\u043c \u0438\u043d\u0441\u0442\u0440\u0443\u043c\u0435\u043d\u0442\u043e\u043c \u043f\u043e \u043c\u0435\u0440\u0435 \u0440\u043e\u0441\u0442\u0430 \u043b\u0438\u0447\u043d\u043e\u0439 \u043f\u0430\u043c\u044f\u0442\u0438: \u0431\u0438\u043b\u0435\u0442\u044b, \u0438\u0434\u0435\u0438, \u0441\u043f\u0438\u0441\u043a\u0438, \u0437\u0430\u043c\u0435\u0442\u043a\u0438, \u043d\u0430\u043f\u043e\u043c\u0438\u043d\u0430\u043d\u0438\u044f \u0438 \u0441\u0442\u0430\u0440\u044b\u0435 \u0432\u0445\u043e\u0434\u044f\u0449\u0438\u0435 \u043d\u0430\u0445\u043e\u0434\u044f\u0442\u0441\u044f \u0438\u0437 \u043e\u0434\u043d\u043e\u0433\u043e \u043f\u043e\u043b\u044f."
        metrics={<span className="metricPill"><strong>{results.length}</strong> \u0440\u0435\u0437\u0443\u043b\u044c\u0442\u0430\u0442\u043e\u0432</span>}
      />

      <label className="heroSearch">
        <span>\u0427\u0442\u043e \u0438\u0449\u0435\u043c?</span>
        <input value={query} onChange={(event) => onQueryChange(event.target.value)} placeholder="\u0431\u0438\u043b\u0435\u0442 \u0432 \u0442\u0435\u0430\u0442\u0440, \u0438\u0434\u0435\u044f \u0434\u043b\u044f \u043e\u0442\u043f\u0443\u0441\u043a\u0430, \u043a\u043e\u0440\u043c \u0434\u043b\u044f \u043a\u043e\u0442\u0430" />
      </label>

      {!query.trim() ? <EmptyState title="\u041d\u0430\u0447\u043d\u0438\u0442\u0435 \u043f\u043e\u0438\u0441\u043a" text="\u0418\u0449\u0438\u0442\u0435 \u043f\u043e \u0441\u043c\u044b\u0441\u043b\u0443, \u0444\u0440\u0430\u0437\u0435, \u0447\u0435\u043b\u043e\u0432\u0435\u043a\u0443, \u043c\u0435\u0441\u0442\u0443, \u0441\u0441\u044b\u043b\u043a\u0435 \u0438\u043b\u0438 \u0444\u0440\u0430\u0433\u043c\u0435\u043d\u0442\u0443 \u0437\u0430\u043c\u0435\u0442\u043a\u0438." /> : null}
      {query.trim() && results.length === 0 ? <EmptyState title="\u041d\u0438\u0447\u0435\u0433\u043e \u043d\u0435 \u043d\u0430\u0448\u043b\u043e\u0441\u044c" text="\u041f\u043e\u043f\u0440\u043e\u0431\u0443\u0439\u0442\u0435 \u043f\u0435\u0440\u0435\u0444\u043e\u0440\u043c\u0443\u043b\u0438\u0440\u043e\u0432\u0430\u0442\u044c \u0437\u0430\u043f\u0440\u043e\u0441 \u043a\u043e\u0440\u043e\u0447\u0435 \u0438\u043b\u0438 \u043f\u043e \u0441\u043c\u044b\u0441\u043b\u0443." /> : null}

      <div className="cardList">
        {results.map((result) => (
          <button key={`${result.object_type}-${result.object_id}`} type="button" className="searchCard" onClick={() => onOpen(result)}>
            <div className="searchCardTop">
              <span className="kindBadge subtle">{getTypeLabel(result.object_type)}</span>
              {result.status ? <span>{result.status}</span> : null}
            </div>
            <strong>{result.title}</strong>
            {result.snippet ? <p>{result.snippet}</p> : null}
          </button>
        ))}
      </div>
    </div>
  );
}
