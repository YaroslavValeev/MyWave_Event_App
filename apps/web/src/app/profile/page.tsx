"use client";

import { FormEvent, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { AppHeader } from "@/components/AppHeader";
import {
  ApiError,
  clearSession,
  confirmAthleteLink,
  fetchMe,
  fetchMyConsents,
  getStoredToken,
  grantMyConsent,
  listAthleteLinks,
  rejectAthleteLink,
  revokeMyConsent,
  saveSession,
  updateMyProfile,
  type AthleteLinkOut,
  type ConsentItem,
  type UserOut,
} from "@/lib/api";
import { AuthNeeded } from "@/components/AuthNeeded";
import styles from "../login/login.module.css";

export default function ProfilePage() {
  const router = useRouter();
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
  const [links, setLinks] = useState<AthleteLinkOut[]>([]);
  const [linkBusy, setLinkBusy] = useState<number | null>(null);

  function onLogout() {
    clearSession();
    router.push("/");
  }

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
    void listAthleteLinks(token)
      .then((payload) => setLinks(payload.items))
      .catch(() => {
        setLinks([]);
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

  async function onLink(link: AthleteLinkOut, action: "confirm" | "reject") {
    const token = getStoredToken();
    if (!token) return;
    setLinkBusy(link.id);
    setError(null);
    try {
      const updated =
        action === "confirm"
          ? await confirmAthleteLink(token, link.id)
          : await rejectAthleteLink(token, link.id);
      setLinks((current) => current.map((row) => (row.id === updated.id ? updated : row)));
      const me = await fetchMe(token);
      setAthleteId(me.athlete_id || null);
      setMessage(
        action === "confirm"
          ? "Профиль спортсмена подтверждён."
          : "Предполагаемая связь отклонена. Организатор увидит спорный случай в аудите.",
      );
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Не удалось обновить связь.");
    } finally {
      setLinkBusy(null);
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

        <p style={{ marginTop: "1.25rem" }}>
          <button type="button" className={styles.secondary} onClick={onLogout}>
            Выйти из аккаунта
          </button>
        </p>

        {links.length ? (
          <section className={styles.form} aria-labelledby="links-title">
            <h2 id="links-title" className={styles.title}>
              Связь со спортсменом
            </h2>
            <p className={styles.hint}>
              Подтвердите свой профиль. Если на одном телефоне несколько спортсменов — выберите
              нужных. Чужой профиль подтверждать нельзя.
            </p>
            {links.map((link) => (
              <div key={link.id} className={styles.field}>
                <strong>
                  {link.display_name} · {link.athlete_id}
                </strong>
                <span className={styles.hint}>
                  {link.relation === "self" ? "Свой профиль" : link.relation}. Статус: {link.status}
                  {link.region ? ` · ${link.region}` : ""}
                </span>
                {link.status === "pending_claim" ? (
                  <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
                    <button
                      type="button"
                      className={styles.submit}
                      disabled={linkBusy === link.id}
                      onClick={() => void onLink(link, "confirm")}
                    >
                      Это я
                    </button>
                    <button
                      type="button"
                      className={styles.submit}
                      disabled={linkBusy === link.id}
                      onClick={() => void onLink(link, "reject")}
                    >
                      Это не я
                    </button>
                  </div>
                ) : null}
              </div>
            ))}
          </section>
        ) : null}

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
