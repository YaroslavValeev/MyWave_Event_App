"use client";

import type { ChecklistItemOut } from "@/lib/api";
import styles from "./PreparationActionList.module.css";

/** Map checklist codes → existing event tabs (deep links). */
const CODE_TO_TAB: Record<string, string> = {
  documents: "docs",
  categories: "overview",
  officials: "overview",
  registration: "apps",
  roster: "participants",
  medical: "participants",
  start_lists: "heats",
  day_starts_ready: "heats",
  day_medical_gate: "participants",
  day_protocol_filed: "protocol",
};

const CODE_HINT: Record<string, string> = {
  documents: "Открыть документы",
  categories: "Смотреть категории на обзоре",
  officials: "Смотреть судейский корпус",
  registration: "Заявки / регистрация",
  roster: "Открыть состав",
  medical: "Состав и медфлаги",
  start_lists: "Заезды и стартовые списки",
  day_starts_ready: "Контроль стартов",
  day_medical_gate: "Медконтроль в составе",
  day_protocol_filed: "Протоколы и ревизии",
};

type PreparationActionListProps = {
  items: ChecklistItemOut[];
  doneCount: number;
  canModerate: boolean;
  onToggle: (item: ChecklistItemOut) => void;
  onOpenTab: (tabId: string) => void;
};

export function PreparationActionList({
  items,
  doneCount,
  canModerate,
  onToggle,
  onOpenTab,
}: PreparationActionListProps) {
  return (
    <section className={styles.wrap} aria-labelledby="prep-actions-title">
      <h2 id="prep-actions-title" className={styles.title}>
        Подготовка события ({doneCount}/{items.length})
      </h2>
      <p className={styles.muted}>
        Нажмите действие, чтобы перейти к нужному разделу. Отметка «готово» не подменяет
        наличие файла или данных на сервере.
      </p>
      <ul className={styles.list}>
        {items.map((item) => {
          const target = CODE_TO_TAB[item.code] ?? "checklist";
          const hint = CODE_HINT[item.code] ?? "Открыть раздел";
          return (
            <li key={item.id} className={styles.item}>
              <div className={styles.head}>
                <strong>
                  {item.is_done ? "✓ " : "○ "}
                  {item.title}
                </strong>
                <div className={styles.actions}>
                  <button
                    type="button"
                    className="btn btnSecondary btnSm"
                    data-go={item.code}
                    onClick={() => onOpenTab(target)}
                  >
                    {hint}
                  </button>
                  {canModerate ? (
                    <button
                      type="button"
                      className="btn btnPrimary btnSm"
                      onClick={() => onToggle(item)}
                    >
                      {item.is_done ? "Снять" : "Отметить"}
                    </button>
                  ) : null}
                </div>
              </div>
              {canModerate ? <div className={styles.code}>{item.code}</div> : null}
            </li>
          );
        })}
      </ul>
    </section>
  );
}
