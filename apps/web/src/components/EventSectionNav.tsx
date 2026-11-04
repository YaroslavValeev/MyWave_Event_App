"use client";

import styles from "./EventSectionNav.module.css";

export type EventPhaseId = "overview" | "prep" | "day" | "wrap";

export type EventSectionTab = {
  id: string;
  label: string;
};

const PHASES: ReadonlyArray<{
  id: EventPhaseId;
  label: string;
  short: string;
  tabs: readonly string[];
}> = [
  { id: "overview", label: "Обзор", short: "Обзор", tabs: ["overview", "feed"] },
  {
    id: "prep",
    label: "Подготовка",
    short: "Подготовка",
    tabs: ["checklist", "docs", "participants", "apps", "slots"],
  },
  {
    id: "day",
    label: "День соревнований",
    short: "День",
    tabs: ["heats", "scoring", "scoreboard"],
  },
  {
    id: "wrap",
    label: "Итоги",
    short: "Итоги",
    tabs: ["results", "protocol", "report"],
  },
];

export function phaseForTab(tabId: string): EventPhaseId {
  const found = PHASES.find((p) => p.tabs.includes(tabId));
  return found?.id ?? "overview";
}

type EventSectionNavProps = {
  activeTab: string;
  tabs: EventSectionTab[];
  onSelect: (tabId: string) => void;
};

export function EventSectionNav({ activeTab, tabs, onSelect }: EventSectionNavProps) {
  const allowed = new Set(tabs.map((t) => t.id));
  const activePhase = phaseForTab(activeTab);
  const phaseMeta = PHASES.find((p) => p.id === activePhase) ?? PHASES[0];
  const secondary = tabs.filter((t) => phaseMeta.tabs.includes(t.id));

  return (
    <div className={styles.wrap}>
      <div className={styles.phases} role="tablist" aria-label="Этапы события">
        {PHASES.map((phase) => {
          const firstAllowed = phase.tabs.find((id) => allowed.has(id));
          if (!firstAllowed) return null;
          const selected = phase.id === activePhase;
          return (
            <button
              key={phase.id}
              type="button"
              role="tab"
              aria-selected={selected}
              className={`${styles.phase} ${selected ? styles.phaseActive : ""}`}
              onClick={() => onSelect(firstAllowed)}
            >
              <span className={styles.phaseFull}>{phase.label}</span>
              <span className={styles.phaseShort}>{phase.short}</span>
            </button>
          );
        })}
      </div>
      {secondary.length > 0 ? (
        <div className={styles.secondary} role="tablist" aria-label={`Разделы: ${phaseMeta.label}`}>
          {secondary.map((t) => (
            <button
              key={t.id}
              type="button"
              role="tab"
              aria-selected={activeTab === t.id}
              className={`${styles.subTab} ${activeTab === t.id ? styles.subTabActive : ""}`}
              onClick={() => onSelect(t.id)}
            >
              {t.label}
            </button>
          ))}
        </div>
      ) : null}
    </div>
  );
}
