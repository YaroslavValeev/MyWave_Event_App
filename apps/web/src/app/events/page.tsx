"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { AppHeader } from "@/components/AppHeader";
import { EventCard } from "@/components/EventCard";
import { ApiError, EventOut, getStoredToken, getStoredUser, listEvents } from "@/lib/api";
import { isStaffRole } from "@/lib/roles";
import styles from "./events.module.css";

type LoadState =
  | { kind: "loading" }
  | { kind: "error"; message: string }
  | { kind: "empty" }
  | { kind: "ok"; events: EventOut[] };

export default function EventsPage() {
  const [state, setState] = useState<LoadState>({ kind: "loading" });
  const [canCreate, setCanCreate] = useState(false);

  useEffect(() => {
    let cancelled = false;
    const user = getStoredUser();
    setCanCreate(Boolean(user && isStaffRole(user.role)));

    async function load() {
      try {
        const events = await listEvents(getStoredToken()).catch(() => listEvents());
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
      <AppHeader subtitle="Соревнования" />
      <main id="main" className={styles.main}>
        <div className={styles.itemHead}>
          <h1 className={styles.title}>События</h1>
          {canCreate ? (
            <Link href="/events/new" className="btn btnPrimary btnSm">
              Создать соревнование
            </Link>
          ) : null}
        </div>

        {state.kind === "loading" ? (
          <p className={styles.muted} aria-live="polite">
            Загрузка…
          </p>
        ) : null}

        {state.kind === "error" ? (
          <div className={styles.panel} role="alert">
            <p className={styles.error}>{state.message}</p>
            <p className={styles.muted}>Если страница пустая — проверьте, что API запущен.</p>
          </div>
        ) : null}

        {state.kind === "empty" ? (
          <div className={styles.panel} role="status">
            <p>
              Пока нет открытых событий.
              {canCreate ? (
                <>
                  {" "}
                  <Link href="/events/new">Создать черновик</Link>
                </>
              ) : (
                " Организатор опубликует старт здесь."
              )}
            </p>
          </div>
        ) : null}

        {state.kind === "ok" ? (
          <ul className={styles.list}>
            {state.events.map((event) => (
              <EventCard key={event.id} event={event} />
            ))}
          </ul>
        ) : null}
      </main>
    </>
  );
}
