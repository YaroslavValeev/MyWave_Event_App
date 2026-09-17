import { StatusBadge } from "@/components/StatusBadge";
import type { HeatOut, StartListEntryOut } from "@/lib/api";
import type { AttentionItem } from "@/lib/eventWorkspace";
import { entryStatusLabel } from "@/lib/eventWorkspace";
import styles from "../app/events/events.module.css";

type OrganizerControlRoomProps = {
  nowHeat?: HeatOut;
  nowName?: string;
  nowEntry?: StartListEntryOut;
  nextHeat?: HeatOut;
  nextName?: string;
  attention: AttentionItem[];
  onOpenTab: (tab: AttentionItem["tab"] | "heats" | "moments") => void;
};

export function OrganizerControlRoom({
  nowHeat,
  nowName,
  nowEntry,
  nextHeat,
  nextName,
  attention,
  onOpenTab,
}: OrganizerControlRoomProps) {
  return (
    <section className={styles.workspace} aria-labelledby="control-room-title">
      <h2 id="control-room-title" className={styles.itemTitle}>
        Пульт организатора
      </h2>
      <p className={styles.muted}>Сейчас на воде, кто следующий и что требует вашего решения.</p>
      <div className={styles.workspaceGrid}>
        <article className={styles.workspaceCard}>
          <h3 className={styles.workspaceCardTitle}>Сейчас</h3>
          {nowHeat ? (
            <>
              <p>
                <strong>
                  {nowHeat.code} — {nowHeat.title}
                </strong>
              </p>
              <p className={styles.muted}>
                <StatusBadge status={nowHeat.status} kind="heat" />
                {nowName ? ` · ${nowName}` : ""}
                {nowEntry ? ` · ${entryStatusLabel(nowEntry.status)}` : ""}
              </p>
              <div className={styles.actions}>
                <button type="button" className="btn btnPrimary btnSm" onClick={() => onOpenTab("heats")}>
                  К заездам
                </button>
                <button type="button" className="btn btnSecondary btnSm" onClick={() => onOpenTab("moments")}>
                  Снять момент
                </button>
              </div>
            </>
          ) : (
            <>
              <p className={styles.muted}>Нет активного заезда.</p>
              <button type="button" className="btn btnSecondary btnSm" onClick={() => onOpenTab("moments")}>
                Снять момент
              </button>
            </>
          )}
        </article>
        <article className={styles.workspaceCard}>
          <h3 className={styles.workspaceCardTitle}>Следующий</h3>
          {nextHeat ? (
            <>
              <p>
                <strong>
                  {nextHeat.code} — {nextHeat.title}
                </strong>
              </p>
              <p className={styles.muted}>
                {nextName ? nextName : <StatusBadge status={nextHeat.status} kind="heat" />}
              </p>
            </>
          ) : (
            <p className={styles.muted}>Следующий заезд не назначен.</p>
          )}
        </article>
        <article className={`${styles.workspaceCard} ${styles.attentionCard}`}>
          <h3 className={styles.workspaceCardTitle}>Требует внимания</h3>
          {attention.length === 0 ? (
            <p className={styles.muted}>Срочных задач нет.</p>
          ) : (
            <ul className={styles.attentionList}>
              {attention.map((item) => (
                <li key={item.id}>
                  <button type="button" className={styles.attentionBtn} onClick={() => onOpenTab(item.tab)}>
                    <strong>{item.title}</strong>
                    <span className={styles.muted}>{item.detail}</span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </article>
      </div>
    </section>
  );
}
