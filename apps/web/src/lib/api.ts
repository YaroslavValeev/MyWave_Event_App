import type { EventStatus, Role } from "./roles";

const TOKEN_KEY = "mywave_event_access_token";
const USER_KEY = "mywave_event_user";

export function getApiBaseUrl(): string {
  const base = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";
  return base.replace(/\/$/, "");
}

export class ApiError extends Error {
  readonly status: number;
  readonly code?: string;

  constructor(message: string, status: number, code?: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
  }
}

export type HealthResponse = {
  status: string;
  app: string;
  env: string;
  time: string;
  db_ok: boolean;
};

export type UserOut = {
  id: string;
  email: string;
  display_name: string;
  role: Role;
  status?: string;
  phone?: string | null;
  created_at?: string;
};

export type TokenResponse = {
  access_token: string;
  token_type: string;
  role: Role;
  email: string;
  user_id: number;
  status?: string;
  phone?: string | null;
  display_name?: string | null;
  user: UserOut;
};

type ApiTokenPayload = {
  access_token: string;
  token_type: string;
  role: Role;
  email: string;
  user_id: number;
  status?: string;
  phone?: string | null;
  display_name?: string | null;
};

function toTokenResponse(payload: ApiTokenPayload): TokenResponse {
  return {
    ...payload,
    user: {
      id: String(payload.user_id),
      email: payload.email,
      display_name: payload.display_name ?? payload.email,
      role: payload.role,
      status: payload.status ?? "active",
      phone: payload.phone ?? null,
    },
  };
}

export type EventOut = {
  id: number | string;
  slug: string;
  title: string;
  description: string | null;
  city?: string | null;
  location?: string | null;
  venue?: string | null;
  disciplines?: string | null;
  starts_at: string | null;
  ends_at: string | null;
  status: EventStatus | string;
  created_by?: string | null;
  created_at?: string;
  updated_at?: string;
};

export type EventDetail = EventOut & {
  categories_count: number;
  participants_count: number;
  documents_count: number;
  officials_count?: number;
  training_slots_count?: number;
};

export type OfficialOut = {
  id: number;
  event_id: number;
  sort_order: number;
  full_name: string;
  position: string;
  region: string | null;
  judge_category: string | null;
  notes: string | null;
  user_id: number | null;
};

export type TrainingSlotOut = {
  id: number;
  event_id: number;
  discipline: string;
  venue: string | null;
  slot_date: string;
  slot_time: string | null;
  status: string;
  athlete_name: string | null;
  notes: string | null;
  sort_order: number;
};

export type CategoryOut = {
  id: number;
  event_id: number;
  code: string;
  title: string;
  discipline: string | null;
  notes: string | null;
};

export type ParticipantOut = {
  id: number;
  event_id: number;
  category_id: number | null;
  full_name: string;
  gender: string | null;
  birth_year: number | null;
  club: string | null;
  region: string | null;
  city: string | null;
  federation: string | null;
  has_medical_cert?: boolean;
  status: string;
};

export type DocumentOut = {
  id: number;
  event_id: number;
  title: string;
  kind: string;
  language: string | null;
  file_name: string;
  description: string | null;
};

type ErrorPayload = {
  error?: { code?: string; message?: string };
  detail?: { code?: string; message?: string } | string;
};

async function parseError(res: Response): Promise<ApiError> {
  let message = `Ошибка API (${res.status})`;
  let code: string | undefined;
  try {
    const body = (await res.json()) as ErrorPayload;
    if (body.error?.message) {
      message = body.error.message;
      code = body.error.code;
    } else if (typeof body.detail === "string") {
      message = body.detail;
    } else if (body.detail && typeof body.detail === "object" && body.detail.message) {
      message = body.detail.message;
      code = body.detail.code;
    }
  } catch {
    /* keep default */
  }
  return new ApiError(message, res.status, code);
}

export async function apiFetch<T>(
  path: string,
  init: RequestInit = {},
  token?: string | null,
): Promise<T> {
  const headers = new Headers(init.headers);
  if (!headers.has("Accept")) {
    headers.set("Accept", "application/json");
  }
  if (init.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const res = await fetch(`${getApiBaseUrl()}${path}`, {
    ...init,
    headers,
    cache: "no-store",
  });

  if (!res.ok) {
    throw await parseError(res);
  }

  if (res.status === 204) {
    return undefined as T;
  }

  return (await res.json()) as T;
}

export function getHealth(): Promise<HealthResponse> {
  return apiFetch<HealthResponse>("/health");
}

export async function devLogin(payload: {
  email: string;
  role: Role;
  display_name?: string;
}): Promise<TokenResponse> {
  const raw = await apiFetch<ApiTokenPayload>("/api/v1/auth/dev-login", {
    method: "POST",
    body: JSON.stringify(payload),
  });
  return toTokenResponse(raw);
}

export type RegisterPayload = {
  phone: string;
  email: string;
  display_name: string;
  requested_role: Role;
  accept_terms: boolean;
  accept_privacy: boolean;
  accept_publish_name?: boolean;
  accept_analytics?: boolean;
};

export type LegalDocument = {
  purpose: string;
  title: string;
  version: string;
  required: boolean;
  revocable: boolean;
  summary: string;
  body?: string | null;
};

export type ConsentItem = {
  purpose: string;
  title: string;
  version: string;
  required: boolean;
  revocable: boolean;
  granted: boolean;
  granted_at: string | null;
  current_document_version: string;
};

export function fetchLegalDocuments() {
  return apiFetch<{ items: LegalDocument[]; current_version: string }>("/api/v1/legal/documents");
}

export function fetchLegalDocument(purpose: string) {
  return apiFetch<LegalDocument>(`/api/v1/legal/documents/${purpose}`);
}

export function fetchMyConsents(token: string) {
  return apiFetch<{ items: ConsentItem[] }>("/api/v1/me/consents", { method: "GET" }, token);
}

export function grantMyConsent(token: string, purpose: string, version?: string) {
  return apiFetch<ConsentItem>(
    "/api/v1/me/consents",
    { method: "POST", body: JSON.stringify({ purpose, version }) },
    token,
  );
}

export function revokeMyConsent(token: string, purpose: string) {
  return apiFetch<ConsentItem>(
    `/api/v1/me/consents/${purpose}/revoke`,
    { method: "POST" },
    token,
  );
}

export type RegisterResponse = {
  user_id: number;
  email: string;
  phone: string;
  role: Role;
  requested_role: Role;
  status: string;
  message: string;
  access_token: string | null;
  token_type: string | null;
};

export function registerAccount(payload: RegisterPayload): Promise<RegisterResponse> {
  return apiFetch<RegisterResponse>("/api/v1/auth/register", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export type OtpRequestResponse = {
  ok: boolean;
  phone_masked: string;
  message: string;
  expires_in_seconds: number;
  dev_otp?: string | null;
};

export function requestPhoneOtp(phone: string): Promise<OtpRequestResponse> {
  return apiFetch<OtpRequestResponse>("/api/v1/auth/phone/request-otp", {
    method: "POST",
    body: JSON.stringify({ phone }),
  });
}

export async function verifyPhoneOtp(phone: string, code: string): Promise<TokenResponse> {
  const raw = await apiFetch<ApiTokenPayload>("/api/v1/auth/phone/verify-otp", {
    method: "POST",
    body: JSON.stringify({ phone, code }),
  });
  return toTokenResponse(raw);
}

export type PendingApproval = {
  approval_id: number;
  user_id: number;
  email: string;
  display_name: string | null;
  phone_masked: string | null;
  requested_role: Role;
  status: string;
  created_at: string;
  expires_at: string;
};

export async function listPendingApprovals(token: string): Promise<PendingApproval[]> {
  const payload = await apiFetch<{ items: PendingApproval[]; total: number }>(
    "/api/v1/auth/approvals/pending",
    { method: "GET" },
    token,
  );
  return payload.items;
}

export function decidePendingApproval(
  token: string,
  approvalId: number,
  decision: "approve" | "reject",
) {
  return apiFetch<{
    ok: boolean;
    user_id: number;
    email: string;
    role: Role;
    status: string;
    message: string;
  }>(`/api/v1/auth/approvals/${approvalId}/${decision}`, { method: "POST" }, token);
}

export type NotificationOut = {
  id: number;
  kind: string;
  title: string;
  body: string;
  entity_type: string | null;
  entity_id: string | null;
  is_read: boolean;
  created_at: string;
};

export async function listMyNotifications(token: string): Promise<{
  items: NotificationOut[];
  total: number;
  unread_count: number;
}> {
  return apiFetch("/api/v1/me/notifications", { method: "GET" }, token);
}

export async function getUnreadCount(token: string): Promise<number> {
  const payload = await apiFetch<{ unread_count: number }>(
    "/api/v1/me/notifications/unread-count",
    { method: "GET" },
    token,
  );
  return payload.unread_count;
}

export function markNotificationRead(token: string, notificationId: number) {
  return apiFetch<NotificationOut>(
    `/api/v1/me/notifications/${notificationId}/read`,
    { method: "POST" },
    token,
  );
}

export function markAllNotificationsRead(token: string) {
  return apiFetch<{ unread_count: number }>(
    "/api/v1/me/notifications/read-all",
    { method: "POST" },
    token,
  );
}

export type ScheduleHint = {
  summary: string;
  notes: string[];
};

export function getScheduleHint(token: string, eventId: number | string) {
  return apiFetch<ScheduleHint>(
    `/api/v1/events/${eventId}/schedule-hint`,
    { method: "GET" },
    token,
  );
}

export type EventCreatePayload = {
  slug: string;
  title: string;
  description?: string | null;
  city?: string | null;
  location?: string | null;
  venue?: string | null;
  disciplines?: string | null;
  starts_at?: string | null;
  ends_at?: string | null;
  status?: EventStatus | string;
  rules_profile?: EventRulesProfileCreatePayload;
};

export type EventRulesProfileCreatePayload = {
  governing_body?: string;
  sanction_body?: string;
  discipline_codes: string[];
  scoring_mode?: string;
};

export type EventRulesProfileOut = {
  id: number;
  event_id: number;
  governing_body: string;
  sanction_body: string;
  discipline_codes: string[];
  rules_packs: Record<string, string>;
  scoring_mode: string;
  created_at: string;
  updated_at: string;
};

export type RulesCatalog = {
  governing_bodies: Record<string, Record<string, string>>;
  disciplines: Record<string, { title_ru: string; default_rules_pack?: string }>;
  rules_packs: Record<string, Record<string, unknown>>;
  scoring_modes: Record<string, { title_ru: string }>;
  p0_discipline_codes: string[];
  defaults: { governing_body: string; sanction_body: string; scoring_mode: string };
};

export type ProtocolCaptureOut = {
  id: number;
  event_id: number;
  heat_id: number | null;
  title: string;
  kind: string;
  status: string;
  file_name: string;
  mime_type: string;
  notes: string | null;
  extracted: Record<string, unknown> | null;
  created_by_user_id: number | null;
  verified_by_user_id: number | null;
  verified_at: string | null;
  created_at: string;
};

export function createEvent(token: string, payload: EventCreatePayload) {
  return apiFetch<EventOut>("/api/v1/events", {
    method: "POST",
    body: JSON.stringify(payload),
  }, token);
}

export function getRulesCatalog() {
  return apiFetch<RulesCatalog>("/api/v1/rules/catalog", { method: "GET" });
}

export function getEventRulesProfile(token: string, eventId: number | string) {
  return apiFetch<EventRulesProfileOut | null>(
    `/api/v1/events/${eventId}/rules-profile`,
    { method: "GET" },
    token,
  );
}

export function upsertEventRulesProfile(
  token: string,
  eventId: number | string,
  payload: EventRulesProfileCreatePayload,
) {
  return apiFetch<EventRulesProfileOut>(
    `/api/v1/events/${eventId}/rules-profile`,
    { method: "PUT", body: JSON.stringify(payload) },
    token,
  );
}

export async function listProtocolCaptures(token: string, eventId: number | string) {
  const payload = await apiFetch<{ items: ProtocolCaptureOut[]; total: number }>(
    `/api/v1/events/${eventId}/protocol-captures`,
    { method: "GET" },
    token,
  );
  return payload.items;
}

export async function uploadProtocolCapture(
  token: string,
  eventId: number | string,
  file: File,
  meta: { title: string; kind?: string; heat_id?: number; notes?: string },
): Promise<ProtocolCaptureOut> {
  const form = new FormData();
  form.append("file", file);
  form.append("title", meta.title);
  form.append("kind", meta.kind ?? "judge_sheet");
  if (meta.heat_id != null) form.append("heat_id", String(meta.heat_id));
  if (meta.notes) form.append("notes", meta.notes);

  const headers = new Headers();
  headers.set("Accept", "application/json");
  headers.set("Authorization", `Bearer ${token}`);

  const response = await fetch(`${getApiBaseUrl()}/api/v1/events/${eventId}/protocol-captures`, {
    method: "POST",
    headers,
    body: form,
  });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    const err = body?.error ?? body?.detail;
    throw new ApiError(
      typeof err === "string" ? err : err?.message ?? response.statusText,
      response.status,
      err?.code,
    );
  }
  return body as ProtocolCaptureOut;
}

export function updateProtocolCapture(
  token: string,
  eventId: number | string,
  captureId: number,
  payload: { status?: string; notes?: string; title?: string; extracted?: Record<string, unknown> },
) {
  return apiFetch<ProtocolCaptureOut>(
    `/api/v1/events/${eventId}/protocol-captures/${captureId}`,
    { method: "PATCH", body: JSON.stringify(payload) },
    token,
  );
}

export function protocolCaptureFileUrl(eventId: number | string, captureId: number): string {
  return `${getApiBaseUrl()}/api/v1/events/${eventId}/protocol-captures/${captureId}/file`;
}

export type EventListResponse = {
  items: EventOut[];
  total: number;
};

export async function listEvents(token: string): Promise<EventOut[]> {
  const payload = await apiFetch<EventListResponse | EventOut[]>(
    "/api/v1/events",
    { method: "GET" },
    token,
  );
  // API returns { items, total }; tolerate a bare array for older mocks.
  if (Array.isArray(payload)) {
    return payload;
  }
  if (payload && Array.isArray(payload.items)) {
    return payload.items;
  }
  return [];
}

export function getEventDetail(token: string, eventId: number | string) {
  return apiFetch<EventDetail>(`/api/v1/events/${eventId}/detail`, { method: "GET" }, token);
}

export async function listCategories(token: string, eventId: number | string) {
  const payload = await apiFetch<{ items: CategoryOut[]; total: number }>(
    `/api/v1/events/${eventId}/categories`,
    { method: "GET" },
    token,
  );
  return payload.items;
}

export async function listParticipants(token: string, eventId: number | string) {
  const payload = await apiFetch<{ items: ParticipantOut[]; total: number }>(
    `/api/v1/events/${eventId}/participants`,
    { method: "GET" },
    token,
  );
  return payload.items;
}

export async function listDocuments(token: string, eventId: number | string) {
  const payload = await apiFetch<{ items: DocumentOut[]; total: number }>(
    `/api/v1/events/${eventId}/documents`,
    { method: "GET" },
    token,
  );
  return payload.items;
}

export async function uploadDocument(
  token: string,
  eventId: number | string,
  file: File,
  meta: { title: string; kind?: string; language?: string; description?: string },
): Promise<DocumentOut> {
  const form = new FormData();
  form.append("file", file);
  form.append("title", meta.title);
  form.append("kind", meta.kind ?? "other");
  if (meta.language) form.append("language", meta.language);
  if (meta.description) form.append("description", meta.description);

  const headers = new Headers();
  headers.set("Accept", "application/json");
  headers.set("Authorization", `Bearer ${token}`);

  const res = await fetch(`${getApiBaseUrl()}/api/v1/events/${eventId}/documents`, {
    method: "POST",
    headers,
    body: form,
    cache: "no-store",
  });
  if (!res.ok) throw await parseError(res);
  return (await res.json()) as DocumentOut;
}

export function deleteDocument(token: string, eventId: number | string, documentId: number) {
  return apiFetch<void>(
    `/api/v1/events/${eventId}/documents/${documentId}`,
    { method: "DELETE" },
    token,
  );
}

export type ChecklistItemOut = {
  id: number;
  event_id: number;
  code: string;
  title: string;
  is_done: boolean;
  sort_order: number;
  done_at: string | null;
  done_by_user_id: number | null;
  created_at: string;
};

export async function listChecklist(token: string, eventId: number | string) {
  return apiFetch<{ items: ChecklistItemOut[]; total: number; done_count: number }>(
    `/api/v1/events/${eventId}/checklist`,
    { method: "GET" },
    token,
  );
}

export function updateChecklistItem(
  token: string,
  eventId: number | string,
  itemId: number,
  is_done: boolean,
) {
  return apiFetch<ChecklistItemOut>(
    `/api/v1/events/${eventId}/checklist/${itemId}`,
    { method: "PATCH", body: JSON.stringify({ is_done }) },
    token,
  );
}

export type HeatOut = {
  id: number;
  event_id: number;
  category_id: number | null;
  code: string;
  title: string;
  heat_number: number;
  scheduled_at: string | null;
  status: string;
  notes: string | null;
};

export type StartListEntryOut = {
  id: number;
  heat_id: number;
  event_id: number;
  participant_id: number;
  start_order: number;
  bib_number: string | null;
  status: string;
  checked_in_at: string | null;
  ready_at: string | null;
  on_water_at: string | null;
  completed_at: string | null;
};

export async function listHeats(token: string, eventId: number | string) {
  const payload = await apiFetch<{ items: HeatOut[]; total: number }>(
    `/api/v1/events/${eventId}/heats`,
    { method: "GET" },
    token,
  );
  return payload.items;
}

export function createHeat(
  token: string,
  eventId: number | string,
  payload: {
    code: string;
    title: string;
    heat_number?: number;
    category_id?: number | null;
  },
) {
  return apiFetch<HeatOut>(
    `/api/v1/events/${eventId}/heats`,
    { method: "POST", body: JSON.stringify(payload) },
    token,
  );
}

export function updateHeatStatus(
  token: string,
  eventId: number | string,
  heatId: number,
  status: string,
) {
  return apiFetch<HeatOut>(
    `/api/v1/events/${eventId}/heats/${heatId}/status`,
    { method: "PATCH", body: JSON.stringify({ status }) },
    token,
  );
}

export async function listStartList(token: string, eventId: number | string, heatId: number) {
  const payload = await apiFetch<{ items: StartListEntryOut[]; total: number }>(
    `/api/v1/events/${eventId}/heats/${heatId}/start-list`,
    { method: "GET" },
    token,
  );
  return payload.items;
}

export function addStartListEntry(
  token: string,
  eventId: number | string,
  heatId: number,
  payload: { participant_id: number; start_order: number; bib_number?: string },
) {
  return apiFetch<StartListEntryOut>(
    `/api/v1/events/${eventId}/heats/${heatId}/start-list`,
    { method: "POST", body: JSON.stringify(payload) },
    token,
  );
}

export async function fillStartList(
  token: string,
  eventId: number | string,
  heatId: number,
  categoryId?: number | null,
) {
  const payload = await apiFetch<{ items: StartListEntryOut[]; total: number }>(
    `/api/v1/events/${eventId}/heats/${heatId}/start-list/fill`,
    { method: "POST", body: JSON.stringify({ category_id: categoryId ?? null }) },
    token,
  );
  return payload;
}

export function updateStartListStatus(
  token: string,
  eventId: number | string,
  heatId: number,
  entryId: number,
  status: string,
) {
  return apiFetch<StartListEntryOut>(
    `/api/v1/events/${eventId}/heats/${heatId}/start-list/${entryId}/status`,
    { method: "PATCH", body: JSON.stringify({ status }) },
    token,
  );
}

export type ResultOut = {
  id: number;
  event_id: number;
  participant_id: number;
  heat_id: number | null;
  run_id: number | null;
  category_id: number | null;
  attempt_no: number;
  status: string;
  score: number | null;
  place: number | null;
  notes: string | null;
  published_at: string | null;
};

export async function listResults(token: string, eventId: number | string, status?: string) {
  const qs = status ? `?status=${encodeURIComponent(status)}` : "";
  const payload = await apiFetch<{ items: ResultOut[]; total: number }>(
    `/api/v1/events/${eventId}/results${qs}`,
    { method: "GET" },
    token,
  );
  return payload.items;
}

export function upsertResultDraft(
  token: string,
  eventId: number | string,
  payload: {
    participant_id: number;
    score?: number | null;
    place?: number | null;
    heat_id?: number | null;
    notes?: string | null;
  },
) {
  return apiFetch<ResultOut>(
    `/api/v1/events/${eventId}/results`,
    { method: "POST", body: JSON.stringify(payload) },
    token,
  );
}

export function updateResultStatus(
  token: string,
  eventId: number | string,
  resultId: number,
  status: "draft" | "verified" | "published" | "void",
) {
  return apiFetch<ResultOut>(
    `/api/v1/events/${eventId}/results/${resultId}/status`,
    { method: "PATCH", body: JSON.stringify({ status }) },
    token,
  );
}

export type ScoringEngineMeta = {
  engine: string;
  criteria: string[];
  criteria_labels_ru: Record<string, string>;
  aggregation: string;
  drop_extremes_if_judges_ge: number | null;
  best_of_runs: boolean;
  placement_overrides_score: boolean;
};

export type JudgeScoreOut = {
  id: number;
  event_id: number;
  participant_id: number;
  heat_id: number | null;
  judge_user_id: number;
  attempt_no: number;
  engine: string;
  criteria: Record<string, number>;
  total: number;
  notes: string | null;
  created_at: string;
  updated_at: string;
};

export function getScoringEngine(token: string, eventId: number | string) {
  return apiFetch<ScoringEngineMeta>(
    `/api/v1/events/${eventId}/scoring/engine`,
    { method: "GET" },
    token,
  );
}

export async function listJudgeScores(
  token: string,
  eventId: number | string,
  participantId?: number,
) {
  const qs = participantId != null ? `?participant_id=${participantId}` : "";
  const payload = await apiFetch<{ items: JudgeScoreOut[]; total: number }>(
    `/api/v1/events/${eventId}/judge-scores${qs}`,
    { method: "GET" },
    token,
  );
  return payload.items;
}

export function submitJudgeScore(
  token: string,
  eventId: number | string,
  payload: {
    participant_id: number;
    heat_id?: number | null;
    attempt_no?: number;
    criteria: Record<string, number>;
    notes?: string;
  },
) {
  return apiFetch<JudgeScoreOut>(
    `/api/v1/events/${eventId}/judge-scores`,
    { method: "POST", body: JSON.stringify(payload) },
    token,
  );
}

export function aggregateJudgeScores(
  token: string,
  eventId: number | string,
  payload: {
    participant_id: number;
    heat_id?: number | null;
    attempt_no?: number;
    write_result_draft?: boolean;
    place?: number | null;
  },
) {
  return apiFetch<{
    engine: string;
    panel_score: number;
    judge_count: number;
    judge_totals: number[];
    result_id: number | null;
  }>(
    `/api/v1/events/${eventId}/judge-scores/aggregate`,
    { method: "POST", body: JSON.stringify(payload) },
    token,
  );
}

export async function listOfficials(token: string, eventId: number | string) {
  const payload = await apiFetch<{ items: OfficialOut[]; total: number }>(
    `/api/v1/events/${eventId}/officials`,
    { method: "GET" },
    token,
  );
  return payload.items;
}

export async function listTrainingSlots(
  token: string,
  eventId: number | string,
  opts?: { onlyBooked?: boolean; discipline?: string },
) {
  const params = new URLSearchParams();
  if (opts?.onlyBooked) params.set("only_booked", "true");
  if (opts?.discipline) params.set("discipline", opts.discipline);
  const qs = params.toString();
  const payload = await apiFetch<{ items: TrainingSlotOut[]; total: number }>(
    `/api/v1/events/${eventId}/training-slots${qs ? `?${qs}` : ""}`,
    { method: "GET" },
    token,
  );
  return payload.items;
}

export type ApplicationOut = {
  id: number;
  event_id: number;
  category_id: number | null;
  user_id: number | null;
  full_name: string;
  club: string | null;
  region: string | null;
  city: string | null;
  gender: string | null;
  birth_year: number | null;
  status: string;
  created_at: string;
};

export type ApplicationCreatePayload = {
  category_id?: number | null;
  club?: string | null;
  region?: string | null;
  city?: string | null;
  gender?: string | null;
  birth_year?: number | null;
};

export function submitApplication(
  token: string,
  eventId: number | string,
  payload: ApplicationCreatePayload,
) {
  return apiFetch<ApplicationOut>(
    `/api/v1/events/${eventId}/applications`,
    { method: "POST", body: JSON.stringify(payload) },
    token,
  );
}

export function getMyApplication(token: string, eventId: number | string) {
  return apiFetch<ApplicationOut | null>(
    `/api/v1/events/${eventId}/applications/me`,
    { method: "GET" },
    token,
  );
}

export async function listEventApplications(
  token: string,
  eventId: number | string,
  status = "pending",
) {
  const payload = await apiFetch<{ items: ApplicationOut[]; total: number }>(
    `/api/v1/events/${eventId}/applications?status=${encodeURIComponent(status)}`,
    { method: "GET" },
    token,
  );
  return payload.items;
}

export function decideEventApplication(
  token: string,
  eventId: number | string,
  participantId: number,
  status: "accepted" | "rejected",
) {
  return apiFetch<ApplicationOut>(
    `/api/v1/events/${eventId}/applications/${participantId}`,
    { method: "PATCH", body: JSON.stringify({ status }) },
    token,
  );
}

export type MeResponse = {
  id: number;
  email: string;
  phone: string | null;
  role: Role;
  requested_role: Role | null;
  status: string;
  display_name: string | null;
};

export function fetchMe(token: string): Promise<MeResponse> {
  return apiFetch<MeResponse>("/api/v1/me", { method: "GET" }, token);
}

export function updateMyProfile(
  token: string,
  payload: { display_name?: string; phone?: string },
): Promise<MeResponse> {
  return apiFetch<MeResponse>(
    "/api/v1/me",
    { method: "PATCH", body: JSON.stringify(payload) },
    token,
  );
}

export function documentDownloadUrl(eventId: number | string, documentId: number): string {
  return `${getApiBaseUrl()}/api/v1/events/${eventId}/documents/${documentId}/file`;
}

export function saveSession(token: string, user: UserOut): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function clearSession(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

export function getStoredToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function getStoredUser(): UserOut | null {
  if (typeof window === "undefined") return null;
  const raw = localStorage.getItem(USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as UserOut;
  } catch {
    return null;
  }
}
