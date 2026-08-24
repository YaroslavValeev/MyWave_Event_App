"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { AppHeader } from "@/components/AppHeader";
import { StatusBadge } from "@/components/StatusBadge";
import { ApiError, EventOut, getStoredToken, listEvents } from "@/lib/api";
import styles from "./events.module.css";

type LoadState =
  | { kind: "loading" }
  | { kind: "unauth" }
  | { kind: "error"; message: string }
  | { kind: "empty" }
  | { kind: "ok"; events: EventOut[] };

function formatDate(value: string | null): string {
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

export default function EventsPage() {
  const [state, setState] = useState<LoadState>({ kind: "loading" });

  useEffect(() => {
    let cancelled = false;

    async function load() {
      const token = getStoredToken();
      if (!token) {
        if (!cancelled) setState({ kind: "unauth" });
        return;
      }

      try {
        const events = await listEvents(token);
        if (cancelled) return;
        const list = Array.isArray(events) ? events : [];
        if (list.length === 0) {
          setState({ kind: "empty" });
        } else {
          setState({ kind: "ok", events: list });
        }
      } catch (err) {
        if (cancelled) return;
        const message =
          err instanceof ApiError ? err.message : "Не удалось загрузить события.";
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
      <AppHeader subtitle="Список событий" />
      <main id="main" className={styles.main}>
        <h1 className={styles.title}>События</h1>
        <p className={styles.muted}>
          <Link href="/events/new">+ Создать событие</Link>
        </p>

        {state.kind === "loading" ? (
          <p className={styles.muted} aria-live="polite">
            Загрузка…
          </p>
        ) : null}

        {state.kind === "unauth" ? (
          <div className={styles.panel} role="status">
            <p>Чтобы увидеть события, выполните вход.</p>
            <Link href="/login" className={styles.linkBtn}>
              Перейти ко входу
            </Link>
          </div>
        ) : null}

        {state.kind === "error" ? (
          <div className={styles.panel} role="alert">
            <p className={styles.error}>{state.message}</p>
            <p className={styles.muted}>
              Убедитесь, что API запущен и{" "}
              <code>NEXT_PUBLIC_API_BASE_URL</code> задан верно.
            </p>
          </div>
        ) : null}

        {state.kind === "empty" ? (
          <div className={styles.panel} role="status">
            <p>Пока нет событий. <Link href="/events/new">Создать черновик</Link></p>
          </div>
        ) : null}

        {state.kind === "ok" ? (
          <ul className={styles.list}>
            {state.events.map((event) => (
              <li key={event.id} className={styles.item}>
                <div className={styles.itemHead}>
                  <h2 className={styles.itemTitle}>
                    <Link href={`/events/${event.id}`}>{event.title}</Link>
                  </h2>
                  <StatusBadge status={event.status} />
                </div>
                {event.description ? (
                  <p className={styles.itemDesc}>{event.description}</p>
                ) : null}
                <dl className={styles.meta}>
                  <div>
                    <dt>Город</dt>
                    <dd>{event.city || "—"}</dd>
                  </div>
                  <div>
                    <dt>Период</dt>
                    <dd>
                      {formatDate(event.starts_at)} — {formatDate(event.ends_at)}
                    </dd>
                  </div>
                  <div>
                    <dt>Дисциплины</dt>
                    <dd>{event.disciplines || "—"}</dd>
                  </div>
                </dl>
              </li>
            ))}
          </ul>
        ) : null}
      </main>
    </>
  );
}
