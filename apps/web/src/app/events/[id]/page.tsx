"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";
import { AppDownloadCard } from "@/components/AppDownloadCard";
import { AppHeader } from "@/components/AppHeader";
import { AthleteEventHome } from "@/components/AthleteEventHome";
import { FieldMomentsPanel } from "@/components/FieldMomentsPanel";
import { OrganizerControlRoom } from "@/components/OrganizerControlRoom";
import { StatusBadge } from "@/components/StatusBadge";
import {
  ApiError,
  ApplicationOut,
  CategoryOut,
  ChecklistItemOut,
  DocumentOut,
  EventDetail,
  EventRulesProfileOut,
  FieldMomentOut,
  HeatOut,
  OfficialOut,
  OfficialProtocolReadiness,
  ParticipantOut,
  ProtocolCaptureOut,
  ResultOut,
  ScoringEngineMeta,
  ScheduleHint,
  StartListEntryOut,
  TrainingSlotOut,
  addStartListEntry,
  aggregateJudgeScores,
  createHeat,
  decideEventApplication,
  deleteDocument,
  documentDownloadUrl,
  fillStartList,
  getEventDetail,
  getEventRulesProfile,
  getMyApplication,
  getOfficialProtocol,
  getScheduleHint,
  getScoringEngine,
  getStoredToken,
  getStoredUser,
  isSessionExpiredError,
  listCategories,
  listChecklist,
  listDocuments,
  listEventApplications,
  listFieldMoments,
  listHeats,
  listJudgeScores,
  listOfficials,
  listParticipants,
  listProtocolCaptures,
  listResults,
  listStartList,
  listTrainingSlots,
  lockEventRoster,
  officialProtocolDownloadUrl,
  officialProtocolHtmlUrl,
  protocolCaptureFileUrl,
  submitApplication,
  submitJudgeScore,
  unlockEventRoster,
  updateChecklistItem,
  updateEventStatus,
  updateHeatStatus,
  updateProtocolCapture,
  updateResultStatus,
  updateStartListStatus,
  uploadDocument,
  uploadProtocolCapture,
  upsertResultDraft,
} from "@/lib/api";
import {
  buildAthleteSnapshot,
  buildAttentionItems,
  findMyEntry,
  findMyParticipant,
  nextEntryAfter,
  pickCurrentEntry,
  pickLiveHeat,
  pickNextHeat,
  scoringEngineLabel,
} from "@/lib/eventWorkspace";
import { formatEventDate, formatEventPeriod, loginHref, rememberLastEvent } from "@/lib/format";
import {
  DOCUMENT_KIND_LABELS,
  ENTRY_STATUS_LABELS,
  HEAT_STATUS_LABELS,
  PROTOCOL_KIND_LABELS,
  labelOf,
  nextEntryStatus,
  nextEntryStatusLabel,
  nextHeatStatus,
  nextHeatStatusLabel,
} from "@/lib/labels";
import {
  canCaptureFieldMoments,
  canModerateFieldMoments,
  canPublishOfficialResults,
  isBroadcastRole,
  isChiefJudgeRole,
  isJudgeRole,
  isStaffRole,
} from "@/lib/roles";
import styles from "../events.module.css";

type TabId =
  | "overview"
  | "checklist"
  | "participants"
  | "slots"
  | "docs"
  | "protocol"
  | "moments"
  | "scoring"
  | "heats"
  | "results"
  | "apps";

const ALL_TABS: TabId[] = [
  "overview",
  "checklist",
  "participants",
  "slots",
  "docs",
  "protocol",
  "moments",
  "scoring",
  "heats",
  "results",
  "apps",
];

function visibleTabs(role: string | undefined, isGuest: boolean): TabId[] {
  if (isGuest) return ["overview", "results"];
  if (isStaffRole(role ?? "")) return ALL_TABS;
  if (isChiefJudgeRole(role)) {
    return ["overview", "checklist", "scoring", "heats", "protocol", "moments", "results", "participants"];
  }
  if (role === "judge") {
    return ["overview", "scoring", "heats", "protocol", "results", "participants"];
  }
  if (isBroadcastRole(role)) {
    return ["overview", "heats", "results", "participants", "docs", "moments"];
  }
  if (role === "support") {
    return ["overview", "participants", "docs", "results", "apps", "moments"];
  }
  return ["overview", "apps", "participants", "slots", "docs", "results"];
}

export default function EventDetailPage() {
  const params = useParams<{ id: string }>();
  const eventId = params.id;
  const [sessionExpired, setSessionExpired] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [detail, setDetail] = useState<EventDetail | null>(null);
  const [categories, setCategories] = useState<CategoryOut[]>([]);
  const [participants, setParticipants] = useState<ParticipantOut[]>([]);
  const [documents, setDocuments] = useState<DocumentOut[]>([]);
  const [checklist, setChecklist] = useState<ChecklistItemOut[]>([]);
  const [checklistDone, setChecklistDone] = useState(0);
  const [heats, setHeats] = useState<HeatOut[]>([]);
  const [selectedHeatId, setSelectedHeatId] = useState<number | null>(null);
  const [startList, setStartList] = useState<StartListEntryOut[]>([]);
  const [heatCode, setHeatCode] = useState("");
  const [heatTitle, setHeatTitle] = useState("");
  const [addParticipantId, setAddParticipantId] = useState("");
  const [uploadTitle, setUploadTitle] = useState("");
  const [uploadKind, setUploadKind] = useState("other");
  const [uploadBusy, setUploadBusy] = useState(false);
  const [rulesProfile, setRulesProfile] = useState<EventRulesProfileOut | null>(null);
  const [protocols, setProtocols] = useState<ProtocolCaptureOut[]>([]);
  const [fieldMoments, setFieldMoments] = useState<FieldMomentOut[]>([]);
  const [protocolTitle, setProtocolTitle] = useState("");
  const [protocolKind, setProtocolKind] = useState("judge_sheet");
  const [protocolBusy, setProtocolBusy] = useState(false);
  const [protocolReadiness, setProtocolReadiness] = useState<OfficialProtocolReadiness | null>(null);
  const [exportBusy, setExportBusy] = useState(false);
  const [scoringEngine, setScoringEngine] = useState<ScoringEngineMeta | null>(null);
  const [judgeScores, setJudgeScores] = useState<
    Awaited<ReturnType<typeof listJudgeScores>>
  >([]);
  const [scoreParticipantId, setScoreParticipantId] = useState("");
  const [criteriaValues, setCriteriaValues] = useState<Record<string, string>>({});
  const [scoreBusy, setScoreBusy] = useState(false);
  const [results, setResults] = useState<ResultOut[]>([]);
  const [resultParticipantId, setResultParticipantId] = useState("");
  const [resultScore, setResultScore] = useState("");
  const [resultPlace, setResultPlace] = useState("");
  const [officials, setOfficials] = useState<OfficialOut[]>([]);
  const [training, setTraining] = useState<TrainingSlotOut[]>([]);
  const [hint, setHint] = useState<ScheduleHint | null>(null);
  const [onlyBooked, setOnlyBooked] = useState(false);
  const [filter, setFilter] = useState("");
  const [slotsLoading, setSlotsLoading] = useState(false);
  const [myApp, setMyApp] = useState<ApplicationOut | null>(null);
  const [pendingApps, setPendingApps] = useState<ApplicationOut[]>([]);
  const [categoryId, setCategoryId] = useState<string>("");
  const [region, setRegion] = useState("");
  const [club, setClub] = useState("");
  const [appMessage, setAppMessage] = useState<string | null>(null);
  const [appBusy, setAppBusy] = useState(false);
  const [rosterBusy, setRosterBusy] = useState(false);
  const [tab, setTab] = useState<TabId>("overview");
  const user = getStoredUser();
  const isGuest = !user;
  const isArchived = Boolean(detail?.archived);
  const role = user?.role ?? "";
  const canOrganize = isStaffRole(role);
  const canModerate = canOrganize && !isArchived;
  const canVerifyOfficial = !isArchived && (canOrganize || isChiefJudgeRole(role));
  const canPublishOfficial = !isArchived && canPublishOfficialResults(role);
  const rosterLocked = Boolean(detail?.roster_locked_at);
  const canUploadProtocol = !isArchived && (canModerate || isJudgeRole(role));
  const canJudge = canUploadProtocol;
  const canCaptureMoments = canCaptureFieldMoments(role);
  const canModerateMoments = !isArchived && canModerateFieldMoments(role);
  const allowedTabs = visibleTabs(user?.role, isGuest);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      const token = getStoredToken();
      try {
        const [d, cats, offs, schedule] = await Promise.all([
          getEventDetail(token, eventId),
          listCategories(token, eventId),
          listOfficials(token, eventId),
          getScheduleHint(token, eventId).catch(() => null),
        ]);
        if (cancelled) return;
        setDetail(d);
        setCategories(cats);
        setOfficials(offs);
        setHint(schedule);
        rememberLastEvent(eventId);

        if (!token) {
          const [published, heatItems] = await Promise.all([
            listResults(null, eventId, "published").catch(() => []),
            listHeats(null, eventId).catch(() => []),
          ]);
          if (!cancelled) {
            setResults(published);
            setHeats(heatItems);
          }
          return;
        }

        const [parts, docs, mine, checks, heatItems, resultItems, profile, protoItems, engine, scores, momentItems] =
          await Promise.all([
          listParticipants(token, eventId),
          listDocuments(token, eventId),
          getMyApplication(token, eventId).catch(() => null),
          listChecklist(token, eventId).catch(() => ({ items: [], total: 0, done_count: 0 })),
          listHeats(token, eventId).catch(() => []),
          listResults(token, eventId).catch(() => []),
          getEventRulesProfile(token, eventId).catch(() => null),
          listProtocolCaptures(token, eventId).catch(() => []),
          getScoringEngine(token, eventId).catch(() => null),
          listJudgeScores(token, eventId).catch(() => []),
          listFieldMoments(token, eventId).catch(() => []),
        ]);
        if (cancelled) return;
        setParticipants(parts);
        setDocuments(docs);
        setMyApp(mine);
        setChecklist(checks.items);
        setChecklistDone(checks.done_count);
        setHeats(heatItems);
        setResults(resultItems);
        setRulesProfile(profile);
        setProtocols(protoItems);
        setFieldMoments(momentItems);
        setScoringEngine(engine);
        setJudgeScores(scores);
        if (engine?.criteria?.length) {
          setCriteriaValues(Object.fromEntries(engine.criteria.map((c) => [c, ""])));
        }
        const preferredHeat =
          heatItems.find((h) => h.status === "on_water") ??
          heatItems.find((h) => h.status === "ready") ??
          heatItems[0];
        if (preferredHeat) {
          setSelectedHeatId(preferredHeat.id);
          try {
            setStartList(await listStartList(token, eventId, preferredHeat.id));
          } catch {
            setStartList([]);
          }
        }
        const stored = getStoredUser();
        if (stored && isStaffRole(stored.role)) {
          try {
            setPendingApps(await listEventApplications(token, eventId, "pending"));
          } catch {
            setPendingApps([]);
          }
          try {
            const bundle = await getOfficialProtocol(token, eventId);
            setProtocolReadiness(bundle.readiness);
          } catch {
            setProtocolReadiness(null);
          }
        }
      } catch (err) {
        if (cancelled) return;
        if (isSessionExpiredError(err)) {
          setSessionExpired(true);
          try {
            const [d, cats, offs, schedule, published, heatItems] = await Promise.all([
              getEventDetail(null, eventId),
              listCategories(null, eventId),
              listOfficials(null, eventId),
              getScheduleHint(null, eventId).catch(() => null),
              listResults(null, eventId, "published").catch(() => []),
              listHeats(null, eventId).catch(() => []),
            ]);
            if (cancelled) return;
            setDetail(d);
            setCategories(cats);
            setOfficials(offs);
            setHint(schedule);
            setResults(published);
            setHeats(heatItems);
            setError(null);
          } catch {
            if (!cancelled) {
              setError("Сессия истекла. Войдите снова, чтобы продолжить.");
            }
          }
          return;
        }
        setError(err instanceof ApiError ? err.message : "Ошибка загрузки события");
      }
    }
    void load();
    return () => {
      cancelled = true;
    };
  }, [eventId]);

  const loadSlots = useCallback(
    async (bookedOnly: boolean) => {
      const token = getStoredToken();
      if (!token) return;
      setSlotsLoading(true);
      try {
        const slots = await listTrainingSlots(token, eventId, { onlyBooked: bookedOnly });
        setTraining(slots);
      } catch (err) {
        setError(err instanceof ApiError ? err.message : "Не удалось загрузить слоты");
      } finally {
        setSlotsLoading(false);
      }
    },
    [eventId],
  );

  useEffect(() => {
    if (!detail) return;
    void loadSlots(onlyBooked);
  }, [detail, onlyBooked, loadSlots]);

  const filtered = useMemo(() => {
    const q = filter.trim().toLowerCase();
    if (!q) return participants;
    return participants.filter((p) => {
      const hay = `${p.full_name} ${p.region || ""} ${p.city || ""}`.toLowerCase();
      return hay.includes(q);
    });
  }, [filter, participants]);

  const medicalStats = useMemo(() => {
    const withMed = participants.filter((p) => p.has_medical_cert).length;
    return { withMed, total: participants.length };
  }, [participants]);

  const catById = useMemo(() => {
    const map = new Map<number, CategoryOut>();
    for (const c of categories) map.set(c.id, c);
    return map;
  }, [categories]);

  const liveHeat = useMemo(() => pickLiveHeat(heats), [heats]);
  const nextHeat = useMemo(() => pickNextHeat(heats, liveHeat), [heats, liveHeat]);
  const currentEntry = useMemo(() => pickCurrentEntry(startList), [startList]);
  const isAthleteView = role === "participant";
  const myParticipant = useMemo(
    () => findMyParticipant(participants, user?.id, myApp),
    [participants, user?.id, myApp],
  );
  const myEntry = useMemo(() => findMyEntry(startList, myParticipant), [startList, myParticipant]);
  const myHeat = useMemo(
    () => (myEntry ? heats.find((h) => h.id === myEntry.heat_id) : liveHeat),
    [heats, myEntry, liveHeat],
  );
  const athleteSnap = useMemo(() => {
    if (!isAthleteView) return null;
    const catId = myParticipant?.category_id ?? myApp?.category_id ?? null;
    const cat = catId != null ? catById.get(catId) : undefined;
    return buildAthleteSnapshot({
      displayName: user?.display_name || "Участник",
      athleteId: myParticipant?.athlete_id || user?.athlete_id,
      myApp,
      participant: myParticipant,
      entry: myEntry,
      heat: myHeat,
      startList,
      categoryTitle: cat?.title || cat?.code || "",
      results,
    });
  }, [
    isAthleteView,
    myParticipant,
    myApp,
    myEntry,
    myHeat,
    startList,
    catById,
    results,
    user?.athlete_id,
    user?.display_name,
  ]);
  const attentionItems = useMemo(() => {
    if (!canModerate) return [];
    const currentHasScore = currentEntry
      ? judgeScores.some((s) => s.participant_id === currentEntry.participant_id)
      : true;
    return buildAttentionItems({
      pendingApps: pendingApps.length,
      rosterLocked,
      participantsCount: participants.length,
      verifiedResults: results.filter((r) => r.status === "verified").length,
      liveHeat,
      currentEntry,
      currentHasScore,
      checklistOpen: Math.max(0, checklist.length - checklistDone),
    });
  }, [
    canModerate,
    pendingApps.length,
    rosterLocked,
    participants.length,
    results,
    liveHeat,
    currentEntry,
    judgeScores,
    checklist.length,
    checklistDone,
  ]);
  const currentAthlete = currentEntry
    ? participants.find((p) => p.id === currentEntry.participant_id)
    : undefined;
  const nextEntry = useMemo(() => {
    if (!currentEntry) return startList.find((e) => e.status === "scheduled" || e.status === "checked_in");
    return nextEntryAfter(startList, currentEntry.participant_id);
  }, [currentEntry, startList]);
  const nextAthlete = nextEntry
    ? participants.find((p) => p.id === nextEntry.participant_id)
    : undefined;

  useEffect(() => {
    if (!canJudge) return;
    const current = pickCurrentEntry(startList);
    if (current && !scoreParticipantId) {
      setScoreParticipantId(String(current.participant_id));
    }
  }, [canJudge, startList, scoreParticipantId]);

  async function downloadDoc(doc: DocumentOut) {
    const token = getStoredToken();
    if (!token) return;
    const res = await fetch(documentDownloadUrl(eventId, doc.id), {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) {
      setError("Не удалось скачать документ");
      return;
    }
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = doc.file_name;
    a.click();
    URL.revokeObjectURL(url);
  }

  async function onSubmitApplication() {
    const token = getStoredToken();
    if (!token) return;
    if (!categoryId) {
      setError("Выберите категорию — без неё заявку не примем.");
      return;
    }
    setAppBusy(true);
    setAppMessage(null);
    setError(null);
    try {
      const created = await submitApplication(token, eventId, {
        category_id: categoryId ? Number(categoryId) : null,
        region: region.trim() || null,
        club: club.trim() || null,
      });
      setMyApp(created);
      setAppMessage("Заявка отправлена и ждёт решения организатора.");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Не удалось подать заявку");
    } finally {
      setAppBusy(false);
    }
  }

  async function onDecideApp(id: number, status: "accepted" | "rejected") {
    const token = getStoredToken();
    if (!token) return;
    setAppBusy(true);
    try {
      await decideEventApplication(token, eventId, id, status);
      setPendingApps(await listEventApplications(token, eventId, "pending"));
      setParticipants(await listParticipants(token, eventId));
      setAppMessage(status === "accepted" ? "Заявка принята." : "Заявка отклонена.");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Ошибка решения по заявке");
    } finally {
      setAppBusy(false);
    }
  }

  async function onToggleRosterLock() {
    const token = getStoredToken();
    if (!token || !canModerate) return;
    const nextLock = !rosterLocked;
    const prompt = nextLock
      ? "Зафиксировать состав? Новые заявки и импорт состава будут закрыты. Check-in и судейство останутся доступны."
      : "Снять фиксацию состава? Организатор снова сможет принимать заявки и импортировать участников.";
    if (!window.confirm(prompt)) return;
    setRosterBusy(true);
    setError(null);
    try {
      if (nextLock) {
        await lockEventRoster(token, eventId);
      } else {
        await unlockEventRoster(token, eventId);
      }
      const [d, checks] = await Promise.all([
        getEventDetail(token, eventId),
        listChecklist(token, eventId),
      ]);
      setDetail(d);
      setChecklist(checks.items);
      setChecklistDone(checks.done_count);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Не удалось изменить фиксацию состава");
    } finally {
      setRosterBusy(false);
    }
  }

  async function refreshChecklist(token: string) {
    const checks = await listChecklist(token, eventId);
    setChecklist(checks.items);
    setChecklistDone(checks.done_count);
  }

  async function onToggleChecklist(item: ChecklistItemOut) {
    const token = getStoredToken();
    if (!token || !canModerate) return;
    try {
      await updateChecklistItem(token, eventId, item.id, !item.is_done);
      await refreshChecklist(token);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Не удалось обновить чеклист");
    }
  }

  async function onUploadProtocol(file: File | null) {
    const token = getStoredToken();
    if (!token || !file || !canUploadProtocol) return;
    setProtocolBusy(true);
    setError(null);
    try {
      await uploadProtocolCapture(token, eventId, file, {
        title: protocolTitle.trim() || file.name,
        kind: protocolKind,
        heat_id: selectedHeatId ?? undefined,
      });
      setProtocolTitle("");
      setProtocols(await listProtocolCaptures(token, eventId));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Не удалось загрузить протокол");
    } finally {
      setProtocolBusy(false);
    }
  }

  async function downloadProtocol(item: ProtocolCaptureOut) {
    const token = getStoredToken();
    if (!token) return;
    const res = await fetch(protocolCaptureFileUrl(eventId, item.id), {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) {
      setError("Не удалось скачать протокол");
      return;
    }
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = item.file_name;
    a.click();
    URL.revokeObjectURL(url);
  }

  async function onVerifyProtocol(item: ProtocolCaptureOut, status: "verified" | "published" | "rejected") {
    const token = getStoredToken();
    if (!token) return;
    if (status === "published" && !canPublishOfficial) return;
    if (status !== "published" && !canVerifyOfficial) return;
    try {
      await updateProtocolCapture(token, eventId, item.id, { status });
      setProtocols(await listProtocolCaptures(token, eventId));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Не удалось обновить статус протокола");
    }
  }

  async function refreshProtocolReadiness() {
    const token = getStoredToken();
    if (!token || !canOrganize) return;
    try {
      const bundle = await getOfficialProtocol(token, eventId);
      setProtocolReadiness(bundle.readiness);
    } catch {
      setProtocolReadiness(null);
    }
  }

  async function downloadOfficialProtocolJson() {
    const token = getStoredToken();
    if (!token || !canOrganize) return;
    setExportBusy(true);
    setError(null);
    try {
      const res = await fetch(officialProtocolDownloadUrl(eventId), {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) {
        throw new ApiError("Не удалось скачать официальный протокол", res.status);
      }
      const blob = await res.blob();
      const slug = detail?.slug || `event-${eventId}`;
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${slug}-official-protocol.json`;
      a.click();
      URL.revokeObjectURL(url);
      await refreshProtocolReadiness();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Не удалось экспортировать протокол");
    } finally {
      setExportBusy(false);
    }
  }

  async function openOfficialProtocolHtml() {
    const token = getStoredToken();
    if (!token || !canOrganize) return;
    setExportBusy(true);
    setError(null);
    try {
      const res = await fetch(officialProtocolHtmlUrl(eventId), {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) {
        throw new ApiError("Не удалось открыть печатную версию", res.status);
      }
      const html = await res.text();
      const w = window.open("", "_blank");
      if (w) {
        w.document.write(html);
        w.document.close();
      }
      await refreshProtocolReadiness();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Не удалось открыть HTML-протокол");
    } finally {
      setExportBusy(false);
    }
  }

  async function onSubmitJudgeScore() {
    const token = getStoredToken();
    if (!token || !canJudge || !scoringEngine) return;
    const pid = Number(scoreParticipantId);
    if (!pid) {
      setError("Выберите участника для оценки.");
      return;
    }
    const criteria: Record<string, number> = {};
    for (const key of scoringEngine.criteria) {
      const raw = criteriaValues[key];
      const num = Number(raw);
      if (raw === "" || Number.isNaN(num)) {
        setError(`Заполните критерий: ${scoringEngine.criteria_labels_ru[key] || key}`);
        return;
      }
      criteria[key] = num;
    }
    setScoreBusy(true);
    setError(null);
    try {
      await submitJudgeScore(token, eventId, {
        participant_id: pid,
        heat_id: selectedHeatId,
        attempt_no: 1,
        criteria,
      });
      setJudgeScores(await listJudgeScores(token, eventId));
      const nextAthleteEntry = nextEntryAfter(startList, pid);
      if (nextAthleteEntry) {
        setScoreParticipantId(String(nextAthleteEntry.participant_id));
      }
      if (scoringEngine.criteria.length) {
        setCriteriaValues(Object.fromEntries(scoringEngine.criteria.map((c) => [c, ""])));
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Не удалось сохранить оценку судьи");
    } finally {
      setScoreBusy(false);
    }
  }

  async function onAggregateScores() {
    const token = getStoredToken();
    if (!token || !canModerate) return;
    const pid = Number(scoreParticipantId);
    if (!pid) {
      setError("Выберите участника для агрегации.");
      return;
    }
    setScoreBusy(true);
    setError(null);
    try {
      const panel = await aggregateJudgeScores(token, eventId, {
        participant_id: pid,
        heat_id: selectedHeatId,
        attempt_no: 1,
        write_result_draft: true,
      });
      setJudgeScores(await listJudgeScores(token, eventId));
      setResults(await listResults(token, eventId));
      setAppMessage(
        `Панель судей: ${panel.panel_score} (${panel.judge_count} судей). Черновик результата ${panel.result_id ?? "пока без номера"}.`,
      );
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Не удалось агрегировать оценки");
    } finally {
      setScoreBusy(false);
    }
  }

  async function onUploadDoc(file: File | null) {
    const token = getStoredToken();
    if (!token || !file || !canModerate) return;
    setUploadBusy(true);
    setError(null);
    try {
      await uploadDocument(token, eventId, file, {
        title: uploadTitle.trim() || file.name,
        kind: uploadKind,
        language: "ru",
      });
      setDocuments(await listDocuments(token, eventId));
      setUploadTitle("");
      await refreshChecklist(token);
      const d = await getEventDetail(token, eventId);
      setDetail(d);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Не удалось загрузить документ");
    } finally {
      setUploadBusy(false);
    }
  }

  async function onDeleteDoc(doc: DocumentOut) {
    const token = getStoredToken();
    if (!token || !canModerate) return;
    if (!window.confirm(`Удалить «${doc.title}»?`)) return;
    try {
      await deleteDocument(token, eventId, doc.id);
      setDocuments(await listDocuments(token, eventId));
      await refreshChecklist(token);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Не удалось удалить документ");
    }
  }

  async function onCreateHeat() {
    const token = getStoredToken();
    if (!token || !canModerate) return;
    if (!heatCode.trim() || !heatTitle.trim()) {
      setError("Укажите код и название heat");
      return;
    }
    try {
      const heat = await createHeat(token, eventId, {
        code: heatCode.trim(),
        title: heatTitle.trim(),
        heat_number: heats.length + 1,
        category_id: categoryId ? Number(categoryId) : null,
      });
      const items = await listHeats(token, eventId);
      setHeats(items);
      setSelectedHeatId(heat.id);
      setHeatCode("");
      setHeatTitle("");
      await refreshChecklist(token);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Не удалось создать заезд");
    }
  }

  async function loadStartList(heatId: number) {
    const token = getStoredToken();
    if (!token) return;
    try {
      setStartList(await listStartList(token, eventId, heatId));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Не удалось загрузить стартовый список");
    }
  }

  async function onSelectHeat(heatId: number) {
    setSelectedHeatId(heatId);
    await loadStartList(heatId);
  }

  async function onAddToStartList() {
    const token = getStoredToken();
    if (!token || !canModerate || !selectedHeatId) return;
    const pid = Number(addParticipantId);
    if (!pid) {
      setError("Выберите участника");
      return;
    }
    try {
      await addStartListEntry(token, eventId, selectedHeatId, {
        participant_id: pid,
        start_order: startList.length + 1,
      });
      await loadStartList(selectedHeatId);
      setAddParticipantId("");
      await refreshChecklist(token);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Не удалось добавить в start list");
    }
  }

  async function onFillStartList() {
    const token = getStoredToken();
    if (!token || !canModerate || !selectedHeatId) return;
    try {
      await fillStartList(
        token,
        eventId,
        selectedHeatId,
        categoryId ? Number(categoryId) : null,
      );
      await loadStartList(selectedHeatId);
      await refreshChecklist(token);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Не удалось заполнить стартовый список");
    }
  }

  async function onSaveResultDraft() {
    const token = getStoredToken();
    if (!token || !canVerifyOfficial) return;
    const pid = Number(resultParticipantId);
    if (!pid) {
      setError("Выберите участника для результата");
      return;
    }
    try {
      await upsertResultDraft(token, eventId, {
        participant_id: pid,
        score: resultScore ? Number(resultScore) : null,
        place: resultPlace ? Number(resultPlace) : null,
        heat_id: selectedHeatId,
      });
      setResults(await listResults(token, eventId));
      setResultScore("");
      setResultPlace("");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Не удалось сохранить черновик результата");
    }
  }

  async function onResultStatus(row: ResultOut, status: "verified" | "published" | "void" | "draft") {
    const token = getStoredToken();
    if (!token || !(canVerifyOfficial || canPublishOfficial)) return;
    try {
      await updateResultStatus(token, eventId, row.id, status);
      setResults(await listResults(token, eventId));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Не удалось сменить статус результата");
    }
  }

  async function onEntryStatus(entry: StartListEntryOut, status: string) {
    const token = getStoredToken();
    if (!token || !canModerate || !selectedHeatId) return;
    try {
      await updateStartListStatus(token, eventId, selectedHeatId, entry.id, status);
      await loadStartList(selectedHeatId);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Не удалось обновить статус");
    }
  }

  async function onHeatStatus(heat: HeatOut, status: string) {
    const token = getStoredToken();
    if (!token || !canModerate) return;
    try {
      await updateHeatStatus(token, eventId, heat.id, status);
      setHeats(await listHeats(token, eventId));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Не удалось обновить heat");
    }
  }

  useEffect(() => {
    if (selectedHeatId != null) {
      void loadStartList(selectedHeatId);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedHeatId, eventId]);

  const allowedTabsKey = allowedTabs.join("|");

  useEffect(() => {
    const raw = typeof window !== "undefined" ? window.location.hash.replace("#", "") : "";
    const allowed = allowedTabsKey.split("|").filter(Boolean);
    if (raw && allowed.includes(raw)) {
      setTab(raw as TabId);
    }
  }, [eventId, allowedTabsKey]);

  function selectTab(id: TabId) {
    setTab(id);
    if (typeof window !== "undefined") {
      history.replaceState(null, "", `#${id}`);
    }
  }

  const publishedResults = results.filter((r) => r.status === "published");

  const tabs: { id: TabId; label: string }[] = [
    { id: "overview", label: isAthleteView ? "Мой старт" : canModerate ? "Пульт" : "Обзор" },
    { id: "checklist", label: `Подготовка (${checklistDone}/${checklist.length || 7})` },
    { id: "participants", label: `Состав (${participants.length})` },
    { id: "slots", label: "Слоты" },
    { id: "docs", label: `Документы (${documents.length})` },
    { id: "protocol", label: `Протокол (${protocols.length})` },
    { id: "moments", label: `Моменты (${fieldMoments.length})` },
    { id: "scoring", label: "Судейство" },
    { id: "heats", label: `Заезды (${heats.length})` },
    { id: "results", label: "Результаты" },
    {
      id: "apps",
      label: canModerate ? `Заявки (${pendingApps.length})` : "Заявка",
    },
  ];

  return (
    <>
      <AppHeader subtitle="Карточка события" />
      <main id="main" className={styles.main}>
        <p className={styles.muted}>
          <Link href="/events">← К списку событий</Link>
        </p>

        {sessionExpired ? (
          <div className={styles.nextAction} role="status">
            <strong>Сессия истекла</strong>
            <p className={styles.muted}>Войдите снова — вернёмся на эту карточку события.</p>
            <Link href={loginHref(`/events/${eventId}`)} className="btn btnPrimary btnSm">
              Войти снова
            </Link>
          </div>
        ) : null}

        {error && !sessionExpired ? (
          <div className={styles.panel} role="alert">
            <p className={styles.error}>{error}</p>
          </div>
        ) : null}

        {detail ? (
          <>
            <div className={styles.itemHead}>
              <h1 className={styles.title}>{detail.title}</h1>
              <StatusBadge status={detail.status} />
            </div>
            {detail.archived ? (
              <div className={styles.panel} role="status">
                <strong>Архив</strong>
                <p className={styles.muted}>
                  Событие завершено или отменено — только просмотр. Экспорт протокола доступен.
                </p>
                {canOrganize ? (
                  <button
                    type="button"
                    className="btn btnPrimary btnSm"
                    onClick={() => {
                      const token = getStoredToken();
                      if (!token) return;
                      void updateEventStatus(token, eventId, "live")
                        .then(() => getEventDetail(token, eventId))
                        .then((d) => setDetail(d))
                        .catch((err) =>
                          setError(err instanceof ApiError ? err.message : "Не удалось открыть событие"),
                        );
                    }}
                  >
                    Вернуть в работу
                  </button>
                ) : null}
              </div>
            ) : null}
            {detail.description ? <p className={styles.itemDesc}>{detail.description}</p> : null}
            <dl className={styles.meta}>
              <div>
                <dt>Город</dt>
                <dd>{detail.city || "—"}</dd>
              </div>
              <div>
                <dt>Даты</dt>
                <dd>{formatEventPeriod(detail.starts_at, detail.ends_at)}</dd>
              </div>
              <div>
                <dt>Дисциплины</dt>
                <dd>{detail.disciplines || "—"}</dd>
              </div>
              <div>
                <dt>Состав</dt>
                <dd>
                  {detail.participants_count} участников · {detail.categories_count} категорий
                  {rosterLocked ? " · зафиксирован" : ""}
                </dd>
              </div>
            </dl>
            {canModerate ? (
              <div className={styles.panel} role="status">
                <strong>{rosterLocked ? "Состав зафиксирован" : "Состав ещё открыт"}</strong>
                <p className={styles.muted}>
                  {rosterLocked
                    ? "Новые заявки и импорт закрыты. Check-in, заезды и судейство доступны. Официальный результат публикует главный судья."
                    : "После проверки заявок зафиксируйте состав — это обязательный шаг перед официальными результатами."}
                </p>
                <button
                  type="button"
                  className={rosterLocked ? "btn btnSecondary btnSm" : "btn btnPrimary btnSm"}
                  disabled={rosterBusy}
                  onClick={() => void onToggleRosterLock()}
                >
                  {rosterBusy
                    ? "Сохранение…"
                    : rosterLocked
                      ? "Снять фиксацию"
                      : "Зафиксировать состав"}
                </button>
              </div>
            ) : rosterLocked ? (
              <p className={styles.muted}>Состав события зафиксирован — новые заявки не принимаются.</p>
            ) : null}

            {liveHeat ? (
              <div className={styles.liveBar} role="status">
                <div>
                  <strong>Сейчас: {liveHeat.title}</strong>
                  <p className={styles.muted} style={{ margin: "0.25rem 0 0" }}>
                    Заезд {liveHeat.code}
                    {liveHeat.status === "on_water" ? " — на воде" : " — готов к старту"}
                  </p>
                </div>
                {allowedTabs.includes("heats") ? (
                  <button type="button" className="btn btnPrimary btnSm" onClick={() => selectTab("heats")}>
                    К заездам
                  </button>
                ) : null}
              </div>
            ) : null}

            {isGuest && !sessionExpired ? (
              <div className={styles.nextAction}>
                <strong>Следующий шаг</strong>
                <p className={styles.muted}>Войдите, чтобы подать заявку и увидеть свой слот.</p>
                <Link href={loginHref(`/events/${eventId}`)} className="btn btnPrimary btnSm">
                  Войти
                </Link>
              </div>
            ) : null}

            {!isGuest && canModerate && pendingApps.length > 0 ? (
              <div className={styles.nextAction}>
                <strong>Следующий шаг: заявки</strong>
                <p className={styles.muted}>
                  {pendingApps.length} заявки ждут решения организатора.
                </p>
                <button type="button" className="btn btnPrimary btnSm" onClick={() => selectTab("apps")}>
                  Открыть заявки
                </button>
              </div>
            ) : null}

            {!isGuest && canModerate && !rosterLocked && pendingApps.length === 0 && participants.length > 0 ? (
              <div className={styles.nextAction}>
                <strong>Следующий шаг: зафиксировать состав</strong>
                <p className={styles.muted}>
                  После проверки участников зафиксируйте состав перед официальными результатами.
                </p>
                <button
                  type="button"
                  className="btn btnPrimary btnSm"
                  disabled={rosterBusy}
                  onClick={() => void onToggleRosterLock()}
                >
                  {rosterBusy ? "Сохранение…" : "Зафиксировать состав"}
                </button>
              </div>
            ) : null}

            {!isGuest && canJudge && liveHeat ? (
              <div className={styles.nextAction}>
                <strong>Следующий шаг: судейство</strong>
                <p className={styles.muted}>
                  Идёт заезд {liveHeat.code}. Оцените текущего спортсмена.
                </p>
                <button type="button" className="btn btnPrimary btnSm" onClick={() => selectTab("scoring")}>
                  К судейству
                </button>
              </div>
            ) : null}

            {!isGuest && !myApp && detail.status === "registration_open" && allowedTabs.includes("apps") && !canModerate && !isAthleteView ? (
              <div className={styles.nextAction}>
                <strong>Следующий шаг: заявка</strong>
                <p className={styles.muted}>Выберите категорию и отправьте заявку организатору.</p>
                <button type="button" className="btn btnPrimary btnSm" onClick={() => selectTab("apps")}>
                  Подать заявку
                </button>
              </div>
            ) : null}

            {!isGuest && myApp && !canModerate && !isAthleteView ? (
              <div className={styles.nextAction}>
                <strong>Следующий шаг</strong>
                <p className={styles.muted} style={{ margin: "0.35rem 0 0.5rem" }}>
                  Заявка: <StatusBadge status={myApp.status} kind="application" /> · {myApp.full_name}
                </p>
                {liveHeat && allowedTabs.includes("heats") ? (
                  <button type="button" className="btn btnPrimary btnSm" onClick={() => selectTab("heats")}>
                    Открыть стартовый список
                  </button>
                ) : publishedResults.length > 0 && allowedTabs.includes("results") ? (
                  <button type="button" className="btn btnPrimary btnSm" onClick={() => selectTab("results")}>
                    Открыть результаты
                  </button>
                ) : null}
              </div>
            ) : null}

            {canCaptureMoments && !canModerate && allowedTabs.includes("moments") ? (
              <div className={styles.nextAction}>
                <strong>Следующий шаг: снять момент</strong>
                <p className={styles.muted}>
                  Бэкстейдж, взгляд пилота, маршал на старте — короткие кадры для эфира. Это не протокол
                  судьи.
                </p>
                <button type="button" className="btn btnPrimary btnSm" onClick={() => selectTab("moments")}>
                  Открыть камеру
                </button>
              </div>
            ) : null}

            <div className={styles.tabs} role="tablist" aria-label="Разделы события">
              {tabs
                .filter((t) => allowedTabs.includes(t.id))
                .map((t) => (
                  <button
                    key={t.id}
                    type="button"
                    role="tab"
                    id={`tab-${t.id}`}
                    aria-selected={tab === t.id}
                    aria-controls={`panel-${t.id}`}
                    className={`${styles.tab} ${tab === t.id ? styles.tabActive : ""}`}
                    onClick={() => selectTab(t.id)}
                  >
                    {t.label}
                  </button>
                ))}
            </div>

            {tab === "overview" ? (
              <>
                {isAthleteView && athleteSnap ? (
                  <AthleteEventHome
                    snapshot={athleteSnap}
                    onOpenStartList={() => selectTab("heats")}
                    onOpenResults={() => selectTab("results")}
                    onApply={() => selectTab("apps")}
                    canOpenStartList={allowedTabs.includes("heats")}
                    canOpenResults={allowedTabs.includes("results")}
                  />
                ) : null}

                {canModerate ? (
                  <OrganizerControlRoom
                    nowHeat={liveHeat}
                    nowName={currentAthlete?.full_name}
                    nowEntry={currentEntry}
                    nextHeat={nextHeat}
                    nextName={nextAthlete?.full_name}
                    attention={attentionItems}
                    onOpenTab={(id) => selectTab(id as TabId)}
                  />
                ) : null}

                {detail.participants_count === 0 ? (
                  <p className={styles.muted}>
                    Состав этого события пуст. Импорт Excel привязывается к событию, выбранному в
                    разделе «Импорт», а не ко всем карточкам сразу.
                  </p>
                ) : null}

                {hint ? (
                  <>
                    <h2 className={styles.itemTitle}>Расписание (кратко)</h2>
                    <p className={styles.itemDesc}>{hint.summary}</p>
                    <ul className={styles.list}>
                      {hint.notes.map((note) => (
                        <li key={note} className={styles.item}>
                          <span className={styles.muted}>{note}</span>
                        </li>
                      ))}
                    </ul>
                  </>
                ) : null}

                {rulesProfile ? (
                  <>
                    <h2 className={styles.itemTitle}>Правила события</h2>
                    <dl className={styles.meta}>
                      <div>
                        <dt>Федерация</dt>
                        <dd>{rulesProfile.governing_body}</dd>
                      </div>
                      <div>
                        <dt>Санкция</dt>
                        <dd>{rulesProfile.sanction_body}</dd>
                      </div>
                      <div>
                        <dt>Режим оценки</dt>
                        <dd>{scoringEngineLabel(rulesProfile.scoring_mode)}</dd>
                      </div>
                    </dl>
                  </>
                ) : null}

                <h2 className={styles.itemTitle}>Судейский корпус</h2>
                <ul className={styles.list}>
                  {officials.length === 0 ? (
                    <li className={styles.item}>
                      <span className={styles.muted}>Судейский состав пока не загружен.</span>
                    </li>
                  ) : (
                    officials.map((o) => (
                      <li key={o.id} className={styles.item}>
                        <strong>
                          {o.sort_order}. {o.full_name}
                        </strong>
                        <div className={styles.muted}>
                          {[o.position, o.region, o.judge_category].filter(Boolean).join(" · ")}
                        </div>
                      </li>
                    ))
                  )}
                </ul>

                <h2 className={styles.itemTitle}>Категории</h2>
                <ul className={styles.list}>
                  {categories.map((c) => (
                    <li key={c.id} className={styles.item}>
                      <strong>{c.title}</strong>
                      <div className={styles.muted}>{c.discipline}</div>
                    </li>
                  ))}
                </ul>
              </>
            ) : null}

            {tab === "apps" ? (
              <>
                <h2 className={styles.itemTitle}>Моя заявка</h2>
                {appMessage ? <p className={styles.muted}>{appMessage}</p> : null}
                {myApp ? (
                  <div className={styles.panel}>
                    <p>
                      Статус: <StatusBadge status={myApp.status} kind="application" /> · {myApp.full_name}
                    </p>
                    <p className={styles.muted}>
                      {[myApp.region, myApp.club].filter(Boolean).join(" · ") || "—"}
                    </p>
                  </div>
                ) : detail.status === "registration_open" && !rosterLocked ? (
                  <div className={styles.panel}>
                    <p className={styles.muted}>
                      Подать заявку на участие (ФИО берётся из профиля аккаунта).
                    </p>
                    <label className={styles.muted}>
                      Категория{" "}
                      <select
                        value={categoryId}
                        onChange={(e) => setCategoryId(e.target.value)}
                        style={{ marginLeft: "0.4rem" }}
                      >
                        <option value="">Выберите категорию</option>
                        {categories.map((c) => (
                          <option key={c.id} value={String(c.id)}>
                            {c.discipline ? `${c.discipline}: ` : ""}
                            {c.title}
                          </option>
                        ))}
                      </select>
                    </label>
                    <div style={{ display: "grid", gap: "0.5rem", marginTop: "0.75rem" }}>
                      <input
                        placeholder="Регион"
                        value={region}
                        onChange={(e) => setRegion(e.target.value)}
                      />
                      <input
                        placeholder="Клуб"
                        value={club}
                        onChange={(e) => setClub(e.target.value)}
                      />
                      <button
                        type="button"
                        className="btn btnPrimary"
                        disabled={appBusy}
                        onClick={() => void onSubmitApplication()}
                      >
                        {appBusy ? "Отправка…" : "Отправить заявку"}
                      </button>
                    </div>
                  </div>
                ) : (
                  <p className={styles.muted}>Регистрация на событие сейчас закрыта.</p>
                )}

                {canModerate ? (
                  <>
                    <h2 className={styles.itemTitle}>
                      Заявки на участие ({pendingApps.length})
                    </h2>
                    <ul className={styles.list}>
                      {pendingApps.length === 0 ? (
                        <li className={styles.item}>
                          <span className={styles.muted}>Нет новых заявок.</span>
                        </li>
                      ) : (
                        pendingApps.map((a) => (
                          <li key={a.id} className={styles.item}>
                            <div className={styles.itemHead}>
                              <strong>{a.full_name}</strong>
                              <span>
                                <button
                                  type="button"
                                  className="btn btnPrimary btnSm"
                                  disabled={appBusy || rosterLocked}
                                  onClick={() => void onDecideApp(a.id, "accepted")}
                                >
                                  Принять
                                </button>{" "}
                                <button
                                  type="button"
                                  className="btn btnDanger btnSm"
                                  disabled={appBusy}
                                  onClick={() => {
                                    if (window.confirm(`Отклонить заявку ${a.full_name}?`)) {
                                      void onDecideApp(a.id, "rejected");
                                    }
                                  }}
                                >
                                  Отклонить
                                </button>
                              </span>
                            </div>
                            <div className={styles.muted}>
                              {[a.region, a.club, a.status].filter(Boolean).join(" · ")}
                            </div>
                          </li>
                        ))
                      )}
                    </ul>
                  </>
                ) : null}
              </>
            ) : null}

            {tab === "slots" ? (
              <>
                <div className={styles.itemHead}>
                  <h2 className={styles.itemTitle}>Тренировочные слоты</h2>
                  <label className={styles.muted}>
                    <input
                      type="checkbox"
                      checked={onlyBooked}
                      onChange={(e) => setOnlyBooked(e.target.checked)}
                    />{" "}
                    только занятые
                  </label>
                </div>
                {slotsLoading ? <p className={styles.muted}>Обновляем слоты…</p> : null}
                <ul className={styles.list}>
                  {training.length === 0 ? (
                    <li className={styles.item}>
                      <span className={styles.muted}>
                        {onlyBooked
                          ? "Нет занятых слотов. Снимите фильтр, чтобы увидеть все."
                          : "Слоты ещё не загружены."}
                      </span>
                    </li>
                  ) : (
                    training.map((s) => (
                      <li key={s.id} className={styles.item}>
                        <strong>
                          {s.slot_date} {s.slot_time || ""} — {s.athlete_name || s.status}
                        </strong>
                        <div className={styles.muted}>
                          {[s.discipline, s.venue, s.notes].filter(Boolean).join(" · ")}
                        </div>
                      </li>
                    ))
                  )}
                </ul>
              </>
            ) : null}

            {tab === "checklist" ? (
              <>
                <h2 className={styles.itemTitle}>
                  Подготовка события ({checklistDone}/{checklist.length})
                </h2>
                <p className={styles.muted}>
                  Чеклист живёт в Event App (сайт — только витрина). Часть пунктов отмечается
                  автоматически по данным события.
                </p>
                <ul className={styles.list}>
                  {checklist.map((item) => (
                    <li key={item.id} className={styles.item}>
                      <div className={styles.itemHead}>
                        <strong>
                          {item.is_done ? "✓ " : "○ "}
                          {item.title}
                        </strong>
                        {canModerate ? (
                          <button
                            type="button"
                            className="btn btnPrimary btnSm"
                            onClick={() => void onToggleChecklist(item)}
                          >
                            {item.is_done ? "Снять" : "Отметить"}
                          </button>
                        ) : null}
                      </div>
                      {canModerate ? <div className={styles.muted}>{item.code}</div> : null}
                    </li>
                  ))}
                </ul>
                <div className={styles.section}>
                  <AppDownloadCard context={`events/${eventId}/checklist`} />
                </div>
              </>
            ) : null}

            {tab === "docs" ? (
              <>
                <h2 className={styles.itemTitle}>Документы</h2>
                {canModerate ? (
                  <div className={styles.panel}>
                    <p className={styles.muted}>Загрузка PDF / XLSX / XLS (до 25 МБ).</p>
                    <label className={styles.muted}>
                      Название{" "}
                      <input
                        value={uploadTitle}
                        onChange={(e) => setUploadTitle(e.target.value)}
                        placeholder="Бюллетень №1"
                        style={{
                          marginLeft: "0.5rem",
                          padding: "0.45rem 0.7rem",
                          borderRadius: "8px",
                          border: "1px solid var(--line)",
background: "var(--surface)",
                            color: "var(--ink)",
                        }}
                      />
                    </label>{" "}
                    <label className={styles.muted}>
                      Тип{" "}
                      <select
                        value={uploadKind}
                        onChange={(e) => setUploadKind(e.target.value)}
                        style={{
                          marginLeft: "0.35rem",
                          padding: "0.45rem 0.5rem",
                          borderRadius: "8px",
                          border: "1px solid var(--line)",
background: "var(--surface)",
                            color: "var(--ink)",
                        }}
                      >
                        <option value="bulletin">Бюллетень</option>
                        <option value="protocol">Протокол</option>
                        <option value="start_list">Стартовый список</option>
                        <option value="official_appointment">Назначение судей</option>
                        <option value="schedule">Расписание</option>
                        <option value="rules">Правила</option>
                        <option value="other">Другое</option>
                      </select>
                    </label>{" "}
                    <input
                      type="file"
                      accept=".pdf,.xlsx,.xls,application/pdf"
                      disabled={uploadBusy}
                      onChange={(e) => {
                        const f = e.target.files?.[0] ?? null;
                        void onUploadDoc(f);
                        e.target.value = "";
                      }}
                    />
                  </div>
                ) : null}
                <ul className={styles.list}>
                  {documents.length === 0 ? (
                    <li className={styles.item}>
                      <span className={styles.muted}>Документов пока нет.</span>
                    </li>
                  ) : (
                    documents.map((d) => (
                      <li key={d.id} className={styles.item}>
                        <div className={styles.itemHead}>
                          <strong>{d.title}</strong>
                          <span>
                            <button
                              type="button"
                              className="btn btnPrimary btnSm"
                              onClick={() => void downloadDoc(d)}
                            >
                              Скачать
                            </button>
                            {canModerate ? (
                              <button
              type="button"
              className="btn btnDanger btnSm"
              style={{ marginLeft: "0.5rem" }}
              onClick={() => void onDeleteDoc(d)}
            >
                                Удалить
                              </button>
                            ) : null}
                          </span>
                        </div>
                        <div className={styles.muted}>
                          {labelOf(DOCUMENT_KIND_LABELS, d.kind)} · {d.file_name}
                        </div>
                      </li>
                    ))
                  )}
                </ul>
              </>
            ) : null}

            {tab === "moments" ? (
              <FieldMomentsPanel
                eventId={eventId}
                heats={heats}
                selectedHeatId={selectedHeatId}
                canModerate={canModerateMoments}
                archived={isArchived}
                items={fieldMoments}
                onChange={setFieldMoments}
              />
            ) : null}

            {tab === "protocol" ? (
              <>
                <h2 className={styles.itemTitle}>Фото / PDF протокола</h2>
                <p className={styles.muted}>
                  Листы судей WSWS (DRIVE) или бумажный протокол. Загрузка: JPG/PNG/WebP/PDF до 15 МБ.
                </p>
                {canOrganize ? (
                  <div className={styles.panel}>
                    <strong>Официальный протокол (export)</strong>
                    <p className={styles.muted}>
                      JSON-файл для федерации и печатная версия. Нужны опубликованные результаты
                      или опубликованные вложения протокола.
                      {protocolReadiness ? (
                        <>
                          {" "}
                          Статус:{" "}
                          <strong>{protocolReadiness.official_ready ? "готов" : "черновик"}</strong>
                          {" · "}
                          результатов: {protocolReadiness.published_results_count}
                          {" · "}
                          вложений: {protocolReadiness.published_protocol_captures_count}
                        </>
                      ) : null}
                    </p>
                    <button
                      type="button"
                      className="btn btnSecondary btnSm"
                      disabled={exportBusy}
                      onClick={() => void downloadOfficialProtocolJson()}
                    >
                      Файл для федерации
                    </button>{" "}
                    <button
                      type="button"
                      className="btn btnPrimary btnSm"
                      disabled={exportBusy}
                      onClick={() => void openOfficialProtocolHtml()}
                    >
                      Открыть для печати
                    </button>
                  </div>
                ) : null}
                {canUploadProtocol ? (
                  <div className={styles.panel}>
                    <label className={styles.muted}>
                      Название{" "}
                      <input
                        value={protocolTitle}
                        onChange={(e) => setProtocolTitle(e.target.value)}
                        placeholder="Лист судьи 1 · Heat A"
                        style={{
                          marginLeft: "0.5rem",
                          padding: "0.45rem 0.7rem",
                          borderRadius: "8px",
                          border: "1px solid var(--line)",
background: "var(--surface)",
                            color: "var(--ink)",
                        }}
                      />
                    </label>{" "}
                    <label className={styles.muted}>
                      Тип{" "}
                      <select
                        value={protocolKind}
                        onChange={(e) => setProtocolKind(e.target.value)}
                        style={{
                          marginLeft: "0.35rem",
                          padding: "0.45rem 0.5rem",
                          borderRadius: "8px",
                          border: "1px solid var(--line)",
background: "var(--surface)",
                            color: "var(--ink)",
                        }}
                      >
                        <option value="judge_sheet">Лист судьи</option>
                        <option value="chief_protocol">Протокол главного судьи</option>
                        <option value="photo_result">Фото табло</option>
                        <option value="other">Другое</option>
                      </select>
                    </label>{" "}
                    <input
                      type="file"
                      accept="image/jpeg,image/png,image/webp,application/pdf,.jpg,.jpeg,.png,.webp,.pdf"
                      capture="environment"
                      disabled={protocolBusy}
                      onChange={(e) => {
                        const f = e.target.files?.[0] ?? null;
                        void onUploadProtocol(f);
                        e.target.value = "";
                      }}
                    />
                  </div>
                ) : null}
                <ul className={styles.list}>
                  {protocols.length === 0 ? (
                    <li className={styles.item}>
                      <span className={styles.muted}>Протоколы ещё не загружены.</span>
                    </li>
                  ) : (
                    protocols.map((p) => (
                      <li key={p.id} className={styles.item}>
                        <div className={styles.itemHead}>
                          <strong>
                            {p.title}{" "}
                            <StatusBadge status={p.status} kind="protocol" />
                          </strong>
                          <span>
                            <button
                              type="button"
                              className="btn btnPrimary btnSm"
                              onClick={() => void downloadProtocol(p)}
                            >
                              Открыть
                            </button>
                            {canVerifyOfficial && p.status === "draft" ? (
                              <button
                                type="button"
                                className="btn btnPrimary btnSm"
                                style={{ marginLeft: "0.5rem" }}
                                onClick={() => void onVerifyProtocol(p, "verified")}
                              >
                                Проверить
                              </button>
                            ) : null}
                            {canPublishOfficial && p.status === "verified" ? (
                              <button
                                type="button"
                                className="btn btnPrimary btnSm"
                                style={{ marginLeft: "0.5rem" }}
                                onClick={() => void onVerifyProtocol(p, "published")}
                              >
                                Утвердить (главный судья)
                              </button>
                            ) : null}
                          </span>
                        </div>
                        <div className={styles.muted}>
                          {labelOf(PROTOCOL_KIND_LABELS, p.kind)} · {p.file_name}
                          {p.heat_id ? ` · заезд ${heats.find((h) => h.id === p.heat_id)?.code || p.heat_id}` : ""}
                          {p.notes ? ` · ${p.notes}` : ""}
                        </div>
                      </li>
                    ))
                  )}
                </ul>
              </>
            ) : null}

            {tab === "scoring" ? (
              <>
                <h2 className={styles.itemTitle}>Сейчас оценивается</h2>
                <p className={styles.muted}>
                  Движок: <strong>{scoringEngineLabel(scoringEngine?.engine)}</strong>
                  {scoringEngine?.engine === "MANUAL_PLACE"
                    ? " — для этого события введите место на вкладке «Результаты» или приложите фото протокола."
                    : " — каждый судья вводит критерии; организатор считает итог и отправляет в результаты."}
                </p>
                {scoringEngine && scoringEngine.engine !== "MANUAL_PLACE" && canJudge ? (
                  <div className={styles.panel}>
                    {currentAthlete && currentEntry ? (
                      <div className={styles.currentAthlete} role="status">
                        <div className={styles.itemHead}>
                          <strong>
                            {currentEntry.bib_number ? `№${currentEntry.bib_number} · ` : ""}
                            {currentAthlete.full_name}
                          </strong>
                          <span className={styles.phaseChip}>
                            {labelOf(ENTRY_STATUS_LABELS, currentEntry.status)}
                          </span>
                        </div>
                        <p className={styles.muted} style={{ margin: "0.35rem 0 0" }}>
                          {liveHeat ? `Заезд ${liveHeat.code}` : "Заезд не выбран"}
                          {currentAthlete.athlete_id ? ` · ${currentAthlete.athlete_id}` : ""}
                        </p>
                        {String(scoreParticipantId) !== String(currentAthlete.id) ? (
                          <button
                            type="button"
                            className="btn btnPrimary btnSm"
                            style={{ marginTop: "0.6rem" }}
                            onClick={() => setScoreParticipantId(String(currentAthlete.id))}
                          >
                            Оценивать этого спортсмена
                          </button>
                        ) : (
                          <p className={styles.muted} style={{ marginTop: "0.5rem" }}>
                            Оценка идёт текущему спортсмену на воде.
                          </p>
                        )}
                      </div>
                    ) : (
                      <p className={styles.muted}>Нет спортсмена со статусом «на воде» или «готов» — выберите вручную.</p>
                    )}
                    <label className={styles.muted} htmlFor="judge-target">
                      Другой участник (если цель не на воде)
                    </label>
                    <select
                      id="judge-target"
                      className={styles.fieldControl}
                      value={scoreParticipantId}
                      onChange={(e) => setScoreParticipantId(e.target.value)}
                      aria-label="Участник для оценки"
                    >
                      <option value="">— выберите —</option>
                      {participants.map((p) => (
                        <option key={p.id} value={p.id}>
                          {p.full_name}
                        </option>
                      ))}
                    </select>
                    <div style={{ marginTop: "0.75rem", display: "grid", gap: "0.5rem" }}>
                      {scoringEngine.criteria.map((key) => (
                        <label key={key} className={styles.muted} htmlFor={`criterion-${key}`}>
                          {scoringEngine.criteria_labels_ru[key] || key}{" "}
                          <input
                            id={`criterion-${key}`}
                            type="number"
                            min={0}
                            max={100}
                            step={0.1}
                            value={criteriaValues[key] ?? ""}
                            onChange={(e) =>
                              setCriteriaValues((prev) => ({ ...prev, [key]: e.target.value }))
                            }
                            className={styles.fieldControl}
                            style={{ width: "6rem", display: "inline-block" }}
                          />
                        </label>
                      ))}
                    </div>
                    <div style={{ marginTop: "0.75rem" }}>
                      <button
                        type="button"
                        className="btn btnPrimary"
                        disabled={scoreBusy}
                        onClick={() => void onSubmitJudgeScore()}
                      >
                        Сохранить оценку
                      </button>
                      {canModerate ? (
                        <button
                          type="button"
                          className="btn btnSecondary"
                          style={{ marginLeft: "0.75rem" }}
                          disabled={scoreBusy}
                          onClick={() => void onAggregateScores()}
                        >
                          Посчитать итог
                        </button>
                      ) : null}
                    </div>
                  </div>
                ) : null}
                <ul className={styles.list}>
                  {judgeScores.length === 0 ? (
                    <li className={styles.item}>
                      <span className={styles.muted}>Оценок судей пока нет.</span>
                    </li>
                  ) : (
                    judgeScores.map((s) => {
                      const athlete = participants.find((x) => x.id === s.participant_id);
                      const mine = user && String(s.judge_user_id) === String(user.id);
                      return (
                      <li key={s.id} className={styles.item}>
                        <div className={styles.itemHead}>
                          <strong>
                            {athlete?.full_name || `Участник ${s.participant_id}`}
                            {" · "}
                            {mine ? "ваша оценка" : "оценка судьи"}
                          </strong>
                          <span className={styles.muted}>итог {s.total}</span>
                        </div>
                        <div className={styles.muted}>
                          попытка {s.attempt_no}
                          {s.heat_id ? ` · заезд ${heats.find((h) => h.id === s.heat_id)?.code || s.heat_id}` : ""}
                        </div>
                      </li>
                      );
                    })
                  )}
                </ul>
              </>
            ) : null}

            {tab === "heats" ? (
              <>
                <h2 className={styles.itemTitle}>Заезды и стартовый список</h2>
                <p className={styles.muted}>
                  День старта: заезд — это не тренировочный слот. Статусы: регистрация → готов → на
                  воде → финиш / не стартовал / не финишировал.
                </p>
                {canModerate ? (
                  <div className={styles.panel}>
                    <input
                      value={heatCode}
                      onChange={(e) => setHeatCode(e.target.value)}
                      placeholder="Код (Q1)"
                      style={{
                        marginRight: "0.5rem",
                        padding: "0.45rem 0.7rem",
                        borderRadius: "8px",
                        border: "1px solid var(--line)",
background: "var(--surface)",
                            color: "var(--ink)",
                      }}
                    />
                    <input
                      value={heatTitle}
                      onChange={(e) => setHeatTitle(e.target.value)}
                      placeholder="Название заезда"
                      style={{
                        marginRight: "0.5rem",
                        padding: "0.45rem 0.7rem",
                        borderRadius: "8px",
                        border: "1px solid var(--line)",
background: "var(--surface)",
                            color: "var(--ink)",
                      }}
                    />
                    <button type="button" className="btn btnPrimary btnSm" onClick={() => void onCreateHeat()}>
                      Создать заезд
                    </button>
                  </div>
                ) : null}
                <ul className={styles.list}>
                  {heats.length === 0 ? (
                    <li className={styles.item}>
                      <span className={styles.muted}>Заезды ещё не созданы.</span>
                    </li>
                  ) : (
                    heats.map((h) => (
                      <li key={h.id} className={styles.item}>
                        <div className={styles.itemHead}>
                          <strong>
                            #{h.heat_number} {h.code} — {h.title}
                          </strong>
                          <button
                            type="button"
                            className="btn btnPrimary btnSm"
                            onClick={() => void onSelectHeat(h.id)}
                          >
                            {selectedHeatId === h.id ? "Открыт" : "Открыть"}
                          </button>
                        </div>
                        <div className={styles.muted}>
                          <StatusBadge status={h.status} kind="heat" />
                          {h.scheduled_at ? ` · ${formatEventDate(h.scheduled_at)}` : ""}
                        </div>
                        {canModerate ? (
                          <div className={styles.actions}>
                            {(() => {
                              const next = nextHeatStatus(h.status);
                              const nextLabel = nextHeatStatusLabel(h.status);
                              return (
                                <>
                                  {next && nextLabel ? (
                                    <button
                                      type="button"
                                      className="btn btnPrimary btnSm"
                                      onClick={() => void onHeatStatus(h, next)}
                                    >
                                      {nextLabel}
                                    </button>
                                  ) : null}
                                  <details className={styles.moreMenu}>
                                    <summary className="btn btnSecondary btnSm" aria-label="Дополнительные статусы заезда">
                                      •••
                                    </summary>
                                    <div className={styles.moreMenuPanel}>
                                      {["planned", "ready", "on_water", "completed"]
                                        .filter((st) => st !== next && st !== h.status)
                                        .map((st) => (
                                          <button
                                            key={st}
                                            type="button"
                                            className="btn btnSecondary btnSm"
                                            onClick={() => void onHeatStatus(h, st)}
                                          >
                                            {st === "planned"
                                              ? labelOf(HEAT_STATUS_LABELS, "planned")
                                              : st === "ready"
                                                ? labelOf(HEAT_STATUS_LABELS, "ready")
                                                : st === "on_water"
                                                  ? labelOf(HEAT_STATUS_LABELS, "on_water")
                                                  : labelOf(HEAT_STATUS_LABELS, "completed")}
                                          </button>
                                        ))}
                                    </div>
                                  </details>
                                </>
                              );
                            })()}
                          </div>
                        ) : null}
                      </li>
                    ))
                  )}
                </ul>

                {selectedHeatId != null ? (
                  <>
                    <h2 className={styles.itemTitle}>Стартовый список</h2>
                    {canModerate ? (
                      <div className={styles.panel}>
                        <select
                          className={styles.fieldControl}
                          value={addParticipantId}
                          onChange={(e) => setAddParticipantId(e.target.value)}
                        >
                          <option value="">Участник…</option>
                          {participants.map((p) => (
                            <option key={p.id} value={p.id}>
                              {p.full_name}
                            </option>
                          ))}
                        </select>
                        <button
                          type="button"
                          className="btn btnPrimary btnSm"
                          onClick={() => void onAddToStartList()}
                        >
                          В список
                        </button>
                        <button
                          type="button"
                          className="btn btnSecondary btnSm"
                          onClick={() => void onFillStartList()}
                        >
                          Добавить всех из состава
                        </button>
                      </div>
                    ) : null}
                    <ul className={styles.list}>
                      {startList.length === 0 ? (
                        <li className={styles.item}>
                          <span className={styles.muted}>Список пуст.</span>
                        </li>
                      ) : (
                        startList.map((e) => {
                          const p = participants.find((x) => x.id === e.participant_id);
                          return (
                            <li key={e.id} className={styles.item}>
                              <div className={styles.itemHead}>
                                <strong>
                                  {e.start_order}. {p?.full_name || `#${e.participant_id}`}
                                  {p?.athlete_id ? ` · ${p.athlete_id}` : ""}
                                  {e.bib_number ? ` · №${e.bib_number}` : ""}
                                </strong>
                                <span className={styles.muted}>
                                  <StatusBadge status={e.status} kind="entry" />
                                </span>
                              </div>
                              {canModerate ? (
                                <div className={styles.actions}>
                                  {(() => {
                                    const next = nextEntryStatus(e.status);
                                    const nextLabel = nextEntryStatusLabel(e.status);
                                    const extras = ["checked_in", "ready", "on_water", "completed", "dns", "dnf"].filter(
                                      (st) => st !== next && st !== e.status,
                                    );
                                    return (
                                      <>
                                        {next && nextLabel ? (
                                          <button
                                            type="button"
                                            className="btn btnPrimary btnSm"
                                            onClick={() => void onEntryStatus(e, next)}
                                          >
                                            {nextLabel}
                                          </button>
                                        ) : null}
                                        <details className={styles.moreMenu}>
                                          <summary
                                            className="btn btnSecondary btnSm"
                                            aria-label="Дополнительные статусы участника"
                                          >
                                            •••
                                          </summary>
                                          <div className={styles.moreMenuPanel}>
                                            {extras.map((st) => (
                                              <button
                                                key={st}
                                                type="button"
                                                className={`btn btnSm ${st === "dns" || st === "dnf" ? "btnDanger" : "btnSecondary"}`}
                                                onClick={() => void onEntryStatus(e, st)}
                                              >
                                                {labelOf(ENTRY_STATUS_LABELS, st)}
                                              </button>
                                            ))}
                                          </div>
                                        </details>
                                      </>
                                    );
                                  })()}
                                </div>
                              ) : null}
                            </li>
                          );
                        })
                      )}
                    </ul>
                  </>
                ) : null}
              </>
            ) : null}

            {tab === "results" ? (
              <>
                <h2 className={styles.itemTitle}>Результаты</h2>
                <p className={styles.muted}>
                  Путь: черновик → проверка организатора → утверждение главного судьи → публикация.
                  Организатор не публикует официальный результат сам.
                </p>
                {canVerifyOfficial ? (
                  <div className={styles.panel}>
                    <select
                      value={resultParticipantId}
                      onChange={(e) => setResultParticipantId(e.target.value)}
                      style={{
                        marginRight: "0.5rem",
                        padding: "0.45rem 0.5rem",
                        borderRadius: "8px",
                        border: "1px solid var(--line)",
background: "var(--surface)",
                            color: "var(--ink)",
                      }}
                    >
                      <option value="">Участник…</option>
                      {participants.map((p) => (
                        <option key={p.id} value={p.id}>
                          {p.full_name}
                        </option>
                      ))}
                    </select>
                    <input
                      value={resultScore}
                      onChange={(e) => setResultScore(e.target.value)}
                      placeholder="Балл"
                      style={{
                        width: "5rem",
                        marginRight: "0.5rem",
                        padding: "0.45rem 0.5rem",
                        borderRadius: "8px",
                        border: "1px solid var(--line)",
background: "var(--surface)",
                            color: "var(--ink)",
                      }}
                    />
                    <input
                      value={resultPlace}
                      onChange={(e) => setResultPlace(e.target.value)}
                      placeholder="Место"
                      style={{
                        width: "5rem",
                        marginRight: "0.5rem",
                        padding: "0.45rem 0.5rem",
                        borderRadius: "8px",
                        border: "1px solid var(--line)",
background: "var(--surface)",
                            color: "var(--ink)",
                      }}
                    />
                    <button
                      type="button"
                      className="btn btnPrimary btnSm"
                      onClick={() => void onSaveResultDraft()}
                    >
                      Сохранить черновик
                    </button>
                  </div>
                ) : null}
                <ul className={styles.list}>
                  {(canVerifyOfficial ? results : publishedResults).length === 0 ? (
                    <li className={styles.item}>
                      <span className={styles.muted}>
                        {canVerifyOfficial ? "Результатов пока нет." : "Опубликованных результатов пока нет."}
                      </span>
                    </li>
                  ) : (
                    (canVerifyOfficial ? results : publishedResults)
                      .slice()
                      .sort((a, b) => (a.place ?? 999) - (b.place ?? 999))
                      .map((r) => {
                      const p = participants.find((x) => x.id === r.participant_id);
                      return (
                        <li key={r.id} className={styles.item}>
                          <div className={styles.itemHead}>
                            <strong>
                              {r.place ? `${r.place} место · ` : ""}
                              {p?.full_name || `Участник ${r.participant_id}`}
                              {r.score != null ? ` · ${r.score}` : ""}
                            </strong>
                            <StatusBadge status={r.status} kind="result" />
                          </div>
                          {canVerifyOfficial ? (
                            <div className={styles.actions}>
                              {r.status === "draft" ? (
                                <button
                                  type="button"
                                  className="btn btnPrimary btnSm"
                                  onClick={() => void onResultStatus(r, "verified")}
                                >
                                  Проверить
                                </button>
                              ) : null}
                              {canPublishOfficial && r.status === "verified" ? (
                                <button
                                  type="button"
                                  className="btn btnPrimary btnSm"
                                  onClick={() => void onResultStatus(r, "published")}
                                >
                                  Утвердить и опубликовать
                                </button>
                              ) : null}
                              {!canPublishOfficial && r.status === "verified" ? (
                                <span className={styles.muted}>Ждёт главного судью</span>
                              ) : null}
                              {r.status !== "void" && (r.status !== "published" || canPublishOfficial) ? (
                                <button
                                  type="button"
                                  className="btn btnDanger btnSm"
                                  onClick={() => {
                                    if (window.confirm("Аннулировать результат?")) {
                                      void onResultStatus(r, "void");
                                    }
                                  }}
                                >
                                  Аннулировать
                                </button>
                              ) : null}
                            </div>
                          ) : null}
                        </li>
                      );
                    })
                  )}
                </ul>
              </>
            ) : null}

            {tab === "participants" ? (
              <>
                <h2 className={styles.itemTitle}>Участники ({filtered.length})</h2>
                <p className={styles.muted}>
                  Медсправка: {medicalStats.withMed} из {medicalStats.total} (без ссылок в публичном
                  списке).
                </p>
                <label className={styles.muted}>
                  Поиск{" "}
                  <input
                    value={filter}
                    onChange={(e) => setFilter(e.target.value)}
                    placeholder="ФИО или регион"
                    style={{
                      marginLeft: "0.5rem",
                      padding: "0.45rem 0.7rem",
                      borderRadius: "8px",
                      border: "1px solid var(--line)",
background: "var(--surface)",
                            color: "var(--ink)",
                    }}
                  />
                </label>
                <ul className={styles.list}>
                  {filtered.map((p) => {
                    const cat = p.category_id ? catById.get(p.category_id) : null;
                    return (
                      <li key={p.id} className={styles.item}>
                        <div className={styles.itemHead}>
                          <strong>{p.full_name}</strong>
                          <span className={p.has_medical_cert ? styles.medOk : styles.medMiss}>
                            {p.has_medical_cert ? "Справка есть" : "Справки нет"}
                          </span>
                        </div>
                        <div className={styles.muted}>
                          {[
                            p.athlete_id,
                            cat?.discipline,
                            cat?.title,
                            p.region,
                            p.gender,
                            p.birth_year,
                          ]
                            .filter(Boolean)
                            .join(" · ")}
                        </div>
                      </li>
                    );
                  })}
                </ul>
              </>
            ) : null}
          </>
        ) : !error ? (
          <p className={styles.muted}>Загрузка события…</p>
        ) : null}
      </main>
    </>
  );
}
