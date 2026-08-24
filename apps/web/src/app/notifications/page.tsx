"use client";

import { useCallback, useEffect, useState } from "react";
import { AppHeader } from "@/components/AppHeader";
import {
  ApiError,
  NotificationOut,
  getStoredToken,
  listMyNotifications,
  markAllNotificationsRead,
  markNotificationRead,
} from "@/lib/api";
import styles from "../login/login.module.css";

export default function NotificationsPage() {
  const [items, setItems] = useState<NotificationOut[]>([]);
  const [unread, setUnread] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  const load = useCallback(async () => {
    const token = getStoredToken();
    if (!token) {
      setError("Нужен вход, чтобы видеть уведомления.");
      return;
    }
    setError(null);
    try {
      const payload = await listMyNotifications(token);
      setItems(payload.items);
      setUnread(payload.unread_count);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Не удалось загрузить уведомления");
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function markOne(id: number) {
    const token = getStoredToken();
    if (!token) return;
    setPending(true);
    try {
      await markNotificationRead(token, id);
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Не удалось отметить прочитанным");
    } finally {
      setPending(false);
    }
  }

  async function markAll() {
    const token = getStoredToken();
    if (!token) return;
    setPending(true);
    try {
      await markAllNotificationsRead(token);
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Не удалось отметить все");
    } finally {
      setPending(false);
    }
  }

  return (
    <>
      <AppHeader subtitle="Журнал статусов" />
      <main id="main" className={styles.main} style={{ maxWidth: "40rem" }}>
        <h1 className={styles.title}>Уведомления</h1>
        <p className={styles.hint}>
          Статусы заявок и ролей видны здесь даже без SMTP. Непрочитанных: {unread}.
        </p>
        {unread > 0 ? (
          <p>
            <button type="button" className={styles.secondary} disabled={pending} onClick={() => void markAll()}>
              Отметить все прочитанными
            </button>
          </p>
        ) : null}

        {error ? (
          <p className={styles.error} role="alert">
            {error}
          </p>
        ) : null}

        {items.length === 0 && !error ? (
          <p className={styles.hint}>Пока нет уведомлений.</p>
        ) : (
          <ul style={{ listStyle: "none", padding: 0, display: "grid", gap: "0.85rem" }}>
            {items.map((item) => (
              <li
                key={item.id}
                style={{
                  border: "1px solid color-mix(in srgb, var(--foam) 25%, transparent)",
                  borderRadius: "0.5rem",
                  padding: "0.85rem 1rem",
                  opacity: item.is_read ? 0.7 : 1,
                }}
              >
                <strong>{item.title}</strong>
                <p className={styles.hint} style={{ margin: "0.35rem 0 0" }}>
                  {item.body}
                </p>
                {!item.is_read ? (
                  <button
                    type="button"
                    className={styles.secondary}
                    disabled={pending}
                    onClick={() => void markOne(item.id)}
                    style={{ marginTop: "0.6rem" }}
                  >
                    Прочитано
                  </button>
                ) : null}
              </li>
            ))}
          </ul>
        )}
      </main>
    </>
  );
}
