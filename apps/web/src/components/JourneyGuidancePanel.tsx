"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import {
  ApiError,
  EventGuidance,
  getEventGuidance,
  getStoredToken,
} from "@/lib/api";
import styles from "./JourneyGuidancePanel.module.css";

const HIDE_OPTIONAL_TIPS_KEY = "mywave_hide_optional_tips";

const PHASE_LABELS: Record<string, string> = {
  DRAFT: "Черновик",
  CONFIGURED: "Подготовка завершена",
  REGISTRATION: "Регистрация",
  LIVE: "Мероприятие идёт",
  RESULTS_REVIEW: "Проверка результатов",
  OFFICIAL: "Официальные итоги",
  ARCHIVED: "Архив",
};

export function JourneyGuidancePanel({ eventId }: { eventId: string }) {
  const [guidance, setGuidance] = useState<EventGuidance | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isOnline, setIsOnline] = useState(true);
  const [hideOptionalTips, setHideOptionalTips] = useState(false);

  useEffect(() => {
    setIsOnline(navigator.onLine);
    setHideOptionalTips(localStorage.getItem(HIDE_OPTIONAL_TIPS_KEY) === "true");

    const online = () => setIsOnline(true);
    const offline = () => setIsOnline(false);
    window.addEventListener("online", online);
    window.addEventListener("offline", offline);
    return () => {
      window.removeEventListener("online", online);
      window.removeEventListener("offline", offline);
    };
  }, []);

  useEffect(() => {
    let cancelled = false;
    getEventGuidance(eventId, getStoredToken())
      .then((payload) => {
        if (!cancelled) setGuidance(payload);
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : "Не удалось загрузить подсказки");
        }
      });
    return () => {
      cancelled = true;
    };
  }, [eventId]);

  function toggleOptionalTips() {
    setHideOptionalTips((current) => {
      const next = !current;
      localStorage.setItem(HIDE_OPTIONAL_TIPS_KEY, String(next));
      return next;
    });
  }

  if (error) {
    return <p className={styles.error} role="alert">{error}</p>;
  }
  if (!guidance) {
    return <p className={styles.loading}>Загружаем следующие шаги…</p>;
  }

  const tasks = hideOptionalTips
    ? guidance.tasks.filter((task) => task.required)
    : guidance.tasks;

  return (
    <section className={styles.panel} aria-labelledby="journey-guidance-title">
      <div className={styles.heading}>
        <div>
          <p className={styles.eyebrow}>Этап мероприятия</p>
          <h2 id="journey-guidance-title">Что делать дальше?</h2>
        </div>
        <span className={styles.phase}>
          {PHASE_LABELS[guidance.journey_phase] ?? guidance.journey_phase}
        </span>
      </div>

      {!isOnline ? (
        <div className={styles.offline} role="status">
          <strong>Нет подключения к интернету.</strong> {guidance.offline_note}
        </div>
      ) : null}

      {guidance.next_step ? (
        <div className={styles.nextStep}>
          <span>Следующий шаг</span>
          {guidance.next_step.href ? (
            <Link href={guidance.next_step.href}>{guidance.next_step.title} →</Link>
          ) : (
            <strong>{guidance.next_step.title}</strong>
          )}
        </div>
      ) : null}

      <div className={styles.sectionHead}>
        <h3>Мои задачи</h3>
        <label className={styles.toggle}>
          <input
            type="checkbox"
            checked={hideOptionalTips}
            onChange={toggleOptionalTips}
          />
          Скрыть необязательные подсказки
        </label>
      </div>
      {tasks.length ? (
        <ul className={styles.list}>
          {tasks.map((task) => (
            <li key={task.id} className={styles.task}>
              <span className={task.required ? styles.required : styles.optional}>
                {task.required ? "Важно" : "Совет"}
              </span>
              {task.href ? <Link href={task.href}>{task.title}</Link> : <span>{task.title}</span>}
              {!isOnline && task.requires_online ? (
                <small>Нужен интернет</small>
              ) : null}
            </li>
          ))}
        </ul>
      ) : (
        <p className={styles.muted}>Обязательных задач сейчас нет.</p>
      )}

      {!hideOptionalTips && guidance.tips.length ? (
        <div className={styles.tips}>
          <h3>Полезные подсказки</h3>
          <ul>
            {guidance.tips.map((tip) => <li key={tip.code}>{tip.title}</li>)}
          </ul>
        </div>
      ) : null}

      {guidance.completed.length ? (
        <details className={styles.completed}>
          <summary>Завершённые ({guidance.completed.length})</summary>
          <ul>
            {guidance.completed.map((item) => <li key={item.id}>✓ {item.title}</li>)}
          </ul>
        </details>
      ) : null}
    </section>
  );
}
