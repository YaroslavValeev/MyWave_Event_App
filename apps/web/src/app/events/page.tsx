"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { AppHeader } from "@/components/AppHeader";
import { EventCard } from "@/components/EventCard";
import { ApiError, EventOut, getStoredToken, getStoredUser, listEvents } from "@/lib/api";
import { partitionEvents } from "@/lib/eventsSort";
import { isStaffRole } from "@/lib/roles";
import styles from "./events.module.css";

type LoadState =
  | { kind: "loading" }
  | { kind: "error"; message: string }
  | { kind: "empty" }
  | { kind: "ok"; events: EventOut[] };

function Section({
  title,
  events,
  emptyHint,
}: {
  title: string;
  events: EventOut[];
  emptyHint?: string;
}) {
  if (events.length === 0 && !emptyHint) return null;
  return (
    <section className={styles.section} aria-labelledby={`sec-${title}`}>
      <h2 id={`sec-${title}`} className={styles.sectionTitle}>
        {title}
      </h2>
      {events.length === 0 ? (
        <p className={styles.muted}>{emptyHint}</p>
      ) : (
        <ul className={styles.list}>
          {events.map((event) => (
            <EventCard key={event.id} event={event} />
          ))}
        </ul>
      )}
    </section>
  );
}

export default function EventsPage() {
  const [state, setState] = useState<LoadState>({ kind: "loading" });
  const [canCreate, setCanCreate] = useState(false);
  const [signedIn, setSignedIn] = useState(false);

  useEffect(() => {
    let cancelled = false;
    const user = getStoredUser();
    setSignedIn(Boolean(user));
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
          err instanceof ApiError ? err.message : "Не удалось загрузить соревнования.";
        setState({ kind: "error", message });
      }
    }

    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  const buckets = state.kind === "ok" ? partitionEvents(state.events) : null;

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
            <button
              type="button"
              className="btn btnSecondary btnSm"
              onClick={() => {
                setState({ kind: "loading" });
                void listEvents(getStoredToken())
                  .catch(() => listEvents())
                  .then((events) => {
                    const list = Array.isArray(events) ? events : [];
                    setState(list.length === 0 ? { kind: "empty" } : { kind: "ok", events: list });
                  })
                  .catch((err) =>
                    setState({
                      kind: "error",
                      message:
                        err instanceof ApiError
                          ? err.message
                          : "Не удалось загрузить соревнования.",
                    }),
                  );
              }}
            >
              Повторить
            </button>
          </div>
        ) : null}

        {state.kind === "empty" ? (
          <div className={styles.panel} role="status">
            <p>
              Пока нет открытых соревнований.
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

        {buckets ? (
          <>
            <Section title="Идёт сейчас" events={buckets.live} />
            <Section title="Ближайшие" events={buckets.upcoming} />
            {signedIn ? (
              <Section
                title="Мои соревнования"
                events={buckets.other}
                emptyHint={
                  buckets.other.length === 0
                    ? "Черновики и закрытые события появятся здесь для организатора и участников с ролью."
                    : undefined
                }
              />
            ) : null}
            <Section title="Архив" events={buckets.archive} />
          </>
        ) : null}
      </main>
    </>
  );
}
