"use client";

import Link from "next/link";
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

/** Deep-link из entity_type / entity_id уведомления. */
function notificationHref(item: NotificationOut): string | null {
  const type = (item.entity_type || "").toLowerCase();
  const id = item.entity_id;
  if (!id) {
    if (/result|результат/i.test(item.kind) || /результат/i.test(item.title)) {
      return "/events";
    }
    return null;
  }
  if (type.includes("event") || type === "competition") {
    return `/events/${id}`;
  }
  if (type.includes("heat") || type.includes("start")) {
    return `/events/${id}#heats`;
  }
  if (type.includes("result")) {
    return `/events/${id}#results`;
  }
  if (type.includes("score") || type.includes("judg")) {
    return `/events/${id}#scoring`;
  }
  if (type.includes("application") || type.includes("registration")) {
    return `/events/${id}#apps`;
  }
  if (/^\d+$/.test(id)) {
    return `/events/${id}`;
  }
  return null;
}

function actionLabel(item: NotificationOut, href: string | null): string {
  if (!href) return "Открыть";
  if (href.includes("#scoring")) return "Перейти к судейству";
  if (href.includes("#heats")) return "Открыть стартовый список";
  if (href.includes("#results")) return "Посмотреть результаты";
  if (href.includes("#apps")) return "Открыть заявку";
  return "Открыть соревнование";
}

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
          Статусы заявок, ролей и стартов. Непрочитанных: {unread}.
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
          <p className={styles.hint}>
            Лента пока пуста. Когда изменят заявку или роль, сообщение появится здесь.{" "}
            <Link href="/events">К событиям</Link>
          </p>
        ) : null}
        {items.length > 0 && !needsAuth ? (
          <ul style={{ listStyle: "none", padding: 0, display: "grid", gap: "0.85rem" }}>
            {items.map((item) => {
              const href = notificationHref(item);
              return (
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
                  <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem", marginTop: "0.6rem" }}>
                    {href ? (
                      <Link
                        href={href}
                        className={styles.submit}
                        style={{ display: "inline-flex", textDecoration: "none" }}
                        onClick={() => {
                          if (!item.is_read) void markOne(item.id);
                        }}
                      >
                        {actionLabel(item, href)}
                      </Link>
                    ) : null}
                    {!item.is_read ? (
                      <button
                        type="button"
                        className={styles.secondary}
                        disabled={pending}
                        onClick={() => void markOne(item.id)}
                      >
                        Прочитано
                      </button>
                    ) : null}
                  </div>
                </li>
              );
            })}
          </ul>
        ) : null}
      </main>
    </>
  );
}
