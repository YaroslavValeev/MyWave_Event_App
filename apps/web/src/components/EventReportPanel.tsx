"use client";

import { useCallback, useEffect, useState } from "react";
import {
  ApiError,
  EventReportOut,
  RoleActionOut,
  assembleEventReport,
  eventReportExcelUrl,
  getEventReport,
  getStoredToken,
  listRoleActions,
  publishEventReport,
  updateEventReport,
  voidEventReport,
} from "@/lib/api";
import styles from "@/app/events/events.module.css";

type Props = {
  eventId: string;
  eventSlug: string;
  canEdit: boolean;
  canPublish: boolean;
  isArchived: boolean;
  onError: (message: string | null) => void;
};

export function EventReportPanel({
  eventId,
  eventSlug,
  canEdit,
  canPublish,
  isArchived,
  onError,
}: Props) {
  const [report, setReport] = useState<EventReportOut | null>(null);
  const [body, setBody] = useState("");
  const [title, setTitle] = useState("");
  const [actions, setActions] = useState<RoleActionOut[]>([]);
  const [busy, setBusy] = useState(false);
  const [loaded, setLoaded] = useState(false);

  const refresh = useCallback(async () => {
    const token = getStoredToken();
    if (!token || !canEdit) return;
    try {
      const [rep, roleActs] = await Promise.all([
        getEventReport(token, eventId).catch((err: unknown) => {
          if (err instanceof ApiError && err.status === 404) return null;
          throw err;
        }),
        listRoleActions(token, eventId),
      ]);
      setReport(rep);
      setBody(rep?.body_markdown ?? "");
      setTitle(rep?.title ?? "");
      setActions(roleActs);
      onError(null);
    } catch (err) {
      onError(err instanceof ApiError ? err.message : "Не удалось загрузить отчёт");
    } finally {
      setLoaded(true);
    }
  }, [canEdit, eventId, onError]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  async function onAssemble(useLlm: boolean) {
    const token = getStoredToken();
    if (!token || !canEdit || isArchived) return;
    setBusy(true);
    onError(null);
    try {
      const rep = await assembleEventReport(token, eventId, { use_llm: useLlm });
      setReport(rep);
      setBody(rep.body_markdown);
      setTitle(rep.title);
    } catch (err) {
      onError(err instanceof ApiError ? err.message : "Сборка отчёта не удалась");
    } finally {
      setBusy(false);
    }
  }

  async function onSave() {
    const token = getStoredToken();
    if (!token || !canEdit || isArchived || !report) return;
    setBusy(true);
    onError(null);
    try {
      const rep = await updateEventReport(token, eventId, {
        title,
        body_markdown: body,
      });
      setReport(rep);
      setBody(rep.body_markdown);
      setTitle(rep.title);
    } catch (err) {
      onError(err instanceof ApiError ? err.message : "Не удалось сохранить отчёт");
    } finally {
      setBusy(false);
    }
  }

  async function onPublish() {
    const token = getStoredToken();
    if (!token || !canPublish || isArchived) return;
    setBusy(true);
    onError(null);
    try {
      const rep = await publishEventReport(token, eventId);
      setReport(rep);
    } catch (err) {
      onError(err instanceof ApiError ? err.message : "Публикация не удалась");
    } finally {
      setBusy(false);
    }
  }

  async function onVoid() {
    const token = getStoredToken();
    if (!token || !canPublish || isArchived) return;
    setBusy(true);
    onError(null);
    try {
      const rep = await voidEventReport(token, eventId);
      setReport(rep);
    } catch (err) {
      onError(err instanceof ApiError ? err.message : "Void не удался");
    } finally {
      setBusy(false);
    }
  }

  async function onExcel() {
    const token = getStoredToken();
    if (!token || !canEdit) return;
    setBusy(true);
    onError(null);
    try {
      const res = await fetch(eventReportExcelUrl(eventId), {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) {
        throw new ApiError("Не удалось скачать Excel", res.status);
      }
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${eventSlug || `event-${eventId}`}-event-report.xlsx`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      onError(err instanceof ApiError ? err.message : "Excel недоступен");
    } finally {
      setBusy(false);
    }
  }

  const aiProvider =
    report && typeof report.facts?.ai === "object" && report.facts.ai
      ? String((report.facts.ai as { provider?: string }).provider || "—")
      : "—";

  if (!canEdit) {
    return (
      <p className={styles.muted}>
        Отчёт события доступен организатору / комментатору. Гости видят только опубликованные
        результаты.
      </p>
    );
  }

  return (
    <>
      <h2 className={styles.itemTitle}>Отчёт о событии</h2>
      <p className={styles.muted}>
        AI собирает черновик из результатов, DNS/DNF и handoff ролей. Excel — выгрузка, не Source of
        Truth. Publish только человеком.
      </p>

      <div className={styles.panel}>
        <p className={styles.muted}>
          Статус: <strong>{report?.status || (loaded ? "нет" : "…")}</strong>
          {report ? (
            <>
              {" · "}
              источник: <strong>{report.source}</strong>
              {" · "}
              AI: <strong>{aiProvider}</strong>
            </>
          ) : null}
        </p>
        <button
          type="button"
          className="btn btnPrimary btnSm"
          disabled={busy || isArchived || report?.status === "published"}
          onClick={() => void onAssemble(true)}
        >
          Собрать AI-черновик
        </button>{" "}
        <button
          type="button"
          className="btn btnSecondary btnSm"
          disabled={busy || isArchived || report?.status === "published"}
          onClick={() => void onAssemble(false)}
        >
          Шаблон без AI
        </button>{" "}
        <button
          type="button"
          className="btn btnSecondary btnSm"
          disabled={busy || !report}
          onClick={() => void onExcel()}
        >
          Excel
        </button>
        {canPublish ? (
          <>
            {" "}
            <button
              type="button"
              className="btn btnPrimary btnSm"
              disabled={busy || isArchived || !report || report.status === "published"}
              onClick={() => void onPublish()}
            >
              Опубликовать
            </button>{" "}
            <button
              type="button"
              className="btn btnSecondary btnSm"
              disabled={busy || isArchived || !report || report.status === "void"}
              onClick={() => void onVoid()}
            >
              Void
            </button>
          </>
        ) : null}
      </div>

      {report ? (
        <div className={styles.panel}>
          <label className={styles.muted}>
            Заголовок
            <input
              value={title}
              disabled={busy || isArchived || report.status === "published"}
              onChange={(e) => setTitle(e.target.value)}
              style={{
                display: "block",
                width: "100%",
                marginTop: "0.35rem",
                marginBottom: "0.75rem",
                padding: "0.55rem 0.7rem",
                borderRadius: "8px",
                border: "1px solid var(--line)",
                background: "rgba(0,0,0,0.25)",
                color: "inherit",
              }}
            />
          </label>
          <label className={styles.muted}>
            Текст (Markdown)
            <textarea
              value={body}
              disabled={busy || isArchived || report.status === "published"}
              onChange={(e) => setBody(e.target.value)}
              rows={16}
              style={{
                display: "block",
                width: "100%",
                marginTop: "0.35rem",
                padding: "0.7rem",
                borderRadius: "8px",
                border: "1px solid var(--line)",
                background: "rgba(0,0,0,0.25)",
                color: "inherit",
                fontFamily: "ui-monospace, monospace",
                fontSize: "0.9rem",
              }}
            />
          </label>
          {report.status !== "published" ? (
            <p style={{ marginTop: "0.75rem" }}>
              <button
                type="button"
                className="btn btnPrimary btnSm"
                disabled={busy || isArchived}
                onClick={() => void onSave()}
              >
                Сохранить правки
              </button>
            </p>
          ) : null}
        </div>
      ) : (
        <p className={styles.muted}>Черновика ещё нет — нажмите «Собрать AI-черновик».</p>
      )}

      <h3 className={styles.itemTitle}>Физика площадки → роли</h3>
      <p className={styles.muted}>Кто что делает руками и кому передаёт в App.</p>
      <ul className={styles.list}>
        {actions.length === 0 ? (
          <li className={styles.item}>
            <span className={styles.muted}>Матрица пуста.</span>
          </li>
        ) : (
          actions.map((a) => (
            <li key={a.code} className={styles.item}>
              <div className={styles.itemHead}>
                <strong>
                  {a.phase} · {a.role} → {a.handoff_to}
                </strong>
              </div>
              <div className={styles.muted}>
                {a.physical_ru}
                <br />
                App: {a.app_action}
              </div>
            </li>
          ))
        )}
      </ul>
    </>
  );
}
