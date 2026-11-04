/** Local offline queue for judge score sheets (SCORE-13C). Never auto-publishes results. */

export type LocalScoreDraft = {
  id: string;
  eventId: string;
  participant_id: number;
  heat_id: number | null;
  attempt_no: number;
  criteria: Record<string, number>;
  notes?: string;
  expected_version: number | null;
  idempotency_key: string;
  status: "queued" | "conflict";
  lastError?: string;
  updatedAt: string;
};

const STORAGE_PREFIX = "mywave_score_drafts:";

function storageKey(eventId: number | string): string {
  return `${STORAGE_PREFIX}${eventId}`;
}

export function listScoreDrafts(eventId: number | string): LocalScoreDraft[] {
  if (typeof window === "undefined") return [];
  try {
    const value = JSON.parse(localStorage.getItem(storageKey(eventId)) ?? "[]");
    return Array.isArray(value) ? (value as LocalScoreDraft[]) : [];
  } catch {
    return [];
  }
}

export function saveScoreDraft(
  eventId: number | string,
  draft: Omit<LocalScoreDraft, "id" | "eventId" | "updatedAt"> & { id?: string },
): LocalScoreDraft {
  const current = listScoreDrafts(eventId);
  const saved: LocalScoreDraft = {
    ...draft,
    id: draft.id ?? crypto.randomUUID(),
    eventId: String(eventId),
    updatedAt: new Date().toISOString(),
  };
  const next = [saved, ...current.filter((item) => item.id !== saved.id)];
  localStorage.setItem(storageKey(eventId), JSON.stringify(next));
  return saved;
}

export function removeScoreDraft(eventId: number | string, draftId: string): void {
  if (typeof window === "undefined") return;
  const next = listScoreDrafts(eventId).filter((item) => item.id !== draftId);
  localStorage.setItem(storageKey(eventId), JSON.stringify(next));
}

export function markScoreDraftConflict(
  eventId: number | string,
  draftId: string,
  lastError: string,
): void {
  const current = listScoreDrafts(eventId);
  const next = current.map((item) =>
    item.id === draftId
      ? { ...item, status: "conflict" as const, lastError, updatedAt: new Date().toISOString() }
      : item,
  );
  localStorage.setItem(storageKey(eventId), JSON.stringify(next));
}
