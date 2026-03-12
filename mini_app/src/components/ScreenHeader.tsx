import { ReactNode } from "react";

type ScreenHeaderProps = {
  eyebrow: string;
  title: string;
  subtitle: string;
  actions?: ReactNode;
  metrics?: ReactNode;
};

export function ScreenHeader({ eyebrow, title, subtitle, actions, metrics }: ScreenHeaderProps) {
  return (
    <header className="screenHeader">
      <div className="screenHeaderCopy">
        <p className="screenEyebrow">{eyebrow}</p>
        <h1>{title}</h1>
        <p className="screenSubtitle">{subtitle}</p>
      </div>
      {actions ? <div className="screenActions">{actions}</div> : null}
      {metrics ? <div className="metricPills">{metrics}</div> : null}
    </header>
  );
}
