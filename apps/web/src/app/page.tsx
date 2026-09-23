"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { AppHeader } from "@/components/AppHeader";
import { EventCard } from "@/components/EventCard";
import { getLastEventId, postLoginPath } from "@/lib/format";
import { pickNearestEvent } from "@/lib/eventsSort";
import { getStoredUser, listEvents, type EventOut } from "@/lib/api";
import styles from "./home.module.css";

export default function HomePage() {
  const [signedIn, setSignedIn] = useState(false);
  const [events, setEvents] = useState<EventOut[]>([]);
  const [continueHref, setContinueHref] = useState("/events");

  useEffect(() => {
    setSignedIn(Boolean(getStoredUser()));
    setContinueHref(getLastEventId() ? postLoginPath() : "/events");
    void listEvents()
      .then((items) => setEvents(Array.isArray(items) ? items : []))
      .catch(() => setEvents([]));
  }, []);

  const featured = pickNearestEvent(events);

  return (
    <>
      <AppHeader />
      <main id="main" className={styles.hero}>
        <p className={styles.brand}>MyWave Event</p>
        <h1 className={styles.headline}>Заявка, старт и протокол — в одном месте</h1>
        <p className={styles.lead}>
          Всё соревнование в одном приложении: регистрация, расписание, стартовые списки, судейство
          и результаты в реальном времени.
        </p>
        <div className={styles.ctaGroup}>
          {signedIn ? (
            <>
              <Link href={continueHref} className={styles.ctaPrimary}>
                Продолжить
              </Link>
              <Link href="/events" className={styles.ctaSecondary}>
                Найти соревнование
              </Link>
            </>
          ) : (
            <>
              <Link href="/events" className={styles.ctaPrimary}>
                Найти соревнование
              </Link>
              <Link href="/login" className={styles.ctaSecondary}>
                Войти
              </Link>
              <Link href="/register" className={styles.ctaText}>
                Создать аккаунт
              </Link>
            </>
          )}
        </div>

        {featured ? (
          <section className={styles.featured} aria-labelledby="featured-title">
            <h2 id="featured-title" className={styles.featuredTitle}>
              {featured.status === "live" ? "Идёт сейчас" : "Ближайшее соревнование"}
            </h2>
            <ul className={styles.featuredList}>
              <EventCard event={featured} cta={signedIn ? "Открыть" : "Смотреть"} />
            </ul>
          </section>
        ) : null}
      </main>
    </>
  );
}
