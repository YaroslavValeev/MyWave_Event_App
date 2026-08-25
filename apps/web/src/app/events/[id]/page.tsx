"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";
import { AppHeader } from "@/components/AppHeader";
import { StatusBadge } from "@/components/StatusBadge";
import {
  ApiError,
  ApplicationOut,
  CategoryOut,
  ChecklistItemOut,
  DocumentOut,
  EventDetail,
  EventRulesProfileOut,
  HeatOut,
  OfficialOut,
  ParticipantOut,
  ProtocolCaptureOut,
  ResultOut,
  ScheduleHint,
  StartListEntryOut,
  TrainingSlotOut,
  addStartListEntry,
  createHeat,
  decideEventApplication,
  deleteDocument,
  documentDownloadUrl,
  fillStartList,
  getEventDetail,
  getEventRulesProfile,
  getMyApplication,
  getScheduleHint,
  getStoredToken,
  getStoredUser,
  listCategories,
  listChecklist,
  listDocuments,
  listEventApplications,
  listHeats,
  listOfficials,
  listParticipants,
  listProtocolCaptures,
  listResults,
  listStartList,
  listTrainingSlots,
  protocolCaptureFileUrl,
  submitApplication,
  updateChecklistItem,
  updateHeatStatus,
  updateProtocolCapture,
  updateResultStatus,
  updateStartListStatus,
  uploadDocument,
  uploadProtocolCapture,
  upsertResultDraft,
} from "@/lib/api";
import styles from "../events.module.css";

type TabId =
  | "overview"
  | "checklist"
  | "participants"
  | "slots"
  | "docs"
  | "protocol"
  | "heats"
  | "results"
  | "apps";

function formatDate(value: string | null | undefined): string {
  if (!value) return "—";
  try {
    return new Intl.DateTimeFormat("ru-RU", {
      dateStyle: "medium",
      timeStyle: "short",
    }).format(new Date(value));
  } catch {
    return value;
  }
}

export default function EventDetailPage() {
  const params = useParams<{ id: string }>();
  const eventId = params.id;
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
  const [protocolTitle, setProtocolTitle] = useState("");
  const [protocolKind, setProtocolKind] = useState("judge_sheet");
  const [protocolBusy, setProtocolBusy] = useState(false);
  const [results, setResults] = useState<ResultOut[]>([]);
  const [resultParticipantId, setResultParticipantId] = useState("");
  const [resultScore, setResultScore] = useState("");
  const [resultPlace, setResultPlace] = useState("");
  const [officials, setOfficials] = useState<OfficialOut[]>([]);
  const [training, setTraining] = useState<TrainingSlotOut[]>([]);
  const [hint, setHint] = useState<ScheduleHint | null>(null);
  const [onlyBooked, setOnlyBooked] = useState(true);
  const [filter, setFilter] = useState("");
  const [slotsLoading, setSlotsLoading] = useState(false);
  const [myApp, setMyApp] = useState<ApplicationOut | null>(null);
  const [pendingApps, setPendingApps] = useState<ApplicationOut[]>([]);
  const [categoryId, setCategoryId] = useState<string>("");
  const [region, setRegion] = useState("");
  const [club, setClub] = useState("");
  const [appMessage, setAppMessage] = useState<string | null>(null);
  const [appBusy, setAppBusy] = useState(false);
  const [tab, setTab] = useState<TabId>("overview");
  const user = getStoredUser();
  const canModerate =
    user?.role === "organizer" ||
    user?.role === "event_admin" ||
    user?.role === "platform_admin" ||
    user?.role === "federation_manager";
  const canUploadProtocol =
    canModerate || user?.role === "judge";

  useEffect(() => {
    let cancelled = false;
    async function load() {
      const token = getStoredToken();
      if (!token) {
        setError("Нужен вход.");
        return;
      }
      try {
        const [d, cats, parts, docs, offs, schedule, mine, checks, heatItems, resultItems, profile, protoItems] =
          await Promise.all([
          getEventDetail(token, eventId),
          listCategories(token, eventId),
          listParticipants(token, eventId),
          listDocuments(token, eventId),
          listOfficials(token, eventId),
          getScheduleHint(token, eventId),
          getMyApplication(token, eventId).catch(() => null),
          listChecklist(token, eventId).catch(() => ({ items: [], total: 0, done_count: 0 })),
          listHeats(token, eventId).catch(() => []),
          listResults(token, eventId).catch(() => []),
          getEventRulesProfile(token, eventId).catch(() => null),
          listProtocolCaptures(token, eventId).catch(() => []),
        ]);
        if (cancelled) return;
        setDetail(d);
        setCategories(cats);
        setParticipants(parts);
        setDocuments(docs);
        setOfficials(offs);
        setHint(schedule);
        setMyApp(mine);
        setChecklist(checks.items);
        setChecklistDone(checks.done_count);
        setHeats(heatItems);
        setResults(resultItems);
        setRulesProfile(profile);
        setProtocols(protoItems);
        if (heatItems.length > 0) setSelectedHeatId(heatItems[0].id);
        const stored = getStoredUser();
        if (
          stored &&
          ["organizer", "event_admin", "platform_admin", "federation_manager"].includes(
            stored.role,
          )
        ) {
          try {
            setPendingApps(await listEventApplications(token, eventId, "pending"));
          } catch {
            setPendingApps([]);
          }
        }
      } catch (err) {
        if (cancelled) return;
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
    if (!token || !canModerate) return;
    try {
      await updateProtocolCapture(token, eventId, item.id, { status });
      setProtocols(await listProtocolCaptures(token, eventId));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Не удалось обновить статус протокола");
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
      setError(err instanceof ApiError ? err.message : "Не удалось создать heat");
    }
  }

  async function loadStartList(heatId: number) {
    const token = getStoredToken();
    if (!token) return;
    try {
      setStartList(await listStartList(token, eventId, heatId));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Не удалось загрузить start list");
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
      setError(err instanceof ApiError ? err.message : "Не удалось заполнить start list");
    }
  }

  async function onSaveResultDraft() {
    const token = getStoredToken();
    if (!token || !canModerate) return;
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
      setError(err instanceof ApiError ? err.message : "Не удалось сохранить draft result");
    }
  }

  async function onResultStatus(row: ResultOut, status: "verified" | "published" | "void" | "draft") {
    const token = getStoredToken();
    if (!token || !canModerate) return;
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

  const tabs: { id: TabId; label: string; show?: boolean }[] = [
    { id: "overview", label: "Обзор" },
    { id: "checklist", label: `Чеклист (${checklistDone}/${checklist.length || 7})` },
    { id: "participants", label: `Участники (${participants.length})` },
    { id: "slots", label: "Слоты" },
    { id: "docs", label: `Документы (${documents.length})` },
    { id: "protocol", label: `Протокол (${protocols.length})` },
    { id: "heats", label: `Heats (${heats.length})` },
    { id: "results", label: `Results (${results.length})` },
    {
      id: "apps",
      label: canModerate ? `Заявки (${pendingApps.length})` : "Моя заявка",
      show: true,
    },
  ];

  return (
    <>
      <AppHeader subtitle="Карточка события" />
      <main id="main" className={styles.main}>
        <p className={styles.muted}>
          <Link href="/events">← К списку событий</Link>
        </p>

        {error ? (
          <div className={styles.panel} role="alert">
            <p className={styles.error}>{error}</p>
            <Link href="/login" className={styles.linkBtn}>
              Войти
            </Link>
          </div>
        ) : null}

        {detail ? (
          <>
            <div className={styles.itemHead}>
              <h1 className={styles.title}>{detail.title}</h1>
              <StatusBadge status={detail.status} />
            </div>
            {detail.description ? <p className={styles.itemDesc}>{detail.description}</p> : null}
            <dl className={styles.meta}>
              <div>
                <dt>Город</dt>
                <dd>{detail.city || "—"}</dd>
              </div>
              <div>
                <dt>Период</dt>
                <dd>
                  {formatDate(detail.starts_at)} — {formatDate(detail.ends_at)}
                </dd>
              </div>
              <div>
                <dt>Дисциплины</dt>
                <dd>{detail.disciplines || "—"}</dd>
              </div>
              {rulesProfile ? (
                <div>
                  <dt>Правила / протокол</dt>
                  <dd>
                    {rulesProfile.governing_body} · санкция {rulesProfile.sanction_body} ·{" "}
                    {rulesProfile.scoring_mode}
                  </dd>
                </div>
              ) : null}
              <div>
                <dt>Сводка</dt>
                <dd>
                  {detail.categories_count} кат. · {detail.participants_count} уч. ·{" "}
                  {detail.documents_count} док. · {detail.officials_count ?? 0} судей ·{" "}
                  {detail.training_slots_count ?? 0} слотов
                </dd>
              </div>
              <div>
                <dt>Медсправки</dt>
                <dd>
                  {medicalStats.withMed} / {medicalStats.total}
                </dd>
              </div>
            </dl>

            <div className={styles.tabs} role="tablist" aria-label="Разделы события">
              {tabs
                .filter((t) => t.show !== false)
                .map((t) => (
                  <button
                    key={t.id}
                    type="button"
                    role="tab"
                    aria-selected={tab === t.id}
                    className={`${styles.tab} ${tab === t.id ? styles.tabActive : ""}`}
                    onClick={() => setTab(t.id)}
                  >
                    {t.label}
                  </button>
                ))}
            </div>

            {tab === "overview" ? (
              <>
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
                      Статус: <strong>{myApp.status}</strong> · {myApp.full_name}
                    </p>
                    <p className={styles.muted}>
                      {[myApp.region, myApp.club].filter(Boolean).join(" · ") || "—"}
                    </p>
                  </div>
                ) : detail.status === "registration_open" ? (
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
                        <option value="">Без категории</option>
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
                        className={styles.linkBtn}
                        disabled={appBusy}
                        onClick={() => void onSubmitApplication()}
                      >
                        {appBusy ? "Отправка…" : "Подать заявку"}
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
                          <span className={styles.muted}>Нет pending-заявок.</span>
                        </li>
                      ) : (
                        pendingApps.map((a) => (
                          <li key={a.id} className={styles.item}>
                            <div className={styles.itemHead}>
                              <strong>{a.full_name}</strong>
                              <span>
                                <button
                                  type="button"
                                  className={styles.linkBtn}
                                  disabled={appBusy}
                                  onClick={() => void onDecideApp(a.id, "accepted")}
                                >
                                  Принять
                                </button>{" "}
                                <button
                                  type="button"
                                  className={styles.linkBtn}
                                  disabled={appBusy}
                                  onClick={() => void onDecideApp(a.id, "rejected")}
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
                            className={styles.linkBtn}
                            onClick={() => void onToggleChecklist(item)}
                          >
                            {item.is_done ? "Снять" : "Отметить"}
                          </button>
                        ) : null}
                      </div>
                      <div className={styles.muted}>{item.code}</div>
                    </li>
                  ))}
                </ul>
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
                          background: "rgba(0,0,0,0.25)",
                          color: "inherit",
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
                          background: "rgba(0,0,0,0.25)",
                          color: "inherit",
                        }}
                      >
                        <option value="bulletin">bulletin</option>
                        <option value="protocol">protocol</option>
                        <option value="schedule">schedule</option>
                        <option value="rules">rules</option>
                        <option value="start_list">start_list</option>
                        <option value="other">other</option>
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
                              className={styles.linkBtn}
                              onClick={() => void downloadDoc(d)}
                            >
                              Скачать
                            </button>
                            {canModerate ? (
                              <button
                                type="button"
                                className={styles.linkBtn}
                                onClick={() => void onDeleteDoc(d)}
                                style={{ marginLeft: "0.5rem" }}
                              >
                                Удалить
                              </button>
                            ) : null}
                          </span>
                        </div>
                        <div className={styles.muted}>
                          {d.kind} · {d.language || "—"} · {d.file_name}
                        </div>
                      </li>
                    ))
                  )}
                </ul>
              </>
            ) : null}

            {tab === "protocol" ? (
              <>
                <h2 className={styles.itemTitle}>Фото / PDF протокола</h2>
                <p className={styles.muted}>
                  Листы судей WSWS (DRIVE) или бумажный протокол. Загрузка: JPG/PNG/WebP/PDF до 15 МБ.
                </p>
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
                          background: "rgba(0,0,0,0.25)",
                          color: "inherit",
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
                          background: "rgba(0,0,0,0.25)",
                          color: "inherit",
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
                            <span className={styles.muted}>({p.status})</span>
                          </strong>
                          <span>
                            <button
                              type="button"
                              className={styles.linkBtn}
                              onClick={() => void downloadProtocol(p)}
                            >
                              Открыть
                            </button>
                            {canModerate && p.status === "draft" ? (
                              <button
                                type="button"
                                className={styles.linkBtn}
                                style={{ marginLeft: "0.5rem" }}
                                onClick={() => void onVerifyProtocol(p, "verified")}
                              >
                                Проверить
                              </button>
                            ) : null}
                            {canModerate && p.status === "verified" ? (
                              <button
                                type="button"
                                className={styles.linkBtn}
                                style={{ marginLeft: "0.5rem" }}
                                onClick={() => void onVerifyProtocol(p, "published")}
                              >
                                Опубликовать
                              </button>
                            ) : null}
                          </span>
                        </div>
                        <div className={styles.muted}>
                          {p.kind} · {p.file_name}
                          {p.heat_id ? ` · heat #${p.heat_id}` : ""}
                          {p.notes ? ` · ${p.notes}` : ""}
                        </div>
                      </li>
                    ))
                  )}
                </ul>
              </>
            ) : null}

            {tab === "heats" ? (
              <>
                <h2 className={styles.itemTitle}>Heats / Start lists</h2>
                <p className={styles.muted}>
                  День старта: heat ≠ тренировочный слот. Статусы участника: check-in → ready →
                  on-water → completed / DNS / DNF.
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
                        background: "rgba(0,0,0,0.25)",
                        color: "inherit",
                      }}
                    />
                    <input
                      value={heatTitle}
                      onChange={(e) => setHeatTitle(e.target.value)}
                      placeholder="Название heat"
                      style={{
                        marginRight: "0.5rem",
                        padding: "0.45rem 0.7rem",
                        borderRadius: "8px",
                        border: "1px solid var(--line)",
                        background: "rgba(0,0,0,0.25)",
                        color: "inherit",
                      }}
                    />
                    <button type="button" className={styles.linkBtn} onClick={() => void onCreateHeat()}>
                      Создать heat
                    </button>
                  </div>
                ) : null}
                <ul className={styles.list}>
                  {heats.length === 0 ? (
                    <li className={styles.item}>
                      <span className={styles.muted}>Heats ещё не созданы.</span>
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
                            className={styles.linkBtn}
                            onClick={() => void onSelectHeat(h.id)}
                          >
                            {selectedHeatId === h.id ? "Открыт" : "Открыть"}
                          </button>
                        </div>
                        <div className={styles.muted}>status: {h.status}</div>
                        {canModerate ? (
                          <div style={{ marginTop: "0.5rem", display: "flex", flexWrap: "wrap", gap: "0.35rem" }}>
                            {["planned", "ready", "on_water", "completed"].map((st) => (
                              <button
                                key={st}
                                type="button"
                                className={styles.linkBtn}
                                onClick={() => void onHeatStatus(h, st)}
                              >
                                {st}
                              </button>
                            ))}
                          </div>
                        ) : null}
                      </li>
                    ))
                  )}
                </ul>

                {selectedHeatId != null ? (
                  <>
                    <h2 className={styles.itemTitle}>Start list</h2>
                    {canModerate ? (
                      <div className={styles.panel}>
                        <select
                          value={addParticipantId}
                          onChange={(e) => setAddParticipantId(e.target.value)}
                          style={{
                            marginRight: "0.5rem",
                            padding: "0.45rem 0.5rem",
                            borderRadius: "8px",
                            border: "1px solid var(--line)",
                            background: "rgba(0,0,0,0.25)",
                            color: "inherit",
                          }}
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
                          className={styles.linkBtn}
                          onClick={() => void onAddToStartList()}
                        >
                          В start list
                        </button>
                        <button
                          type="button"
                          className={styles.linkBtn}
                          style={{ marginLeft: "0.5rem" }}
                          onClick={() => void onFillStartList()}
                        >
                          Заполнить из roster
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
                                  {e.bib_number ? ` · №${e.bib_number}` : ""}
                                </strong>
                                <span className={styles.muted}>{e.status}</span>
                              </div>
                              {canModerate ? (
                                <div style={{ display: "flex", flexWrap: "wrap", gap: "0.35rem" }}>
                                  {["checked_in", "ready", "on_water", "completed", "dns", "dnf"].map(
                                    (st) => (
                                      <button
                                        key={st}
                                        type="button"
                                        className={styles.linkBtn}
                                        onClick={() => void onEntryStatus(e, st)}
                                      >
                                        {st}
                                      </button>
                                    ),
                                  )}
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
                <h2 className={styles.itemTitle}>Results</h2>
                <p className={styles.muted}>
                  Контур draft → verified → published (+ history/audit). Полный judge scoring —
                  следующий шаг.
                </p>
                {canModerate ? (
                  <div className={styles.panel}>
                    <select
                      value={resultParticipantId}
                      onChange={(e) => setResultParticipantId(e.target.value)}
                      style={{
                        marginRight: "0.5rem",
                        padding: "0.45rem 0.5rem",
                        borderRadius: "8px",
                        border: "1px solid var(--line)",
                        background: "rgba(0,0,0,0.25)",
                        color: "inherit",
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
                      placeholder="Score"
                      style={{
                        width: "5rem",
                        marginRight: "0.5rem",
                        padding: "0.45rem 0.5rem",
                        borderRadius: "8px",
                        border: "1px solid var(--line)",
                        background: "rgba(0,0,0,0.25)",
                        color: "inherit",
                      }}
                    />
                    <input
                      value={resultPlace}
                      onChange={(e) => setResultPlace(e.target.value)}
                      placeholder="Place"
                      style={{
                        width: "5rem",
                        marginRight: "0.5rem",
                        padding: "0.45rem 0.5rem",
                        borderRadius: "8px",
                        border: "1px solid var(--line)",
                        background: "rgba(0,0,0,0.25)",
                        color: "inherit",
                      }}
                    />
                    <button
                      type="button"
                      className={styles.linkBtn}
                      onClick={() => void onSaveResultDraft()}
                    >
                      Save draft
                    </button>
                  </div>
                ) : null}
                <ul className={styles.list}>
                  {results.length === 0 ? (
                    <li className={styles.item}>
                      <span className={styles.muted}>Результатов пока нет.</span>
                    </li>
                  ) : (
                    results.map((r) => {
                      const p = participants.find((x) => x.id === r.participant_id);
                      return (
                        <li key={r.id} className={styles.item}>
                          <div className={styles.itemHead}>
                            <strong>
                              {p?.full_name || `#${r.participant_id}`} · {r.score ?? "—"} pts · place{" "}
                              {r.place ?? "—"}
                            </strong>
                            <span className={styles.muted}>{r.status}</span>
                          </div>
                          {canModerate ? (
                            <div style={{ display: "flex", flexWrap: "wrap", gap: "0.35rem" }}>
                              {r.status === "draft" ? (
                                <button
                                  type="button"
                                  className={styles.linkBtn}
                                  onClick={() => void onResultStatus(r, "verified")}
                                >
                                  Verify
                                </button>
                              ) : null}
                              {r.status === "verified" ? (
                                <button
                                  type="button"
                                  className={styles.linkBtn}
                                  onClick={() => void onResultStatus(r, "published")}
                                >
                                  Publish
                                </button>
                              ) : null}
                              {r.status !== "void" ? (
                                <button
                                  type="button"
                                  className={styles.linkBtn}
                                  onClick={() => void onResultStatus(r, "void")}
                                >
                                  Void
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
                      background: "rgba(0,0,0,0.25)",
                      color: "inherit",
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
                            {p.has_medical_cert ? "мед ✓" : "мед —"}
                          </span>
                        </div>
                        <div className={styles.muted}>
                          {[cat?.discipline, cat?.title, p.region, p.gender, p.birth_year]
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
