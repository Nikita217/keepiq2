import type { ReactNode } from "react";

export function Card({ title, meta, children }: { title: string; meta?: string; children: ReactNode }) {
  return (
    <section className="card">
      <div className="cardHead">
        <h3>{title}</h3>
        {meta ? <span>{meta}</span> : null}
      </div>
      {children}
    </section>
  );
}
