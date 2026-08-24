"use client";

import { useEffect, useState } from "react";
import { AppHeader } from "@/components/AppHeader";
import { ApiError, getApiBaseUrl, getHealth, type HealthResponse } from "@/lib/api";
import styles from "./health.module.css";

type State =
  | { kind: "loading" }
  | { kind: "error"; message: string }
  | { kind: "ok"; data: HealthResponse };

export default function HealthPage() {
  const [state, setState] = useState<State>({ kind: "loading" });

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const data = await getHealth();
        if (!cancelled) setState({ kind: "ok", data });
      } catch (err) {
        if (cancelled) return;
        const message =
          err instanceof ApiError
            ? err.message
            : "API недоступен. Проверьте, что backend запущен.";
        setState({ kind: "error", message });
      }
    }

    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <>
      <AppHeader subtitle="Проверка API" />
      <main id="main" className={styles.main}>
        <h1 className={styles.title}>Статус системы</h1>
        <p className={styles.base}>
          Базовый URL: <code>{getApiBaseUrl()}</code>
        </p>

        {state.kind === "loading" ? (
          <p className={styles.muted} aria-live="polite">
            Запрос к <code>/health</code>…
          </p>
        ) : null}

        {state.kind === "error" ? (
          <div className={styles.panel} role="alert">
            <p className={styles.badgeError}>Недоступно</p>
            <p>{state.message}</p>
          </div>
        ) : null}

        {state.kind === "ok" ? (
          <div className={styles.panel} role="status">
            <p
              className={
                state.data.status === "ok" && state.data.db_ok
                  ? styles.badgeOk
                  : styles.badgeWarn
              }
            >
              {state.data.status === "ok" && state.data.db_ok ? "Работает" : "Частично"}
            </p>
            <dl className={styles.grid}>
              <div>
                <dt>Статус</dt>
                <dd>{state.data.status}</dd>
              </div>
              <div>
                <dt>Приложение</dt>
                <dd>{state.data.app}</dd>
              </div>
              <div>
                <dt>Окружение</dt>
                <dd>{state.data.env}</dd>
              </div>
              <div>
                <dt>БД</dt>
                <dd>{state.data.db_ok ? "ok" : "ошибка"}</dd>
              </div>
              <div>
                <dt>Время сервера</dt>
                <dd>{state.data.time}</dd>
              </div>
            </dl>
          </div>
        ) : null}
      </main>
    </>
  );
}
