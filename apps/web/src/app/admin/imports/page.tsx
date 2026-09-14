"use client";

import { useCallback, useEffect, useState } from "react";
import { AppHeader } from "@/components/AppHeader";
import { AuthNeeded } from "@/components/AuthNeeded";
import {
  ApiError,
  commitImportBatch,
  ingestEventPack,
  applyKazanScanProtocol,
  decideImportRow,
  getImportBatch,
  getStoredToken,
  getStoredUser,
  listEvents,
  listImportBatches,
  uploadImportBatch,
  type EventOut,
  type ImportBatchOut,
  type ImportRowOut,
} from "@/lib/api";
import { isStaffRole } from "@/lib/roles";
import loginStyles from "../../login/login.module.css";
import styles from "./imports.module.css";

const KIND_LABEL: Record<string, string> = {
  new: "новый",
  exact: "точное",
  probable: "вероятное",
  conflict: "конфликт",
  excluded: "исключено",
};

function kindClass(kind: string): string {
  if (kind === "new") return `${styles.kind} ${styles.kindNew}`;
  if (kind === "exact") return `${styles.kind} ${styles.kindExact}`;
  if (kind === "probable") return `${styles.kind} ${styles.kindProbable}`;
  return `${styles.kind} ${styles.kindConflict}`;
}

export default function ImportCenterPage() {
  const [gate, setGate] = useState<"ok" | "auth" | "forbidden">("ok");
  const [events, setEvents] = useState<EventOut[]>([]);
  const [eventId, setEventId] = useState<string>("");
  const [batches, setBatches] = useState<ImportBatchOut[]>([]);
  const [batch, setBatch] = useState<ImportBatchOut | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  const token = () => getStoredToken();

  const loadEvents = useCallback(async () => {
    const t = token();
    const user = getStoredUser();
    if (!t || !user) {
      setGate("auth");
      return;
    }
    if (!isStaffRole(user.role)) {
      setGate("forbidden");
      return;
    }
    setGate("ok");
    try {
      const list = await listEvents(t);
      setEvents(list);
      if (!eventId && list.length) setEventId(String(list[0].id));
    } catch (err) {
      if (err instanceof ApiError && (err.status === 401 || err.code === "token_expired")) {
        setGate("auth");
        return;
      }
      setError(err instanceof ApiError ? err.message : "Не удалось загрузить события");
    }
  }, [eventId]);

  const loadBatches = useCallback(async (id: string) => {
    const t = token();
    if (!t || !id) return;
    const items = await listImportBatches(t, id);
    setBatches(items);
    if (items[0]) {
      const full = await getImportBatch(t, id, items[0].id);
      setBatch(full);
    } else {
      setBatch(null);
    }
  }, []);

  useEffect(() => {
    void loadEvents();
  }, [loadEvents]);

  useEffect(() => {
    if (eventId && gate === "ok") {
      void loadBatches(eventId).catch((err) => {
        setError(err instanceof ApiError ? err.message : "Не удалось загрузить импорты");
      });
    }
  }, [eventId, gate, loadBatches]);

  async function onUpload(file: File | undefined) {
    const t = token();
    if (!t || !eventId || !file) return;
    setPending(true);
    setError(null);
    setMessage(null);
    try {
      const uploaded = await uploadImportBatch(t, eventId, file);
      setMessage(`Файл разобран: ${uploaded.row_count} строк. Повтор той же таблицы не создаёт дубликат.`);
      await loadBatches(eventId);
      const full = await getImportBatch(t, eventId, uploaded.id);
      setBatch(full);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Не удалось загрузить файл");
    } finally {
      setPending(false);
    }
  }

  async function onIngestPack(list: FileList | null) {
    const t = token();
    const files = list ? Array.from(list) : [];
    if (!t || !eventId || files.length === 0) return;
    setPending(true);
    setError(null);
    setMessage(null);
    try {
      const result = await ingestEventPack(t, eventId, files);
      setMessage(
        `Пакет загружен в это событие: судей ${result.officials}, стартовых записей ${result.start_entries}, файлов ${result.files.length}.`,
      );
      await loadBatches(eventId);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Не удалось загрузить пакет");
    } finally {
      setPending(false);
    }
  }

  async function onScanProtocol() {
    const t = token();
    if (!t || !eventId) return;
    setPending(true);
    setError(null);
    setMessage(null);
    try {
      const result = await applyKazanScanProtocol(t, eventId);
      setMessage(
        `Сканы Казани разложены: заездов ${result.heats}, стартов ${result.entries}, черновиков результатов ${result.results} (DNS ${result.dns}). Не опубликовано — на листах Not homologated.`,
      );
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Не удалось разложить сканы");
    } finally {
      setPending(false);
    }
  }

  async function onDecide(row: ImportRowOut, decision: "approve" | "reject") {
    const t = token();
    if (!t || !eventId || !batch) return;
    setPending(true);
    setError(null);
    try {
      await decideImportRow(t, eventId, batch.id, row.id, decision);
      const full = await getImportBatch(t, eventId, batch.id);
      setBatch(full);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Не удалось сохранить решение");
    } finally {
      setPending(false);
    }
  }

  async function onCommit() {
    const t = token();
    if (!t || !eventId || !batch) return;
    setPending(true);
    setError(null);
    try {
      const result = await commitImportBatch(t, eventId, batch.id);
      setMessage(`Зафиксировано участий: ${result.committed_count}. Созданы Athlete ID и pending-аккаунты.`);
      const full = await getImportBatch(t, eventId, result.id);
      setBatch(full);
      await loadBatches(eventId);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Не удалось зафиксировать импорт");
    } finally {
      setPending(false);
    }
  }

  return (
    <>
      <AppHeader subtitle="Центр импорта" />
      <main id="main" className={`${loginStyles.main} ${styles.wrap}`}>
        <h1 className={loginStyles.title}>Импорт заявок</h1>
        {gate === "auth" ? (
          <AuthNeeded next="/admin/imports" title="Нужен вход" actionLabel="Войти">
            Импорт доступен организатору после входа.
          </AuthNeeded>
        ) : null}
        {gate === "forbidden" ? (
          <p className={loginStyles.error} role="alert">
            Этот раздел только для организатора и администратора события.
          </p>
        ) : null}
        {gate === "ok" ? (
          <>
            <p className={loginStyles.hint}>
              Загружайте xlsx и PDF в выбранную карточку события (для Казани — одно событие ЧР+ПР).
              Категории приводятся к IWWF: U14, U18, O30, O40, Open (чемпионат). Возраст — на 31.12.2026.
              Сначала пакет заявок, затем кнопка сканов дня старта. Результаты со сканов остаются черновиками
              (на листах Not homologated). Персональные данные и фото протоколов не попадают в GitHub.
            </p>
            <div className={loginStyles.field}>
              <label htmlFor="event">Событие</label>
              <select
                id="event"
                value={eventId}
                onChange={(e) => setEventId(e.target.value)}
                disabled={pending}
              >
                {events.map((event) => (
                  <option key={event.id} value={event.id}>
                    {event.title}
                  </option>
                ))}
              </select>
            </div>
            <div className={`${loginStyles.field} ${styles.fileRow}`}>
              <label htmlFor="xlsx">Таблица заявок (.xlsx)</label>
              <input
                id="xlsx"
                type="file"
                accept=".xlsx"
                disabled={pending || !eventId}
                onChange={(e) => void onUpload(e.target.files?.[0])}
              />
            </div>
            <div className={`${loginStyles.field} ${styles.fileRow}`}>
              <label htmlFor="pack">Пакет документов (xlsx + PDF start list + протокол КС)</label>
              <input
                id="pack"
                type="file"
                multiple
                accept=".xlsx,.pdf,.xls,.docx"
                disabled={pending || !eventId}
                onChange={(e) => void onIngestPack(e.target.files)}
              />
            </div>
            <div className={styles.actions}>
              <button
                type="button"
                className={loginStyles.submit}
                disabled={pending || !eventId}
                onClick={() => void onScanProtocol()}
              >
                Разложить сканы Казани
              </button>
            </div>
            {error ? (
              <p className={loginStyles.error} role="alert">
                {error}
              </p>
            ) : null}
            {message ? (
              <p className={loginStyles.hint} role="status">
                {message}
              </p>
            ) : null}
            {batch ? (
              <>
                <div className={styles.stats} aria-label="Сводка пакета">
                  <div className={styles.stat}>
                    <b>{batch.row_count}</b> строк
                  </div>
                  <div className={styles.stat}>
                    <b>{batch.new_count}</b> новых
                  </div>
                  <div className={styles.stat}>
                    <b>{batch.exact_count}</b> точных
                  </div>
                  <div className={styles.stat}>
                    <b>{batch.probable_count}</b> вероятных
                  </div>
                  <div className={styles.stat}>
                    <b>{batch.conflict_count}</b> конфликтов
                  </div>
                  <div className={styles.stat}>
                    <b>{batch.committed_count}</b> в roster
                  </div>
                </div>
                <p className={loginStyles.hint}>
                  Файл: {batch.source_filename}. Статус: {batch.status}. Новые и точные совпадения
                  отмечены к импорту автоматически; конфликты нужно разобрать вручную.
                </p>
                <div className={styles.actions}>
                  <button
                    type="button"
                    className={loginStyles.submit}
                    disabled={pending || batch.status === "committed"}
                    onClick={() => void onCommit()}
                  >
                    {batch.status === "committed" ? "Уже зафиксирован" : "Зафиксировать одобренные"}
                  </button>
                </div>
                <div className={styles.tableWrap}>
                  <table className={styles.table}>
                    <thead>
                      <tr>
                        <th>ФИО</th>
                        <th>Дисциплина</th>
                        <th>Категория</th>
                        <th>Совпадение</th>
                        <th>Решение</th>
                      </tr>
                    </thead>
                    <tbody>
                      {(batch.rows || []).map((row) => (
                        <tr key={row.id}>
                          <td>
                            {row.display_name || "—"}
                            <div className={loginStyles.hint}>
                              {row.phone_masked || "нет телефона"}
                              {row.has_medical ? "" : " · нет медсправки"}
                            </div>
                          </td>
                          <td>{row.discipline || "—"}</td>
                          <td>{row.category_label || "—"}</td>
                          <td>
                            <span className={kindClass(row.match_kind)}>
                              {KIND_LABEL[row.match_kind] || row.match_kind}
                            </span>
                            {row.conflict_codes.length ? (
                              <div className={loginStyles.hint}>{row.conflict_codes.join(", ")}</div>
                            ) : null}
                          </td>
                          <td>
                            <div className={styles.rowBtns}>
                              <button
                                type="button"
                                className={loginStyles.submit}
                                disabled={pending || batch.status === "committed"}
                                onClick={() => void onDecide(row, "approve")}
                              >
                                {row.admin_decision === "approve" ? "Одобрено" : "Одобрить"}
                              </button>
                              <button
                                type="button"
                                className={loginStyles.submit}
                                disabled={pending || batch.status === "committed"}
                                onClick={() => void onDecide(row, "reject")}
                              >
                                {row.admin_decision === "reject" ? "Отклонено" : "Отклонить"}
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                {batches.length > 1 ? (
                  <p className={loginStyles.hint}>Пакетов по событию: {batches.length}.</p>
                ) : null}
              </>
            ) : (
              <p className={loginStyles.hint}>Пока нет пакетов. Выберите событие и загрузите таблицу.</p>
            )}
          </>
        ) : null}
      </main>
    </>
  );
}
