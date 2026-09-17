"use client";

import Link from "next/link";
import { useEffect } from "react";
import { AppDownloadCard } from "@/components/AppDownloadCard";
import { AppHeader } from "@/components/AppHeader";
import { OrganizerGuideChecklist } from "@/components/OrganizerGuideChecklist";
import styles from "../../events/events.module.css";

export default function OrganizerChecklistPage() {
  useEffect(() => {
    const hash = window.location.hash;
    if (!hash) return;
    document.getElementById(hash.slice(1))?.scrollIntoView({ block: "start" });
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
          Здесь живут два слоя: готовое приложение для старта и справочник площадки из 11 разделов.
          Подготовка конкретного соревнования (состав, документы, старты) — в карточке события.
        </p>
        <AppDownloadCard context="projects/checklist-org" />
        <OrganizerGuideChecklist />
      </main>
    </>
  );
}
