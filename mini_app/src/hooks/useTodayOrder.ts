import { useEffect, useMemo, useState } from "react";

const STORAGE_KEY = "keepiq.today.order";

function readStoredOrder(): string[] {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    return raw ? (JSON.parse(raw) as string[]) : [];
  } catch {
    return [];
  }
}

export function useTodayOrder(itemKeys: string[]) {
  const [order, setOrder] = useState<string[]>(() => readStoredOrder());
  const itemKeySignature = itemKeys.join("|");

  useEffect(() => {
    setOrder((current) => {
      const seen = new Set(itemKeys);
      const next = [...current.filter((key) => seen.has(key)), ...itemKeys.filter((key) => !current.includes(key))];
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
      return next;
    });
  }, [itemKeySignature, itemKeys]);

  const orderMap = useMemo(() => new Map(order.map((key, index) => [key, index])), [order]);

  function move(itemKey: string, direction: -1 | 1) {
    setOrder((current) => {
      const next = [...current];
      const index = next.indexOf(itemKey);
      if (index === -1) {
        return current;
      }
      const targetIndex = index + direction;
      if (targetIndex < 0 || targetIndex >= next.length) {
        return current;
      }
      [next[index], next[targetIndex]] = [next[targetIndex], next[index]];
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
      return next;
    });
  }

  return { orderMap, moveUp: (itemKey: string) => move(itemKey, -1), moveDown: (itemKey: string) => move(itemKey, 1) };
}
