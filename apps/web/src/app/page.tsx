"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { AppHeader } from "@/components/AppHeader";
import { EventCard } from "@/components/EventCard";
import { getLastEventId, postLoginPath } from "@/lib/format";
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
      .then((items) => setEvents(items.slice(0, 2)))
      .catch(() => setEvents([]));
  }, []);

  const featured = events[0];

  return (
    <>
      <AppHeader />
      <main id="main" className={styles.hero}>
        <p className={styles.brand}>MyWave Event</p>
        <h1 className={styles.headline}>Заявка, старт и протокол — в одном месте</h1>
        <p className={styles.lead}>
          Цифровая сцена соревнования для участников, судей и организаторов. Без привязки к
          сайту MyWave.
        </p>
        <div className={styles.ctaGroup}>
          {signedIn ? (
            <Link href={continueHref} className={styles.ctaPrimary}>
              Продолжить
            </Link>
          ) : (
            <>
              <Link href="/login" className={styles.ctaPrimary}>
                Войти
              </Link>
              <Link href="/register" className={styles.ctaSecondary}>
                Создать аккаунт
              </Link>
            </>
          )}
          <Link href="/events" className={styles.ctaSecondary}>
            Смотреть события
          </Link>
        </div>

        {featured ? (
          <section className={styles.featured} aria-labelledby="featured-title">
            <h2 id="featured-title" className={styles.featuredTitle}>
              Ближайшее событие
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
