export function EmptyState({ title, text }: { title: string; text: string }) {
  return (
    <section className="emptyPanel">
      <h3>{title}</h3>
      <p>{text}</p>
    </section>
  );
}
