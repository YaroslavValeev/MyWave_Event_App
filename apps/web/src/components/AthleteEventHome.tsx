import { StatusBadge } from "@/components/StatusBadge";
import type { AthleteSnapshot } from "@/lib/eventWorkspace";
import styles from "../app/events/events.module.css";

type AthleteEventHomeProps = {
  snapshot: AthleteSnapshot;
  onOpenStartList: () => void;
  onOpenResults: () => void;
  onApply: () => void;
  canOpenStartList: boolean;
  canOpenResults: boolean;
};

export function AthleteEventHome({
  snapshot,
  onOpenStartList,
  onOpenResults,
  onApply,
  canOpenStartList,
  canOpenResults,
}: AthleteEventHomeProps) {
  return (
    <section className={styles.workspace} aria-labelledby="athlete-home-title">
      <h2 id="athlete-home-title" className={styles.itemTitle}>
        Мой старт
      </h2>
      <p className={styles.muted}>Что происходит с вами на этом соревновании сейчас.</p>
      <div className={styles.currentAthlete}>
        <div className={styles.itemHead}>
          <strong>{snapshot.fullName}</strong>
          <span className={styles.phaseChip}>{snapshot.phaseLabel}</span>
        </div>
        {snapshot.athleteId ? (
          <p className={styles.athleteIdLine}>
            MyWave Athlete ID: <code>{snapshot.athleteId}</code>
          </p>
        ) : null}
        <dl className={styles.meta}>
          <div>
            <dt>Категория</dt>
            <dd>{snapshot.categoryTitle || "—"}</dd>
          </div>
          <div>
            <dt>Заезд</dt>
            <dd>
              {snapshot.heatCode
                ? `${snapshot.heatCode}${snapshot.heatTitle ? ` — ${snapshot.heatTitle}` : ""}`
                : "Ещё не назначен"}
            </dd>
          </div>
          <div>
            <dt>Стартовый номер</dt>
            <dd>{snapshot.bib ? `№${snapshot.bib}` : "—"}</dd>
          </div>
          <div>
            <dt>Очередь</dt>
            <dd>
              {snapshot.startOrder != null
                ? snapshot.queueAhead === 0
                  ? "Вы следующие или на воде"
                  : `Перед вами: ${snapshot.queueAhead}`
                : "—"}
            </dd>
          </div>
        </dl>
        {snapshot.applicationStatus ? (
          <p className={styles.muted} style={{ marginTop: "0.5rem" }}>
            Заявка: <StatusBadge status={snapshot.applicationStatus} kind="application" />
          </p>
        ) : null}
        {snapshot.resultStatus ? (
          <p className={styles.muted}>
            Мой результат:{" "}
            {snapshot.resultPlace != null ? `${snapshot.resultPlace} место` : "без места"}
            {snapshot.resultScore != null ? ` · ${snapshot.resultScore}` : ""}{" "}
            <StatusBadge status={snapshot.resultStatus} kind="result" />
          </p>
        ) : null}
        <div className={styles.actions}>
          {snapshot.phase === "not_applied" ? (
            <button type="button" className="btn btnPrimary" onClick={onApply}>
              Подать заявку
            </button>
          ) : null}
          {canOpenStartList ? (
            <button type="button" className="btn btnPrimary" onClick={onOpenStartList}>
              Открыть стартовый список
            </button>
          ) : null}
          {canOpenResults && snapshot.resultStatus ? (
            <button type="button" className="btn btnSecondary" onClick={onOpenResults}>
              Мой результат
            </button>
          ) : null}
        </div>
      </div>
    </section>
  );
}
