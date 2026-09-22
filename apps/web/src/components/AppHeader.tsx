"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
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
  onNavigate,
}: {
  href: string;
  children: React.ReactNode;
  pathname: string;
  onNavigate?: () => void;
}) {
  const active = pathname === href || (href !== "/" && pathname.startsWith(href));
  return (
    <Link
      href={href}
      className={`${styles.navLink} ${active ? styles.navLinkActive : ""}`}
      aria-current={active ? "page" : undefined}
      onClick={onNavigate}
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
  const [moreOpen, setMoreOpen] = useState(false);
  const moreRef = useRef<HTMLDivElement | null>(null);

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

  useEffect(() => {
    setMoreOpen(false);
  }, [pathname]);

  useEffect(() => {
    if (!moreOpen) return;
    function onDoc(event: MouseEvent) {
      if (!moreRef.current?.contains(event.target as Node)) {
        setMoreOpen(false);
      }
    }
    function onKey(event: KeyboardEvent) {
      if (event.key === "Escape") setMoreOpen(false);
    }
    document.addEventListener("mousedown", onDoc);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDoc);
      document.removeEventListener("keydown", onKey);
    };
  }, [moreOpen]);

  function onLogout() {
    clearSession();
    setUser(null);
    setMoreOpen(false);
    router.push("/");
  }

  const roleLabel =
    user && user.role in ROLE_LABELS ? ROLE_LABELS[user.role as Role] : null;
  const staff = isStaffRole(user?.role ?? "");
  const displayName = user?.display_name?.trim() || null;

  const unreadBadge =
    unread > 0 ? (
      <span className={styles.badge} aria-label={`Непрочитанных: ${unread}`}>
        {unread}
      </span>
    ) : null;

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
      {staff ? (
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
        {unreadBadge}
      </NavLink>
      <NavLink href="/profile" pathname={pathname}>
        Профиль
      </NavLink>
      <button type="button" className={styles.navButton} onClick={onLogout}>
        Выйти
      </button>
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
      <NavLink href="/projects/checklist-org" pathname={pathname}>
        Проекты
      </NavLink>
      <Link
        href={loginHref(pathname)}
        className={`${styles.navLink} ${pathname === "/login" || pathname.startsWith("/login") ? styles.navLinkActive : ""}`}
      >
        Войти
      </Link>
    </>
  );

  const userMobilePrimary = (
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
      <NavLink href="/notifications" pathname={pathname}>
        Лента
        {unreadBadge}
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
        {user && displayName ? (
          <p className={styles.session}>
            {displayName}
            {roleLabel ? ` · ${roleLabel}` : ""}
          </p>
        ) : null}
      </div>
      <nav className={`${styles.nav} ${styles.desktopNav}`} aria-label="Основная навигация">
        {user ? userDesktopLinks : guestDesktopLinks}
      </nav>
      <nav className={styles.bottomNav} aria-label="Мобильная навигация">
        {user ? (
          <>
            {userMobilePrimary}
            <div className={styles.moreWrap} ref={moreRef}>
              <button
                type="button"
                className={`${styles.navButton} ${moreOpen || pathname.startsWith("/admin") || pathname === "/profile" ? styles.navLinkActive : ""}`}
                aria-expanded={moreOpen}
                aria-controls="mobile-more-menu"
                onClick={() => setMoreOpen((open) => !open)}
              >
                Ещё
              </button>
              {moreOpen ? (
                <div id="mobile-more-menu" className={styles.morePanel} role="menu">
                  {staff ? (
                    <>
                      <NavLink
                        href="/admin/approvals"
                        pathname={pathname}
                        onNavigate={() => setMoreOpen(false)}
                      >
                        Доступы
                      </NavLink>
                      <NavLink
                        href="/admin/imports"
                        pathname={pathname}
                        onNavigate={() => setMoreOpen(false)}
                      >
                        Импорт
                      </NavLink>
                    </>
                  ) : null}
                  <NavLink
                    href="/profile"
                    pathname={pathname}
                    onNavigate={() => setMoreOpen(false)}
                  >
                    Профиль
                  </NavLink>
                  <button type="button" className={styles.navButton} role="menuitem" onClick={onLogout}>
                    Выйти
                  </button>
                </div>
              ) : null}
            </div>
          </>
        ) : (
          guestMobileLinks
        )}
      </nav>
    </header>
  );
}
