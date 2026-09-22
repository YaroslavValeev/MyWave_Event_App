/** Русские лейблы статусов и типов — SoT для UI, коды API не меняем. */

export const RESULT_STATUS_LABELS: Record<string, string> = {
  draft: "Черновик",
  verified: "Проверен",
  published: "Опубликован",
  void: "Аннулирован",
};

export const APPLICATION_STATUS_LABELS: Record<string, string> = {
  draft: "Черновик",
  submitted: "На рассмотрении",
  pending: "На рассмотрении",
  accepted: "В составе",
  rejected: "Отклонена",
  registered: "В составе",
};

export const HEAT_STATUS_LABELS: Record<string, string> = {
  planned: "Запланирован",
  ready: "Готов",
  on_water: "На воде",
  completed: "Завершён",
  cancelled: "Отменён",
};

export const ENTRY_STATUS_LABELS: Record<string, string> = {
  scheduled: "В списке",
  checked_in: "Регистрация",
  ready: "Готов",
  on_water: "На воде",
  completed: "Финиш",
  dns: "Не стартовал",
  dnf: "Не финишировал",
};

export const PROTOCOL_STATUS_LABELS: Record<string, string> = {
  draft: "Черновик",
  verified: "Проверен",
  published: "Опубликован",
  rejected: "Отклонён",
};

export const PROTOCOL_KIND_LABELS: Record<string, string> = {
  judge_sheet: "Лист судьи",
  chief_protocol: "Протокол главного судьи",
  photo_result: "Фото табло",
  other: "Другое",
};

export const DOCUMENT_KIND_LABELS: Record<string, string> = {
  bulletin: "Бюллетень",
  protocol: "Протокол",
  schedule: "Расписание",
  rules: "Правила",
  start_list: "Стартовый список",
  questionnaire: "Анкета / реестр",
  official_appointment: "Назначение судей",
  rulebook: "Регламент",
  other: "Другое",
};

export const DOWNLOAD_STATE_LABELS: Record<string, string> = {
  loading: "Проверяем файл…",
  available: "Файл доступен",
  unavailable: "Файл временно недоступен",
  error: "Ошибка скачивания",
  success: "Скачивание запущено",
};

export const FIELD_POV_LABELS: Record<string, string> = {
  backstage: "За кулисами",
  boat_pilot: "Глазами пилота",
  start_marshal: "Маршал на старте",
  on_water: "На воде",
  crowd: "Зрители и эмоции",
  other: "Другой момент",
};

export const FIELD_MOMENT_STATUS_LABELS: Record<string, string> = {
  draft: "Черновик команды",
  approved: "Для эфира",
  withheld: "Скрыт",
};

export function labelOf(map: Record<string, string>, value: string | null | undefined): string {
  if (!value) return "—";
  return map[value] ?? value;
}

/** Primary next status for start-list entry (Live Heat contextual CTA). */
export function nextEntryStatus(current: string): string | null {
  const flow: Record<string, string> = {
    scheduled: "checked_in",
    checked_in: "ready",
    ready: "on_water",
    on_water: "completed",
  };
  return flow[current] ?? null;
}

export function nextEntryStatusLabel(current: string): string | null {
  const next = nextEntryStatus(current);
  return next ? labelOf(ENTRY_STATUS_LABELS, next) : null;
}

/** Primary next heat status. */
export function nextHeatStatus(current: string): string | null {
  const flow: Record<string, string> = {
    planned: "ready",
    ready: "on_water",
    on_water: "completed",
  };
  return flow[current] ?? null;
}

export function nextHeatStatusLabel(current: string): string | null {
  const next = nextHeatStatus(current);
  return next ? labelOf(HEAT_STATUS_LABELS, next) : null;
}
