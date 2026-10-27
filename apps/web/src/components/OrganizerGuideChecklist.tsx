"use client";

import { useEffect, useMemo, useState } from "react";
import {
  ORGANIZER_GUIDE_SECTIONS,
  organizerGuideTotals,
  readGuideDoneIds,
  writeGuideDoneIds,
} from "@/lib/organizerGuide";
import styles from "../app/events/events.module.css";

export function OrganizerGuideChecklist() {
  const [done, setDone] = useState<string[]>([]);
  const doneSet = useMemo(() => new Set(done), [done]);
  const { total, done: doneCount, percent } = organizerGuideTotals(doneSet);

  useEffect(() => {
    setDone(readGuideDoneIds());
  }, []);

  function toggle(id: string) {
    const next = doneSet.has(id) ? done.filter((item) => item !== id) : [...done, id];
    setDone(next);
    writeGuideDoneIds(next);
  }

  function reset() {
    setDone([]);
    writeGuideDoneIds([]);
  }

  return (
    <section className={styles.workspace} id="guide" aria-labelledby="organizer-guide-title">
      <h2 id="organizer-guide-title" className={styles.itemTitle}>
        Условия площадки — 11 разделов
      </h2>
      <p className={styles.muted}>
        Справочник подготовки старта: судьи, вода, зоны, медиа, партнёры. Отметки хранятся в этом
        браузере. Чек-лист конкретного события (документы, состав, старты) — на вкладке «Подготовка»
        карточки соревнования.
      </p>
      <div className={styles.panel} aria-live="polite">
        <strong>
          Готово {doneCount} из {total} ({percent}%)
        </strong>
        <div className={styles.guideTrack} aria-hidden="true">
          <span className={styles.guideFill} style={{ width: `${percent}%` }} />
        </div>
        <div className={styles.actions} style={{ marginTop: "0.75rem" }}>
          <button type="button" className="btn btnSecondary btnSm" onClick={reset} disabled={doneCount === 0}>
            Сбросить отметки
          </button>
        </div>
      </div>
      <nav className={styles.guideNav} aria-label="Разделы чек-листа">
        {ORGANIZER_GUIDE_SECTIONS.map((section) => (
          <a key={section.id} href={`#guide-${section.id}`} className={styles.guideNavLink}>
            {section.title}
          </a>
        ))}
      </nav>
      {ORGANIZER_GUIDE_SECTIONS.map((section) => {
        const sectionDone = section.items.filter((item) => doneSet.has(item.id)).length;
        return (
          <article key={section.id} id={`guide-${section.id}`} className={styles.workspaceCard}>
            <h3 className={styles.workspaceCardTitle}>
              {section.title}{" "}
              <span className={styles.muted}>
                {sectionDone}/{section.items.length}
              </span>
            </h3>
            <ul className={styles.list}>
              {section.items.map((item) => {
                const checked = doneSet.has(item.id);
                return (
                  <li key={item.id} className={styles.item}>
                    <label className={styles.guideItem} htmlFor={`guide-item-${item.id}`}>
                      <input
                        id={`guide-item-${item.id}`}
                        type="checkbox"
                        checked={checked}
                        onChange={() => toggle(item.id)}
                      />
                      <span>
                        <strong>{item.title}</strong>
                        <span className={styles.muted}>{item.hint}</span>
                      </span>
                    </label>
                  </li>
                );
              })}
            </ul>
          </article>
        );
      })}
    </section>
  );
}
