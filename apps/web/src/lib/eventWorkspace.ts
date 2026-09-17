/** Role-based workspace helpers — presentation only, API codes unchanged. */

import type {
  ApplicationOut,
  HeatOut,
  ParticipantOut,
  ResultOut,
  StartListEntryOut,
} from "@/lib/api";
import { ENTRY_STATUS_LABELS, labelOf } from "@/lib/labels";

export type AthletePhase =
  | "not_applied"
  | "applied"
  | "in_roster"
  | "checked_in"
  | "ready"
  | "next"
  | "on_water"
  | "finished";

export const ATHLETE_PHASE_LABELS: Record<AthletePhase, string> = {
  not_applied: "Нужна заявка",
  applied: "Заявка на рассмотрении",
  in_roster: "В составе",
  checked_in: "Регистрация пройдена",
  ready: "Готов к старту",
  next: "Следующий на старте",
  on_water: "На воде",
  finished: "Заезд завершён",
};

export const SCORING_ENGINE_LABELS: Record<string, string> = {
  MANUAL_PLACE: "Место вручную",
  FVLS_WAKE: "ФВЛС",
  IWWF_WAKE: "IWWF",
  IWWF: "IWWF",
  FVLS: "ФВЛС",
};

export type AttentionItem = {
  id: string;
  title: string;
  detail: string;
  tab: "apps" | "participants" | "heats" | "scoring" | "results" | "checklist";
};

export function pickLiveHeat(heats: HeatOut[]): HeatOut | undefined {
  return (
    heats.find((h) => h.status === "on_water") ??
    heats.find((h) => h.status === "ready") ??
    heats.find((h) => h.status === "planned")
  );
}

export function pickNextHeat(heats: HeatOut[], live?: HeatOut): HeatOut | undefined {
  if (!heats.length) return undefined;
  const liveIdx = live ? heats.findIndex((h) => h.id === live.id) : -1;
  if (liveIdx >= 0) {
    return heats.slice(liveIdx + 1).find((h) => h.status !== "completed" && h.status !== "cancelled");
  }
  return heats.find((h) => h.status === "planned" || h.status === "ready");
}

export function pickCurrentEntry(entries: StartListEntryOut[]): StartListEntryOut | undefined {
  return (
    entries.find((e) => e.status === "on_water") ??
    entries.find((e) => e.status === "ready") ??
    entries.find((e) => e.status === "checked_in")
  );
}

export function nextEntryAfter(
  entries: StartListEntryOut[],
  participantId: number,
): StartListEntryOut | undefined {
  const ordered = [...entries].sort((a, b) => a.start_order - b.start_order);
  const idx = ordered.findIndex((e) => e.participant_id === participantId);
  if (idx < 0) return pickCurrentEntry(ordered);
  return ordered.slice(idx + 1).find((e) => !["completed", "dns", "dnf"].includes(e.status));
}

export function findMyParticipant(
  participants: ParticipantOut[],
  userId: string | undefined,
  myApp: ApplicationOut | null,
): ParticipantOut | undefined {
  if (userId) {
    const byUser = participants.find((p) => p.user_id != null && String(p.user_id) === String(userId));
    if (byUser) return byUser;
  }
  if (myApp?.full_name) {
    return participants.find((p) => p.full_name.trim() === myApp.full_name.trim());
  }
  return undefined;
}

export function findMyEntry(
  entries: StartListEntryOut[],
  participant: ParticipantOut | undefined,
): StartListEntryOut | undefined {
  if (!participant) return undefined;
  return entries.find((e) => e.participant_id === participant.id);
}

function athletePhase(
  myApp: ApplicationOut | null,
  participant: ParticipantOut | undefined,
  entry: StartListEntryOut | undefined,
  current: StartListEntryOut | undefined,
): AthletePhase {
  if (entry?.status === "on_water") return "on_water";
  if (entry?.status === "completed" || entry?.status === "dns" || entry?.status === "dnf") return "finished";
  if (entry?.status === "ready") {
    if (!current || current.id === entry.id || current.status !== "on_water") return "next";
    return "ready";
  }
  if (entry?.status === "checked_in") return "checked_in";
  if (participant || myApp?.status === "accepted" || myApp?.status === "registered") return "in_roster";
  if (myApp) return "applied";
  return "not_applied";
}

export type AthleteSnapshot = {
  fullName: string;
  athleteId: string | null;
  categoryTitle: string;
  heatTitle: string | null;
  heatCode: string | null;
  bib: string | null;
  startOrder: number | null;
  queueAhead: number | null;
  phase: AthletePhase;
  phaseLabel: string;
  applicationStatus: string | null;
  resultPlace: number | null;
  resultScore: number | null;
  resultStatus: string | null;
};

export function buildAthleteSnapshot(input: {
  displayName: string;
  athleteId?: string | null;
  myApp: ApplicationOut | null;
  participant?: ParticipantOut;
  entry?: StartListEntryOut;
  heat?: HeatOut;
  startList: StartListEntryOut[];
  categoryTitle: string;
  results: ResultOut[];
}): AthleteSnapshot {
  const current = pickCurrentEntry(input.startList);
  const phase = athletePhase(input.myApp, input.participant, input.entry, current);
  const queueAhead =
    input.entry == null
      ? null
      : input.startList.filter(
          (e) =>
            e.start_order < input.entry!.start_order && !["completed", "dns", "dnf"].includes(e.status),
        ).length;
  const myResult = input.participant
    ? input.results.find((r) => r.participant_id === input.participant!.id)
    : undefined;
  return {
    fullName: input.participant?.full_name || input.myApp?.full_name || input.displayName,
    athleteId: input.participant?.athlete_id || input.athleteId || null,
    categoryTitle: input.categoryTitle,
    heatTitle: input.heat?.title ?? null,
    heatCode: input.heat?.code ?? null,
    bib: input.entry?.bib_number ?? null,
    startOrder: input.entry?.start_order ?? null,
    queueAhead,
    phase,
    phaseLabel: ATHLETE_PHASE_LABELS[phase],
    applicationStatus: input.myApp?.status ?? null,
    resultPlace: myResult?.place ?? null,
    resultScore: myResult?.score ?? null,
    resultStatus: myResult?.status ?? null,
  };
}

export function scoringEngineLabel(engine: string | null | undefined): string {
  if (!engine) return "—";
  return SCORING_ENGINE_LABELS[engine] ?? engine.replace(/_/g, " ");
}

export function buildAttentionItems(input: {
  pendingApps: number;
  rosterLocked: boolean;
  participantsCount: number;
  verifiedResults: number;
  liveHeat?: HeatOut;
  currentEntry?: StartListEntryOut;
  currentHasScore: boolean;
  checklistOpen: number;
}): AttentionItem[] {
  const items: AttentionItem[] = [];
  if (input.pendingApps > 0) {
    items.push({
      id: "apps",
      title: "Заявки ждут решения",
      detail: `${input.pendingApps} заявки на рассмотрении.`,
      tab: "apps",
    });
  }
  if (!input.rosterLocked && input.participantsCount > 0) {
    items.push({
      id: "roster",
      title: "Состав ещё не зафиксирован",
      detail: "После проверки участников зафиксируйте состав.",
      tab: "participants",
    });
  }
  if (input.liveHeat && !input.currentEntry) {
    items.push({
      id: "heat-empty",
      title: "Нет спортсмена на воде",
      detail: `Заезд ${input.liveHeat.code} открыт, но текущий старт не выбран.`,
      tab: "heats",
    });
  }
  if (input.currentEntry && !input.currentHasScore) {
    items.push({
      id: "score",
      title: "Нет оценки текущего старта",
      detail: "Судья ещё не сохранил лист на спортсмена на воде.",
      tab: "scoring",
    });
  }
  if (input.verifiedResults > 0) {
    items.push({
      id: "publish",
      title: "Результаты ждут главного судью",
      detail: `${input.verifiedResults} проверенных результата нельзя опубликовать организатору.`,
      tab: "results",
    });
  }
  if (input.checklistOpen > 0) {
    items.push({
      id: "checklist",
      title: "Чек-лист подготовки",
      detail: `Открыто пунктов: ${input.checklistOpen}.`,
      tab: "checklist",
    });
  }
  return items;
}

export function entryStatusLabel(status: string): string {
  return labelOf(ENTRY_STATUS_LABELS, status);
}
