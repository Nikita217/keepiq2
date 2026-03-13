const LOCALE = "ru-RU";

export function parseDate(value: string | null | undefined): Date | null {
  if (!value) {
    return null;
  }
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? null : parsed;
}

export function startOfDay(date = new Date()): Date {
  return new Date(date.getFullYear(), date.getMonth(), date.getDate(), 0, 0, 0, 0);
}

export function endOfDay(date = new Date()): Date {
  return new Date(date.getFullYear(), date.getMonth(), date.getDate(), 23, 59, 59, 999);
}

export function dayKey(date: Date): string {
  const year = date.getFullYear();
  const month = `${date.getMonth() + 1}`.padStart(2, "0");
  const day = `${date.getDate()}`.padStart(2, "0");
  return `${year}-${month}-${day}`;
}

export function isSameDay(left: Date, right: Date): boolean {
  return dayKey(left) === dayKey(right);
}

export function formatDayLabel(date: Date): string {
  return new Intl.DateTimeFormat(LOCALE, { weekday: "long", day: "numeric", month: "long" }).format(date);
}

export function formatShortDate(value: string | Date | null | undefined): string {
  const date = value instanceof Date ? value : parseDate(value ?? null);
  if (!date) {
    return "\u0411\u0435\u0437 \u0434\u0430\u0442\u044b";
  }
  return new Intl.DateTimeFormat(LOCALE, { day: "numeric", month: "short" }).format(date);
}

export function formatLongDateTime(value: string | Date | null | undefined): string {
  const date = value instanceof Date ? value : parseDate(value ?? null);
  if (!date) {
    return "\u0411\u0435\u0437 \u0434\u0430\u0442\u044b";
  }
  return new Intl.DateTimeFormat(LOCALE, {
    day: "numeric",
    month: "long",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

export function formatTime(value: string | Date | null | undefined): string {
  const date = value instanceof Date ? value : parseDate(value ?? null);
  if (!date) {
    return "\u0411\u0435\u0437 \u0432\u0440\u0435\u043c\u0435\u043d\u0438";
  }
  return new Intl.DateTimeFormat(LOCALE, { hour: "2-digit", minute: "2-digit" }).format(date);
}

export function toDateInputValue(value: string | null | undefined): string {
  const date = parseDate(value ?? null);
  if (!date) {
    return "";
  }
  const local = new Date(date.getTime() - date.getTimezoneOffset() * 60000);
  return local.toISOString().slice(0, 10);
}

export function toTimeInputValue(value: string | null | undefined): string {
  const date = parseDate(value ?? null);
  if (!date) {
    return "";
  }
  const local = new Date(date.getTime() - date.getTimezoneOffset() * 60000);
  return local.toISOString().slice(11, 16);
}

export function mergeDateAndTime(dateValue: string, timeValue: string): string | null {
  if (!dateValue) {
    return null;
  }
  const normalizedTime = timeValue || "09:00";
  return new Date(`${dateValue}T${normalizedTime}:00`).toISOString();
}

export function withTime(date: Date, hours: number, minutes: number): string {
  const next = new Date(date);
  next.setHours(hours, minutes, 0, 0);
  return next.toISOString();
}
