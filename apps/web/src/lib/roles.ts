/** Роли Stage 1 — синхронно с packages/shared-schema и services/api. */

export const ROLES = [
  "participant",
  "organizer",
  "judge",
  "chief_judge",
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
  chief_judge: "Главный судья",
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

export function isStaffRole(value: string): boolean {
  return (
    value === "organizer" ||
    value === "federation_manager" ||
    value === "event_admin" ||
    value === "platform_admin"
  );
}

export function isJudgeRole(value: string | undefined | null): boolean {
  return value === "judge" || value === "chief_judge" || isStaffRole(value ?? "");
}

export function isChiefJudgeRole(value: string | undefined | null): boolean {
  return value === "chief_judge";
}

export function canPublishOfficialResults(value: string | undefined | null): boolean {
  return value === "chief_judge" || value === "platform_admin";
}

export function isBroadcastRole(value: string | undefined | null): boolean {
  return value === "commentator" || value === "media";
}

export function canCaptureFieldMoments(value: string | undefined | null): boolean {
  return (
    isStaffRole(value ?? "") ||
    isBroadcastRole(value) ||
    value === "support" ||
    value === "chief_judge"
  );
}

/** Организатор+ и главный судья могут отдать кадр в эфир или скрыть. */
export function canModerateFieldMoments(value: string | undefined | null): boolean {
  return isStaffRole(value ?? "") || value === "chief_judge";
}

/** Self-serve staff request — без platform_admin / event_admin. */
export const REQUESTABLE_STAFF_ROLES = [
  "judge",
  "chief_judge",
  "organizer",
  "commentator",
  "media",
  "support",
  "federation_manager",
] as const satisfies readonly Role[];
