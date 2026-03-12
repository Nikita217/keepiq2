import { FilterBar } from "../components/FilterBar";
import { Card } from "../components/Card";
import { SearchResult } from "../types";

export function SearchPage({ query, onQueryChange, results }: { query: string; onQueryChange: (value: string) => void; results: SearchResult[] }) {
  return (
    <div className="stack">
      <FilterBar query={query} onChange={onQueryChange} />
      <Card title="Результаты" meta="поиск по объектам, сущностям и входящим">
        <ul className="listClean">
          {results.map((result) => <li key={`${result.object_type}-${result.object_id}`}>{result.title} • {result.object_type} {result.snippet ? `• ${result.snippet}` : ""}</li>)}
        </ul>
      </Card>
    </div>
  );
}
