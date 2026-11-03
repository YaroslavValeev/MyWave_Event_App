import type { PublicationType } from "./api";

export type LocalPublicationDraft = {
  id: string;
  eventId: string;
  title: string;
  body: string;
  type: PublicationType;
  authorRole: string;
  imageDataUrl?: string;
  imageName?: string;
  status: "draft" | "queued";
  updatedAt: string;
};

const STORAGE_PREFIX = "mywave_publication_drafts:";

function storageKey(eventId: number | string): string {
  return `${STORAGE_PREFIX}${eventId}`;
}

export function listPublicationDrafts(eventId: number | string): LocalPublicationDraft[] {
  if (typeof window === "undefined") return [];
  try {
    const value = JSON.parse(localStorage.getItem(storageKey(eventId)) ?? "[]");
    return Array.isArray(value) ? (value as LocalPublicationDraft[]) : [];
  } catch {
    return [];
  }
}

export function savePublicationDraft(
  eventId: number | string,
  draft: Omit<LocalPublicationDraft, "id" | "eventId" | "updatedAt"> & { id?: string },
): LocalPublicationDraft {
  const current = listPublicationDrafts(eventId);
  const saved: LocalPublicationDraft = {
    ...draft,
    id: draft.id ?? crypto.randomUUID(),
    eventId: String(eventId),
    updatedAt: new Date().toISOString(),
  };
  const next = [saved, ...current.filter((item) => item.id !== saved.id)];
  localStorage.setItem(storageKey(eventId), JSON.stringify(next));
  return saved;
}

export function removePublicationDraft(eventId: number | string, draftId: string): void {
  if (typeof window === "undefined") return;
  const next = listPublicationDrafts(eventId).filter((item) => item.id !== draftId);
  localStorage.setItem(storageKey(eventId), JSON.stringify(next));
}
