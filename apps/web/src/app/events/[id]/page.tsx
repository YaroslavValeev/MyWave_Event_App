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
  DocumentOut,
  EventDetail,
  OfficialOut,
  ParticipantOut,
  ScheduleHint,
  TrainingSlotOut,
  decideEventApplication,
  documentDownloadUrl,
  getEventDetail,
  getMyApplication,
  getScheduleHint,
  getStoredToken,
  getStoredUser,
  listCategories,
  listDocuments,
  listEventApplications,
  listOfficials,
  listParticipants,
  listTrainingSlots,
  submitApplication,
} from "@/lib/api";
import styles from "../events.module.css";

type TabId = "overview" | "participants" | "slots" | "docs" | "apps";

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

  useEffect(() => {
    let cancelled = false;
    async function load() {
      const token = getStoredToken();
      if (!token) {
        setError("Нужен вход.");
        return;
      }
      try {
        const [d, cats, parts, docs, offs, schedule, mine] = await Promise.all([
          getEventDetail(token, eventId),
          listCategories(token, eventId),
          listParticipants(token, eventId),
          listDocuments(token, eventId),
          listOfficials(token, eventId),
          getScheduleHint(token, eventId),
          getMyApplication(token, eventId).catch(() => null),
        ]);
        if (cancelled) return;
        setDetail(d);
        setCategories(cats);
        setParticipants(parts);
        setDocuments(docs);
        setOfficials(offs);
        setHint(schedule);
        setMyApp(mine);
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

  const tabs: { id: TabId; label: string; show?: boolean }[] = [
    { id: "overview", label: "Обзор" },
    { id: "participants", label: `Участники (${participants.length})` },
    { id: "slots", label: "Слоты" },
    { id: "docs", label: `Документы (${documents.length})` },
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

            {tab === "docs" ? (
              <>
                <h2 className={styles.itemTitle}>Документы</h2>
                <ul className={styles.list}>
                  {documents.map((d) => (
                    <li key={d.id} className={styles.item}>
                      <div className={styles.itemHead}>
                        <strong>{d.title}</strong>
                        <button
                          type="button"
                          className={styles.linkBtn}
                          onClick={() => void downloadDoc(d)}
                        >
                          Скачать
                        </button>
                      </div>
                      <div className={styles.muted}>
                        {d.kind} · {d.language || "—"} · {d.file_name}
                      </div>
                    </li>
                  ))}
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
