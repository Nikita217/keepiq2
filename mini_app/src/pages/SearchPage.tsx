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
        eyebrow="Поиск"
        title="Найти старое за секунды"
        subtitle="Поиск становится главным инструментом по мере роста личной памяти: билеты, идеи, списки, заметки, напоминания и старые входящие находятся из одного поля."
        metrics={<span className="metricPill"><strong>{results.length}</strong> результатов</span>}
      />

      <label className="heroSearch">
        <span>Что ищем?</span>
        <input value={query} onChange={(event) => onQueryChange(event.target.value)} placeholder="билет в театр, идея для отпуска, корм для кота" />
      </label>

      {!query.trim() ? <EmptyState title="Начните поиск" text="Ищите по смыслу, фразе, человеку, месту, ссылке или фрагменту заметки." /> : null}
      {query.trim() && results.length === 0 ? <EmptyState title="Ничего не нашлось" text="Попробуйте переформулировать запрос короче или по смыслу." /> : null}

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
