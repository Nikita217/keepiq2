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

function getWebApp() {
  return window.Telegram?.WebApp ?? null;
}

export function getInitData(): string | null {
  return getWebApp()?.initData ?? null;
}

export function getTelegramUserId(): number | null {
  return getWebApp()?.initDataUnsafe?.user?.id ?? null;
}

export function isInsideTelegram(): boolean {
  return Boolean(getWebApp());
}

export function isLocalDevHost(): boolean {
  return ["localhost", "127.0.0.1"].includes(window.location.hostname);
}

export function prepareTelegramWebApp(): void {
  getWebApp()?.ready?.();
  getWebApp()?.expand?.();
}

export async function waitForTelegramInitData(timeoutMs = 2500): Promise<string | null> {
  if (!isInsideTelegram()) {
    return getInitData();
  }

  const deadline = Date.now() + timeoutMs;
  let initData = getInitData();
  while (!initData && Date.now() < deadline) {
    await new Promise((resolve) => window.setTimeout(resolve, 50));
    initData = getInitData();
  }
  return initData;
}

export function getTelegramDebugState() {
  return {
    insideTelegram: isInsideTelegram(),
    hasInitData: Boolean(getInitData()),
    telegramUserId: getTelegramUserId(),
    locationHost: window.location.host,
    locationHref: window.location.href,
  };
}
