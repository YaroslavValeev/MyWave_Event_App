"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { clearSession, getStoredUser, type UserOut } from "@/lib/api";
import { ROLE_LABELS, type Role } from "@/lib/roles";
import styles from "./AppHeader.module.css";

type AppHeaderProps = {
  subtitle?: string;
};

export function AppHeader({ subtitle }: AppHeaderProps) {
  const router = useRouter();
  const [user, setUser] = useState<UserOut | null>(null);

  useEffect(() => {
    setUser(getStoredUser());
  }, []);

  function onLogout() {
    clearSession();
    setUser(null);
    router.push("/");
  }

  const roleLabel =
    user && user.role in ROLE_LABELS
      ? ROLE_LABELS[user.role as Role]
      : user?.role;

  return (
    <header className={styles.header}>
      <div className={styles.brandRow}>
        <Link href="/" className={styles.brand}>
          MyWave Event App
        </Link>
        {subtitle ? <p className={styles.subtitle}>{subtitle}</p> : null}
        {user ? (
          <p className={styles.session}>
            {user.display_name || user.email}
            {roleLabel ? ` · ${roleLabel}` : ""}
          </p>
        ) : null}
      </div>
      <nav className={styles.nav} aria-label="Основная навигация">
        <Link href="/events" className={styles.navLink}>
          События
        </Link>
        {user?.role === "platform_admin" ||
        user?.role === "event_admin" ||
        user?.role === "organizer" ||
        user?.role === "federation_manager" ? (
          <Link href="/admin/approvals" className={styles.navLink}>
            Заявки
          </Link>
        ) : null}
        {user ? (
          <>
            <Link href="/profile" className={styles.navLink}>
              Профиль
            </Link>
            <button type="button" className={styles.navButton} onClick={onLogout}>
              Выйти
            </button>
          </>
        ) : (
          <>
            <Link href="/login" className={styles.navLink}>
              Вход
            </Link>
            <Link href="/register" className={styles.navLink}>
              Регистрация
            </Link>
          </>
        )}
        <Link href="/health" className={styles.navLink}>
          Статус
        </Link>
      </nav>
    </header>
  );
}
