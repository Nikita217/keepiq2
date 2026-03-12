declare global {
  interface Window {
    Telegram?: {
      WebApp?: {
        initData?: string;
        ready?: () => void;
        expand?: () => void;
      };
    };
  }
}

export function getInitData(): string | null {
  return window.Telegram?.WebApp?.initData ?? null;
}

export function prepareTelegramWebApp(): void {
  window.Telegram?.WebApp?.ready?.();
  window.Telegram?.WebApp?.expand?.();
}
