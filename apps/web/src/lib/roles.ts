/** Роли Stage 1 — синхронно с packages/shared-schema и services/api. */

export const ROLES = [
  "participant",
  "organizer",
  "judge",
  "commentator",
  "media",
  "support",
  "federation_manager",
  "event_admin",
  "platform_admin",
] as const;

export type Role = (typeof ROLES)[number];

export const ROLE_LABELS: Record<Role, string> = {
  participant: "Участник",
  organizer: "Организатор",
  judge: "Судья",
  commentator: "Комментатор",
  media: "Медиа",
  support: "Поддержка",
  federation_manager: "Менеджер федерации",
  event_admin: "Админ события",
  platform_admin: "Админ платформы",
};

export const EVENT_STATUSES = [
  "draft",
  "published",
  "registration_open",
  "live",
  "completed",
  "cancelled",
] as const;

export type EventStatus = (typeof EVENT_STATUSES)[number];

export const EVENT_STATUS_LABELS: Record<EventStatus, string> = {
  draft: "Черновик",
  published: "Опубликовано",
  registration_open: "Регистрация открыта",
  live: "Идёт сейчас",
  completed: "Завершено",
  cancelled: "Отменено",
};

export function isRole(value: string): value is Role {
  return (ROLES as readonly string[]).includes(value);
}

export function isEventStatus(value: string): value is EventStatus {
  return (EVENT_STATUSES as readonly string[]).includes(value);
}
