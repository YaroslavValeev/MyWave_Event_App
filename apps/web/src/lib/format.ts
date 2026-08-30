const LAST_EVENT_KEY = "mywave_last_event_id";

export function formatEventDate(value: string | null | undefined): string {
  if (!value) return "—";
  try {
    const date = new Date(value);
    const defaultMorning = date.getHours() === 9 && date.getMinutes() === 0;
    const defaultEvening = date.getHours() === 21 && date.getMinutes() === 0;
    return new Intl.DateTimeFormat("ru-RU", {
      dateStyle: "medium",
      timeStyle: defaultMorning || defaultEvening ? undefined : "short",
    }).format(date);
  } catch {
    return value;
  }
}

export function formatEventPeriod(
  startsAt: string | null | undefined,
  endsAt: string | null | undefined,
): string {
  const start = formatEventDate(startsAt);
  const end = formatEventDate(endsAt);
  if (start === "—" && end === "—") return "Даты уточняются";
  if (start === end || end === "—") return start;
  return `${start} — ${end}`;
}

export function rememberLastEvent(eventId: string | number): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(LAST_EVENT_KEY, String(eventId));
}

export function getLastEventId(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(LAST_EVENT_KEY);
}

export function postLoginPath(nextFromQuery?: string | null): string {
  const candidate = (nextFromQuery || "").trim();
  if (candidate.startsWith("/") && !candidate.startsWith("//")) {
    return candidate;
  }
  const last = getLastEventId();
  return last ? `/events/${last}` : "/events";
}

export function loginHref(nextPath?: string): string {
  const next = nextPath || (typeof window !== "undefined" ? `${window.location.pathname}${window.location.hash}` : "/events");
  if (!next || next === "/login" || next.startsWith("/login?")) {
    return "/login";
  }
  return `/login?next=${encodeURIComponent(next)}`;
}
