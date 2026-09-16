"use client";

import Link from "next/link";
import { useEffect } from "react";
import { AppDownloadCard } from "@/components/AppDownloadCard";
import { AppHeader } from "@/components/AppHeader";
import styles from "../../events/events.module.css";

export default function OrganizerChecklistPage() {
  useEffect(() => {
    if (window.location.hash !== "#mywave-event-app") return;
    document.getElementById("mywave-event-app")?.scrollIntoView({ block: "start" });
  }, []);

  return (
    <>
      <AppHeader subtitle="Проекты" />
      <main id="main" className={styles.main}>
        <nav className={styles.muted} aria-label="Навигация по разделу">
          <Link href="/">Главная</Link>
          {" · "}
          <span>Проекты</span>
          {" · "}
          <span>Чек-лист организатора</span>
        </nav>
        <h1 className={styles.title}>Чек-лист организатора</h1>
        <p className={styles.muted}>
          Подготовка конкретного соревнования живёт в карточке события. Ниже — готовое решение
          MyWave Event App: описание, статус и безопасная выдача файлов.
        </p>
        <AppDownloadCard context="projects/checklist-org" />
      </main>
    </>
  );
}
