"use client";

import { useCallback, useEffect, useId, useMemo, useRef, useState, type KeyboardEvent as ReactKeyboardEvent } from "react";
import { ApiError } from "@/lib/api";
import {
  APP_DOWNLOAD_ANALYTICS,
  formatFileSize,
  getAppDownloadManifest,
  getAppDownloadStatus,
  startAppDownloadHandoff,
  trackAppDownloadEvent,
  type AppDownloadArtifact,
  type AppDownloadManifest,
} from "@/lib/appDownloads";
import { DOWNLOAD_STATE_LABELS, labelOf } from "@/lib/labels";
import styles from "./AppDownloadCard.module.css";

type AppDownloadCardProps = {
  context?: string;
};

type UiState = "loading" | "available" | "unavailable" | "error" | "success";

const FOCUSABLE = "button:not([disabled]), a[href], [tabindex]:not([tabindex='-1'])";

function asUiState(value: string | undefined): UiState {
  if (value === "available" || value === "unavailable" || value === "error" || value === "success") {
    return value;
  }
  return "loading";
}

export function AppDownloadCard({ context = "projects/checklist-org" }: AppDownloadCardProps) {
  const reactId = useId();
  const rootRef = useRef<HTMLElement | null>(null);
  const dialogRef = useRef<HTMLDivElement | null>(null);
  const previousFocus = useRef<HTMLElement | null>(null);
  const viewedRef = useRef(false);
  const [manifest, setManifest] = useState<AppDownloadManifest | null>(null);
  const [selectedId, setSelectedId] = useState<string>("android");
  const [artifact, setArtifact] = useState<AppDownloadArtifact | null>(null);
  const [uiState, setUiState] = useState<UiState>("loading");
  const [message, setMessage] = useState("Загружаем варианты…");
  const [announce, setAnnounce] = useState("");
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [confirmBusy, setConfirmBusy] = useState(false);
  const [catalogError, setCatalogError] = useState(false);

  const artifacts = useMemo(() => manifest?.artifacts ?? [], [manifest]);
  const statusRequestRef = useRef(0);

  const speak = useCallback((text: string) => {
    setAnnounce("");
    window.setTimeout(() => setAnnounce(text), 20);
  }, []);

  const applyArtifact = useCallback((item: AppDownloadArtifact, nextState?: UiState, nextMessage?: string) => {
    setArtifact(item);
    setUiState(nextState ?? asUiState(item.state));
    setMessage(nextMessage ?? item.message);
  }, []);

  const loadManifest = useCallback(async () => {
    setCatalogError(false);
    setUiState("loading");
    setMessage("Загружаем варианты…");
    try {
      const next = await getAppDownloadManifest();
      setManifest(next);
      const first = next.artifacts[0];
      if (first) {
        setSelectedId(first.id);
        applyArtifact(first);
      }
    } catch {
      setCatalogError(true);
      setUiState("error");
      setMessage("Не удалось загрузить каталог файлов.");
      speak("Ошибка загрузки каталога. Нажмите «Повторить проверку».");
      trackAppDownloadEvent(APP_DOWNLOAD_ANALYTICS.failed, { stage: "manifest" }, context);
    }
  }, [applyArtifact, context, speak]);

  const refreshStatus = useCallback(
    async (artifactId: string) => {
      const requestId = ++statusRequestRef.current;
      setUiState("loading");
      setMessage("Проверяем доступность…");
      try {
        const next = await getAppDownloadStatus(artifactId);
        if (requestId !== statusRequestRef.current) return;
        applyArtifact(next);
        setManifest((current) => {
          if (!current) return current;
          return {
            ...current,
            artifacts: current.artifacts.map((item) => (item.id === next.id ? next : item)),
          };
        });
      } catch {
        if (requestId !== statusRequestRef.current) return;
        setUiState("error");
        setMessage("Ошибка проверки доступности.");
        speak("Ошибка проверки файла. Доступна повторная попытка.");
        trackAppDownloadEvent(
          APP_DOWNLOAD_ANALYTICS.failed,
          { artifact_id: artifactId, stage: "status" },
          context,
        );
      }
    },
    [applyArtifact, context, speak],
  );

  useEffect(() => {
    void loadManifest();
  }, [loadManifest]);

  useEffect(() => {
    const node = rootRef.current;
    if (!node || viewedRef.current) return;
    if (typeof IntersectionObserver === "undefined") {
      viewedRef.current = true;
      trackAppDownloadEvent(APP_DOWNLOAD_ANALYTICS.viewed, {}, context);
      return;
    }
    const observer = new IntersectionObserver(
      (entries) => {
        if (!viewedRef.current && entries.some((entry) => entry.isIntersecting)) {
          viewedRef.current = true;
          trackAppDownloadEvent(APP_DOWNLOAD_ANALYTICS.viewed, {}, context);
          observer.disconnect();
        }
      },
      { threshold: 0.35 },
    );
    observer.observe(node);
    return () => observer.disconnect();
  }, [context]);

  useEffect(() => {
    if (!confirmOpen) return;
    const dialog = dialogRef.current;
    const focusable = dialog?.querySelectorAll<HTMLElement>(FOCUSABLE);
    focusable?.[0]?.focus();
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    function onKeyDown(event: globalThis.KeyboardEvent) {
      if (event.key === "Escape") {
        event.preventDefault();
        setConfirmOpen(false);
        return;
      }
      if (event.key !== "Tab" || !dialog) return;
      const items = Array.from(dialog.querySelectorAll<HTMLElement>(FOCUSABLE)).filter(
        (item) => !item.hasAttribute("hidden"),
      );
      if (!items.length) return;
      const first = items[0];
      const last = items[items.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    }

    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("keydown", onKeyDown);
      document.body.style.overflow = previousOverflow;
    };
  }, [confirmOpen]);

  useEffect(() => {
    if (!confirmOpen && previousFocus.current) {
      previousFocus.current.focus();
      previousFocus.current = null;
    }
  }, [confirmOpen]);

  function selectArtifact(id: string, track: boolean) {
    const next = artifacts.find((item) => item.id === id);
    if (!next) return;
    setSelectedId(id);
    applyArtifact(next);
    if (track) {
      trackAppDownloadEvent(APP_DOWNLOAD_ANALYTICS.selected, { artifact_id: id }, context);
    }
    void refreshStatus(id);
  }

  function onTabKeyDown(event: ReactKeyboardEvent<HTMLButtonElement>, index: number) {
    if (!artifacts.length) return;
    let nextIndex: number | null = null;
    if (event.key === "ArrowRight" || event.key === "ArrowDown") {
      nextIndex = (index + 1) % artifacts.length;
    } else if (event.key === "ArrowLeft" || event.key === "ArrowUp") {
      nextIndex = (index - 1 + artifacts.length) % artifacts.length;
    } else if (event.key === "Home") {
      nextIndex = 0;
    } else if (event.key === "End") {
      nextIndex = artifacts.length - 1;
    }
    if (nextIndex == null) return;
    event.preventDefault();
    const next = artifacts[nextIndex];
    const button = event.currentTarget.parentElement?.querySelectorAll<HTMLButtonElement>("[role='tab']")[
      nextIndex
    ];
    button?.focus();
    selectArtifact(next.id, true);
  }

  function openConfirm() {
    if (!artifact || artifact.state !== "available") return;
    previousFocus.current = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    trackAppDownloadEvent(
      APP_DOWNLOAD_ANALYTICS.clicked,
      { artifact_id: artifact.id, version: artifact.version },
      context,
    );
    setConfirmBusy(false);
    setConfirmOpen(true);
  }

  async function confirmDownload() {
    if (!artifact) return;
    setConfirmBusy(true);
    try {
      const handoff = await startAppDownloadHandoff(artifact.id);
      trackAppDownloadEvent(
        APP_DOWNLOAD_ANALYTICS.succeeded,
        { artifact_id: artifact.id, version: artifact.version },
        context,
      );
      setConfirmOpen(false);
      setUiState("success");
      setMessage(handoff.message || "Скачивание успешно запущено.");
      speak("Скачивание успешно запущено.");
      window.setTimeout(() => {
        const link = document.createElement("a");
        link.href = handoff.location;
        link.rel = "noopener noreferrer";
        if (handoff.open_in_new_tab) {
          link.target = "_blank";
        } else {
          link.setAttribute("download", "");
        }
        document.body.appendChild(link);
        link.click();
        link.remove();
      }, 250);
    } catch (err) {
      setConfirmOpen(false);
      setUiState("error");
      setMessage("Ошибка скачивания. Повторите попытку.");
      speak("Не удалось начать скачивание. Попробуйте ещё раз.");
      const reason = err instanceof ApiError ? err.code || err.message : "unknown";
      trackAppDownloadEvent(
        APP_DOWNLOAD_ANALYTICS.failed,
        { artifact_id: artifact.id, stage: "handoff", reason: String(reason).slice(0, 80) },
        context,
      );
    } finally {
      setConfirmBusy(false);
    }
  }

  const canDownload =
    Boolean(artifact) &&
    artifact?.state === "available" &&
    (uiState === "available" || uiState === "success" || uiState === "error");
  const showRetry = uiState === "error" || catalogError;
  const downloadLabel = catalogError
    ? "Каталог недоступен"
    : uiState === "loading"
      ? "Проверяем файл…"
      : uiState === "available" || uiState === "success"
        ? artifact?.action_label || "Скачать"
        : uiState === "error"
          ? "Повторить скачивание"
          : "Файл временно недоступен";

  return (
    <article
      ref={rootRef}
      id="mywave-event-app"
      className={styles.card}
      aria-labelledby={`${reactId}-title`}
    >
      <header className={styles.hero}>
        <div>
          <p className={styles.eyebrow}>Готовое решение</p>
          <div className={styles.titleRow}>
            <span className={styles.mark} aria-hidden="true">
              MW
            </span>
            <div>
              <h2 id={`${reactId}-title`} className={styles.title}>
                {manifest?.app.name ?? "MyWave Event App"}
              </h2>
              <p className={styles.lead}>
                {manifest?.app.short_description ??
                  "Цифровая платформа соревнований MyWave в одном приложении."}
              </p>
            </div>
          </div>
        </div>
        <p className={styles.readiness} data-app-status="">
          <span
            className={`${styles.dot} ${manifest?.app.available_count ? styles.dotReady : ""}`}
            aria-hidden="true"
          />
          <span>{manifest?.app.readiness ?? "Проверяем готовность…"}</span>
        </p>
      </header>

      <div className={styles.overview}>
        <section aria-labelledby={`${reactId}-features`}>
          <h3 id={`${reactId}-features`} className={styles.featuresTitle}>
            Основные возможности
          </h3>
          <ul className={styles.features}>
            {(manifest?.app.features ?? ["Загружаем описание…"]).map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </section>
        <section aria-labelledby={`${reactId}-meta`}>
          <h3 id={`${reactId}-meta`} className={styles.metaTitle}>
            Сведения о выпуске
          </h3>
          <dl className={styles.meta}>
            <div>
              <dt>Статус готовности</dt>
              <dd>{manifest?.app.readiness ?? "Проверяем…"}</dd>
            </div>
            <div>
              <dt>Версия</dt>
              <dd>{manifest?.app.version ?? "Не опубликована"}</dd>
            </div>
            <div>
              <dt>Платформы</dt>
              <dd>{manifest?.app.platforms.join(", ") ?? "Веб-приложение"}</dd>
            </div>
            <div>
              <dt>Дата обновления</dt>
              <dd>{manifest?.app.last_updated ?? "Не указана"}</dd>
            </div>
          </dl>
        </section>
      </div>

      <section className={styles.download} aria-labelledby={`${reactId}-download`}>
        <h3 id={`${reactId}-download`} className={styles.panelTitle}>
          Скачать готовое решение
        </h3>
        <p className={styles.note}>
          Выберите платформу или формат. Перед скачиванием покажем версию и системные требования.
          Нативные файлы появляются здесь только после подключения реальных ссылок.
        </p>
        <div className={styles.tabs} role="tablist" aria-label="Формат скачивания">
          {artifacts.map((item, index) => {
            const selected = item.id === selectedId;
            return (
              <button
                key={item.id}
                id={`${reactId}-tab-${item.id}`}
                type="button"
                role="tab"
                className={styles.tab}
                aria-selected={selected}
                aria-controls={`${reactId}-panel`}
                tabIndex={selected ? 0 : -1}
                onClick={() => selectArtifact(item.id, true)}
                onKeyDown={(event) => onTabKeyDown(event, index)}
              >
                {item.label}
              </button>
            );
          })}
        </div>
        <div
          id={`${reactId}-panel`}
          className={styles.panel}
          role="tabpanel"
          aria-labelledby={`${reactId}-tab-${selectedId}`}
        >
          <dl className={styles.meta}>
            <div>
              <dt>Формат</dt>
              <dd>{artifact?.format ?? "—"}</dd>
            </div>
            <div>
              <dt>Версия файла</dt>
              <dd>{artifact?.version ?? "Не опубликована"}</dd>
            </div>
            <div>
              <dt>Размер</dt>
              <dd>{formatFileSize(artifact?.size)}</dd>
            </div>
            <div>
              <dt>Обновлён</dt>
              <dd>{artifact?.last_updated ?? "Не указана"}</dd>
            </div>
          </dl>
          <div className={styles.fileState} data-state={uiState} role="status">
            <span>
              <strong>{labelOf(DOWNLOAD_STATE_LABELS, uiState)}. </strong>
              {message}
            </span>
          </div>
          <div className={styles.actions}>
            <button
              type="button"
              className="btn btnPrimary"
              disabled={!canDownload || catalogError}
              onClick={openConfirm}
              aria-describedby={`${reactId}-help`}
            >
              {downloadLabel}
            </button>
            {showRetry ? (
              <button
                type="button"
                className="btn btnSecondary"
                onClick={() => (catalogError ? void loadManifest() : void refreshStatus(selectedId))}
              >
                Повторить проверку
              </button>
            ) : null}
          </div>
          <p id={`${reactId}-help`} className={styles.note}>
            Ссылки на файлы не показываются заранее. Скачивание начинается только после подтверждения.
          </p>
        </div>
      </section>

      <div className={styles.live} aria-live="polite">
        {announce}
      </div>

      {confirmOpen && artifact ? (
        <div
          className={styles.overlay}
          onMouseDown={(event) => {
            if (event.target === event.currentTarget) setConfirmOpen(false);
          }}
        >
          <div
            ref={dialogRef}
            className={styles.dialog}
            role="dialog"
            aria-modal="true"
            aria-labelledby={`${reactId}-dialog-title`}
            aria-describedby={`${reactId}-dialog-desc`}
          >
            <div className={styles.dialogHead}>
              <h3 id={`${reactId}-dialog-title`} className={styles.dialogTitle}>
                Скачать {artifact.label}
              </h3>
              <button
                type="button"
                className={`btn btnGhost ${styles.close}`}
                onClick={() => setConfirmOpen(false)}
                aria-label="Закрыть окно подтверждения"
              >
                Закрыть
              </button>
            </div>
            <p id={`${reactId}-dialog-desc`}>
              Вы выбрали {artifact.platform}, версия {artifact.version}. После подтверждения начнётся
              скачивание или откроется страница установки.
            </p>
            <dl className={styles.meta}>
              <div>
                <dt>Версия</dt>
                <dd>{artifact.version}</dd>
              </div>
              <div>
                <dt>Формат</dt>
                <dd>{artifact.format}</dd>
              </div>
              <div>
                <dt>Размер</dt>
                <dd>{formatFileSize(artifact.size)}</dd>
              </div>
            </dl>
            <h4 className={styles.featuresTitle}>Системные требования</h4>
            <ul className={styles.requirements}>
              {artifact.requirements.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
            <div className={styles.actions}>
              <button
                type="button"
                className="btn btnPrimary"
                disabled={confirmBusy}
                onClick={() => void confirmDownload()}
              >
                {confirmBusy ? "Запускаем…" : "Начать скачивание"}
              </button>
              <button type="button" className="btn btnSecondary" onClick={() => setConfirmOpen(false)}>
                Отмена
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </article>
  );
}
