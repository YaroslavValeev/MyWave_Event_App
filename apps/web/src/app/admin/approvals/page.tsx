"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { AppHeader } from "@/components/AppHeader";
import {
  ApiError,
  PendingApproval,
  decidePendingApproval,
  getStoredToken,
  getStoredUser,
  listPendingApprovals,
} from "@/lib/api";
import { ROLE_LABELS, isStaffRole, type Role } from "@/lib/roles";
import { AuthNeeded } from "@/components/AuthNeeded";
import styles from "../../login/login.module.css";

export default function ApprovalsAdminPage() {
  const [items, setItems] = useState<PendingApproval[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [pending, setPending] = useState(false);
  const [gate, setGate] = useState<"ok" | "auth" | "forbidden">("ok");

  const load = useCallback(async () => {
    const token = getStoredToken();
    const user = getStoredUser();
    if (!token || !user) {
      setGate("auth");
      setItems([]);
      return;
    }
    if (!isStaffRole(user.role)) {
      setGate("forbidden");
      setItems([]);
      return;
    }
    setGate("ok");
    setError(null);
    try {
      const list = await listPendingApprovals(token);
      setItems(list);
    } catch (err) {
      if (err instanceof ApiError && (err.status === 401 || err.code === "token_expired")) {
        setGate("auth");
        return;
      }
      if (err instanceof ApiError && err.status === 403) {
        setGate("forbidden");
        return;
      }
      setError(err instanceof ApiError ? err.message : "Не удалось загрузить заявки");
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function decide(approvalId: number, decision: "approve" | "reject") {
    const token = getStoredToken();
    if (!token) return;
    setPending(true);
    setMessage(null);
    setError(null);
    try {
      const result = await decidePendingApproval(token, approvalId, decision);
      setMessage(result.message);
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Ошибка решения");
    } finally {
      setPending(false);
    }
  }

  return (
    <>
      <AppHeader subtitle="Очередь ролей" />
      <main id="main" className={styles.main} style={{ maxWidth: "40rem" }}>
        <h1 className={styles.title}>Доступы и роли</h1>
        <p className={styles.hint}>
          Подтвердите судью, комментатора или организатора.{" "}
          <Link href="/events">К событиям</Link>
        </p>

        {gate === "auth" ? (
          <AuthNeeded next="/admin/approvals" title="Нужен вход организатора">
            Очередь ролей видна только организатору и админу. После входа вернёмся сюда.
          </AuthNeeded>
        ) : null}
        {gate === "forbidden" ? (
          <div className="card" role="status">
            <strong>Недостаточно прав</strong>
            <p className={styles.hint}>
              Подтверждать роли может организатор или админ платформы. Откройте события — там ваш рабочий
              путь.
            </p>
            <Link href="/events" className="btn btnPrimary">
              К событиям
            </Link>
          </div>
        ) : null}

        {error && gate === "ok" ? (
          <p className={styles.error} role="alert">
            {error}
          </p>
        ) : null}
        {message ? (
          <p className={styles.hint} role="status">
            {message}
          </p>
        ) : null}

        {gate === "ok" && items.length === 0 && !error ? (
          <p className={styles.hint}>Очередь пуста.</p>
        ) : null}
        {gate === "ok" && items.length > 0 ? (
          <ul style={{ listStyle: "none", padding: 0, display: "grid", gap: "1rem" }}>
            {items.map((item) => (
              <li
                key={item.approval_id}
                style={{
                  border: "1px solid color-mix(in srgb, var(--foam) 25%, transparent)",
                  borderRadius: "0.5rem",
                  padding: "0.9rem 1rem",
                }}
              >
                <strong>{item.display_name || item.email}</strong>
                <div className={styles.hint}>
                  {item.email}
                  {item.phone_masked ? ` · ${item.phone_masked}` : ""}
                </div>
                <div className={styles.hint}>
                  Роль: {ROLE_LABELS[item.requested_role as Role] || item.requested_role}
                </div>
                <div style={{ display: "flex", gap: "0.6rem", marginTop: "0.75rem" }}>
                  <button
                    type="button"
                    className={styles.submit}
                    disabled={pending}
                    onClick={() => void decide(item.approval_id, "approve")}
                  >
                    Утвердить
                  </button>
                  <button
                    type="button"
                    className={styles.secondary}
                    disabled={pending}
                    onClick={() => void decide(item.approval_id, "reject")}
                  >
                    Отклонить
                  </button>
                </div>
              </li>
            ))}
          </ul>
        ) : null}
      </main>
    </>
  );
}
