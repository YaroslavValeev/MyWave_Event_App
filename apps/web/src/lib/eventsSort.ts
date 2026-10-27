/** Partition and order events for Champ App Events screen / home featured. */

import type { EventOut } from "./api";

function startMs(event: EventOut): number {
  if (!event.starts_at) return Number.POSITIVE_INFINITY;
  const t = Date.parse(event.starts_at);
  return Number.isFinite(t) ? t : Number.POSITIVE_INFINITY;
}

function endMs(event: EventOut): number {
  if (!event.ends_at) return Number.POSITIVE_INFINITY;
  const t = Date.parse(event.ends_at);
  return Number.isFinite(t) ? t : Number.POSITIVE_INFINITY;
}

export type EventBuckets = {
  live: EventOut[];
  upcoming: EventOut[];
  archive: EventOut[];
  other: EventOut[];
};

/** Split by status + chronology. «Ближайшие» = будущие по starts_at, не items[0]. */
export function partitionEvents(events: EventOut[], now = Date.now()): EventBuckets {
  const live: EventOut[] = [];
  const upcoming: EventOut[] = [];
  const archive: EventOut[] = [];
  const other: EventOut[] = [];

  for (const event of events) {
    if (event.status === "live") {
      live.push(event);
      continue;
    }
    if (event.status === "completed" || event.status === "cancelled") {
      archive.push(event);
      continue;
    }
    const start = startMs(event);
    const end = endMs(event);
    if (start > now || (event.status === "published" || event.status === "registration_open")) {
      if (end < now && event.ends_at) {
        archive.push(event);
      } else {
        upcoming.push(event);
      }
      continue;
    }
    other.push(event);
  }

  live.sort((a, b) => startMs(a) - startMs(b));
  upcoming.sort((a, b) => startMs(a) - startMs(b));
  archive.sort((a, b) => endMs(b) - endMs(a));
  return { live, upcoming, archive, other };
}

/** Featured «ближайшее»: live first, else earliest upcoming by starts_at. */
export function pickNearestEvent(events: EventOut[], now = Date.now()): EventOut | null {
  const { live, upcoming } = partitionEvents(events, now);
  if (live.length > 0) return live[0];
  if (upcoming.length > 0) return upcoming[0];
  return null;
}
