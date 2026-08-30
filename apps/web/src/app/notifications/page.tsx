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
import { AuthNeeded } from "@/components/AuthNeeded";
import styles from "../login/login.module.css";

export default function NotificationsPage() {
  const [items, setItems] = useState<NotificationOut[]>([]);
  const [unread, setUnread] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);
  const [needsAuth, setNeedsAuth] = useState(false);

  const load = useCallback(async () => {
    const token = getStoredToken();
    if (!token) {
      setNeedsAuth(true);
      setItems([]);
      return;
    }
    setNeedsAuth(false);
    setError(null);
    try {
      const payload = await listMyNotifications(token);
      setItems(payload.items);
      setUnread(payload.unread_count);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Не удалось загрузить уведомления");
      if (err instanceof ApiError && (err.status === 401 || err.code === "token_expired")) {
        setNeedsAuth(true);
      }
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
      <AppHeader subtitle="Уведомления" />
      <main id="main" className={styles.main} style={{ maxWidth: "40rem" }}>
        <h1 className={styles.title}>Уведомления</h1>
        <p className={styles.hint}>
          Статусы заявок и ролей приходят сюда. Непрочитанных: {unread}.
        </p>
        {needsAuth ? (
          <AuthNeeded next="/notifications" title="Нужен вход" actionLabel="Войти">
            Уведомления о заявках и ролях видны после входа. После входа вернёмся сюда.
          </AuthNeeded>
        ) : null}
        {unread > 0 && !needsAuth ? (
          <p>
            <button type="button" className={styles.secondary} disabled={pending} onClick={() => void markAll()}>
              Отметить все прочитанными
            </button>
          </p>
        ) : null}

        {error && !needsAuth ? (
          <p className={styles.error} role="alert">
            {error}
          </p>
        ) : null}

        {items.length === 0 && !error && !needsAuth ? (
          <p className={styles.hint}>Здесь появятся решение по заявке и изменения роли.</p>
        ) : null}
        {items.length > 0 && !needsAuth ? (
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
        ) : null}
      </main>
    </>
  );
}
