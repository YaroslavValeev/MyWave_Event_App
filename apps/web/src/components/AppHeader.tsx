"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import {
  clearSession,
  getStoredToken,
  getStoredUser,
  getUnreadCount,
  SESSION_CHANGED_EVENT,
  type UserOut,
} from "@/lib/api";
import { loginHref } from "@/lib/format";
import { ROLE_LABELS, isStaffRole, type Role } from "@/lib/roles";
import styles from "./AppHeader.module.css";

type AppHeaderProps = {
  subtitle?: string;
};

function NavLink({
  href,
  children,
  pathname,
}: {
  href: string;
  children: React.ReactNode;
  pathname: string;
}) {
  const active = pathname === href || (href !== "/" && pathname.startsWith(href));
  return (
    <Link
      href={href}
      className={`${styles.navLink} ${active ? styles.navLinkActive : ""}`}
      aria-current={active ? "page" : undefined}
    >
      {children}
    </Link>
  );
}

export function AppHeader({ subtitle }: AppHeaderProps) {
  const router = useRouter();
  const pathname = usePathname() || "/";
  const [user, setUser] = useState<UserOut | null>(null);
  const [unread, setUnread] = useState(0);

  useEffect(() => {
    function refresh() {
      setUser(getStoredUser());
      const token = getStoredToken();
      if (!token) {
        setUnread(0);
        return;
      }
      void getUnreadCount(token)
        .then((count) => setUnread(count))
        .catch(() => setUnread(0));
    }
    refresh();
    window.addEventListener(SESSION_CHANGED_EVENT, refresh);
    return () => window.removeEventListener(SESSION_CHANGED_EVENT, refresh);
  }, [pathname]);

  function onLogout() {
    clearSession();
    setUser(null);
    router.push("/");
  }

  const roleLabel =
    user && user.role in ROLE_LABELS ? ROLE_LABELS[user.role as Role] : user?.role;

  const guestDesktopLinks = (
    <>
      <NavLink href="/" pathname={pathname}>
        Главная
      </NavLink>
      <NavLink href="/events" pathname={pathname}>
        События
      </NavLink>
      <NavLink href="/projects/checklist-org" pathname={pathname}>
        Проекты
      </NavLink>
      <Link
        href={loginHref(pathname)}
        className={`${styles.navLink} ${pathname === "/login" || pathname.startsWith("/login") ? styles.navLinkActive : ""}`}
      >
        Войти
      </Link>
      <NavLink href="/register" pathname={pathname}>
        Аккаунт
      </NavLink>
    </>
  );

  const guestMobileLinks = (
    <>
      <NavLink href="/" pathname={pathname}>
        Главная
      </NavLink>
      <NavLink href="/events" pathname={pathname}>
        События
      </NavLink>
      <Link
        href={loginHref(pathname)}
        className={`${styles.navLink} ${pathname === "/login" || pathname.startsWith("/login") ? styles.navLinkActive : ""}`}
      >
        Войти
      </Link>
      <NavLink href="/register" pathname={pathname}>
        Аккаунт
      </NavLink>
    </>
  );

  const userDesktopLinks = (
    <>
      <NavLink href="/" pathname={pathname}>
        Главная
      </NavLink>
      <NavLink href="/events" pathname={pathname}>
        События
      </NavLink>
      <NavLink href="/projects/checklist-org" pathname={pathname}>
        Проекты
      </NavLink>
      {isStaffRole(user?.role ?? "") ? (
        <>
          <NavLink href="/admin/approvals" pathname={pathname}>
            Доступы
          </NavLink>
          <NavLink href="/admin/imports" pathname={pathname}>
            Импорт
          </NavLink>
        </>
      ) : null}
      <NavLink href="/notifications" pathname={pathname}>
        Уведомления
        {unread > 0 ? (
          <span className={styles.badge} aria-label={`Непрочитанных: ${unread}`}>
            {unread}
          </span>
        ) : null}
      </NavLink>
      <NavLink href="/profile" pathname={pathname}>
        Профиль
      </NavLink>
      <button type="button" className={styles.navButton} onClick={onLogout}>
        Выйти
      </button>
    </>
  );

  /** Mobile: max 4–5 destinations; «Выйти» только в профиле. */
  const userMobileLinks = (
    <>
      <NavLink href="/" pathname={pathname}>
        Главная
      </NavLink>
      <NavLink href="/events" pathname={pathname}>
        События
      </NavLink>
      <NavLink href="/notifications" pathname={pathname}>
        Уведомления
        {unread > 0 ? (
          <span className={styles.badge} aria-label={`Непрочитанных: ${unread}`}>
            {unread}
          </span>
        ) : null}
      </NavLink>
      <NavLink href="/profile" pathname={pathname}>
        Профиль
      </NavLink>
    </>
  );

  return (
    <header className={styles.header}>
      <div className={styles.brandRow}>
        <Link href="/" className={styles.brand}>
          MyWave Event
        </Link>
        {subtitle ? <p className={styles.subtitle}>{subtitle}</p> : null}
        {user ? (
          <p className={styles.session}>
            {user.display_name || user.email}
            {roleLabel ? ` · ${roleLabel}` : ""}
          </p>
        ) : null}
      </div>
      <nav className={`${styles.nav} ${styles.desktopNav}`} aria-label="Основная навигация">
        {user ? userDesktopLinks : guestDesktopLinks}
      </nav>
      <nav className={styles.bottomNav} aria-label="Мобильная навигация">
        {user ? userMobileLinks : guestMobileLinks}
      </nav>
    </header>
  );
}
