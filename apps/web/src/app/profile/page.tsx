"use client";

import { FormEvent, useEffect, useState } from "react";
import Link from "next/link";
import { AppHeader } from "@/components/AppHeader";
import {
  ApiError,
  fetchMe,
  fetchMyConsents,
  getStoredToken,
  grantMyConsent,
  revokeMyConsent,
  saveSession,
  updateMyProfile,
  type ConsentItem,
  type UserOut,
} from "@/lib/api";
import { AuthNeeded } from "@/components/AuthNeeded";
import styles from "../login/login.module.css";

export default function ProfilePage() {
  const [displayName, setDisplayName] = useState("");
  const [phone, setPhone] = useState("");
  const [email, setEmail] = useState("");
  const [athleteId, setAthleteId] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);
  const [consents, setConsents] = useState<ConsentItem[]>([]);
  const [consentBusy, setConsentBusy] = useState<string | null>(null);
  const [needsAuth, setNeedsAuth] = useState(false);

  useEffect(() => {
    const token = getStoredToken();
    if (!token) {
      setNeedsAuth(true);
      return;
    }
    void fetchMe(token)
      .then((me) => {
        setDisplayName(me.display_name || "");
        setPhone(me.phone || "");
        setEmail(me.email);
        setAthleteId(me.athlete_id || null);
      })
      .catch((err) => {
        if (err instanceof ApiError && (err.status === 401 || err.code === "token_expired")) {
          setNeedsAuth(true);
          return;
        }
        setError("Не удалось загрузить профиль. Войдите снова.");
      });
    void fetchMyConsents(token)
      .then((payload) => setConsents(payload.items))
      .catch(() => {
        /* профиль всё равно показываем */
      });
  }, []);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const token = getStoredToken();
    if (!token) {
      setNeedsAuth(true);
      return;
    }
    setError(null);
    setMessage(null);
    setPending(true);
    try {
      const payload: { display_name?: string; phone?: string } = {
        display_name: displayName.trim(),
      };
      const looksReal = /^\+?\d[\d\s()-]{9,}$/.test(phone.trim());
      if (looksReal) {
        payload.phone = phone.trim();
      }
      const me = await updateMyProfile(token, payload);
      const user: UserOut = {
        id: String(me.id),
        email: me.email,
        display_name: me.display_name || me.email,
        role: me.role,
        status: me.status,
        phone: me.phone,
        athlete_id: me.athlete_id ?? null,
      };
      saveSession(token, user);
      setPhone(me.phone || "");
      setDisplayName(me.display_name || "");
      setAthleteId(me.athlete_id || null);
      setMessage("Профиль сохранён.");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Не удалось сохранить профиль.");
    } finally {
      setPending(false);
    }
  }

  async function onConsentToggle(item: ConsentItem) {
    const token = getStoredToken();
    if (!token || item.required) return;
    setConsentBusy(item.purpose);
    setError(null);
    try {
      const updated = item.granted
        ? await revokeMyConsent(token, item.purpose)
        : await grantMyConsent(token, item.purpose);
      setConsents((current) =>
        current.map((row) => (row.purpose === updated.purpose ? updated : row)),
      );
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Не удалось обновить согласие.");
    } finally {
      setConsentBusy(null);
    }
  }

  return (
    <>
      <AppHeader subtitle="Профиль" />
      <main id="main" className={styles.main}>
        <h1 className={styles.title}>Профиль</h1>
        {needsAuth ? (
          <AuthNeeded next="/profile" title="Нужен вход" actionLabel="Войти снова">
            Сессия истекла или вы ещё не вошли. После входа вернёмся в профиль.
          </AuthNeeded>
        ) : (
        <>
        <p className={styles.hint}>
          Телефон нужен для входа по OTP. Email: <strong>{email || "—"}</strong>.
          {athleteId ? (
            <>
              {" "}
              Номер участника: <strong>{athleteId}</strong>.
            </>
          ) : null}{" "}
          <Link href="/events">К событиям</Link>
        </p>

        <form className={styles.form} onSubmit={onSubmit} noValidate>
          <div className={styles.field}>
            <label htmlFor="display_name">ФИО / имя</label>
            <input
              id="display_name"
              name="display_name"
              required
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              disabled={pending}
            />
          </div>

          <div className={styles.field}>
            <label htmlFor="phone">Телефон</label>
            <input
              id="phone"
              name="phone"
              type="tel"
              inputMode="tel"
              autoComplete="tel"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              disabled={pending}
              placeholder="+7 900 000-00-00"
            />
            <span className={styles.hint}>
              Чтобы сменить номер, введите полный телефон (+7…). Маску менять не нужно.
            </span>
          </div>

          {error ? (
            <p className={styles.error} role="alert">
              {error}
            </p>
          ) : null}
          {message ? (
            <p className={styles.hint} role="status">
              {message}
            </p>
          ) : null}

          <button type="submit" className={styles.submit} disabled={pending}>
            {pending ? "Сохраняем…" : "Сохранить"}
          </button>
        </form>

        {consents.length ? (
          <section className={styles.form} aria-labelledby="consents-title">
            <h2 id="consents-title" className={styles.title}>
              Согласия
            </h2>
            {consents.map((item) => (
              <div key={item.purpose} className={styles.checkboxRow}>
                <input
                  id={`consent-${item.purpose}`}
                  type="checkbox"
                  checked={item.granted}
                  disabled={item.required || consentBusy === item.purpose}
                  onChange={() => void onConsentToggle(item)}
                />
                <label htmlFor={`consent-${item.purpose}`}>
                  {item.title}
                  {item.required ? " (обязательное)" : ""}
                  .{" "}
                  <Link href={`/legal/${item.purpose}`} target="_blank" rel="noreferrer">
                    текст
                  </Link>
                </label>
              </div>
            ))}
          </section>
        ) : null}
        </>
        )}
      </main>
    </>
  );
}
