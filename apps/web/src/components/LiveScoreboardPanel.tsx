"use client";

import { useCallback, useEffect, useState } from "react";
import {
  ApiError,
  Scoreboard,
  getApiBaseUrl,
  getScoreboard,
  getStoredToken,
} from "@/lib/api";
import styles from "./LiveScoreboardPanel.module.css";

type LiveScoreboardPanelProps = {
  eventId: string;
  includeUnofficial?: boolean;
};

export function LiveScoreboardPanel({
  eventId,
  includeUnofficial = false,
}: LiveScoreboardPanelProps) {
  const [scoreboard, setScoreboard] = useState<Scoreboard | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [usePolling, setUsePolling] = useState(includeUnofficial);

  const load = useCallback(async () => {
    try {
      const payload = await getScoreboard(
        eventId,
        includeUnofficial,
        getStoredToken(),
      );
      setScoreboard(payload);
      setError(null);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Не удалось обновить табло");
    }
  }, [eventId, includeUnofficial]);

  useEffect(() => {
    setUsePolling(includeUnofficial);
    void load();

    if (includeUnofficial || typeof EventSource === "undefined") {
      setUsePolling(true);
      return;
    }

    const stream = new EventSource(
      `${getApiBaseUrl()}/api/v1/events/${eventId}/scoreboard/stream`,
    );
    const onScoreboard = (event: MessageEvent<string>) => {
      try {
        setScoreboard(JSON.parse(event.data) as Scoreboard);
        setError(null);
      } catch {
        setUsePolling(true);
      }
    };
    stream.addEventListener("scoreboard", onScoreboard as EventListener);
    stream.onerror = () => {
      stream.close();
      setUsePolling(true);
    };
    return () => stream.close();
  }, [eventId, includeUnofficial, load]);

  useEffect(() => {
    if (!usePolling) return;
    const timer = window.setInterval(() => void load(), 5_000);
    return () => window.clearInterval(timer);
  }, [load, usePolling]);

  return (
    <section className={styles.panel} aria-labelledby="scoreboard-title">
      <div className={styles.heading}>
        <div>
          <h2 id="scoreboard-title">Табло результатов</h2>
          <p>Обновляется автоматически</p>
        </div>
        {scoreboard?.revision ? (
          <code title={scoreboard.revision}>ревизия {scoreboard.revision.slice(0, 8)}</code>
        ) : null}
      </div>

      {error ? <p className={styles.error} role="alert">{error}</p> : null}
      {!scoreboard && !error ? <p className={styles.muted}>Загрузка табло…</p> : null}

      {scoreboard ? (
        scoreboard.entries.length ? (
          <div className={styles.tableWrap}>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th scope="col">Место</th>
                  <th scope="col">Участник</th>
                  <th scope="col">Балл</th>
                  <th scope="col">Статус</th>
                </tr>
              </thead>
              <tbody>
                {scoreboard.entries.map((entry) => (
                  <tr key={entry.result_id}>
                    <td className={styles.place}>{entry.place ?? "—"}</td>
                    <td>{entry.display_name}</td>
                    <td className={styles.score}>{entry.score ?? "—"}</td>
                    <td>
                      {entry.run_flag ? (
                        <span className={styles.unofficial}>{entry.run_flag}</span>
                      ) : (
                        <span className={entry.official ? styles.official : styles.unofficial}>
                          {entry.official ? "официальный" : "предварительный"}
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className={styles.empty}>Результатов для табло пока нет.</p>
        )
      ) : null}
    </section>
  );
}
