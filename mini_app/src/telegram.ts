declare global {
  interface Window {
    Telegram?: {
      WebApp?: {
        initData?: string;
        initDataUnsafe?: {
          user?: {
            id?: number;
            first_name?: string;
            username?: string;
          };
        };
        ready?: () => void;
        expand?: () => void;
      };
    };
  }
}

export function getInitData(): string | null {
  return window.Telegram?.WebApp?.initData ?? null;
}

export function getTelegramUserId(): number | null {
  return window.Telegram?.WebApp?.initDataUnsafe?.user?.id ?? null;
}

export function isInsideTelegram(): boolean {
  return Boolean(window.Telegram?.WebApp);
}

export function prepareTelegramWebApp(): void {
  window.Telegram?.WebApp?.ready?.();
  window.Telegram?.WebApp?.expand?.();
}