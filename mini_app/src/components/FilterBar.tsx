export function FilterBar({ query, onChange }: { query: string; onChange: (value: string) => void }) {
  return (
    <label className="searchBox">
      <span>Поиск</span>
      <input value={query} onChange={(event) => onChange(event.target.value)} placeholder="что я хотел купить для кота" />
    </label>
  );
}
