"use client";

import { FormEvent, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { AppHeader } from "@/components/AppHeader";
import { ApiError, registerAccount, saveSession } from "@/lib/api";
import { ROLE_LABELS, ROLES, type Role } from "@/lib/roles";
import styles from "../login/login.module.css";

const REQUESTABLE_ROLES = ROLES;

export default function RegisterPage() {
  const router = useRouter();
  const [phone, setPhone] = useState("");
  const [email, setEmail] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [role, setRole] = useState<Role>("participant");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loginHint, setLoginHint] = useState(false);
  const [pending, setPending] = useState(false);
  const [acceptTerms, setAcceptTerms] = useState(false);
  const [acceptPrivacy, setAcceptPrivacy] = useState(false);
  const [acceptPublishName, setAcceptPublishName] = useState(false);
  const [acceptAnalytics, setAcceptAnalytics] = useState(false);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setLoginHint(false);
    setMessage(null);
    setPending(true);
    try {
      const result = await registerAccount({
        phone: phone.trim(),
        email: email.trim(),
        display_name: displayName.trim(),
        requested_role: role,
        accept_terms: acceptTerms,
        accept_privacy: acceptPrivacy,
        accept_publish_name: acceptPublishName,
        accept_analytics: acceptAnalytics,
      });
      setMessage(result.message);
      if (result.access_token) {
        saveSession(result.access_token, {
          id: String(result.user_id),
          email: result.email,
          display_name: displayName.trim(),
          role: result.role,
          status: result.status,
          phone: result.phone,
        });
        router.replace("/events");
        return;
      }
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
        if (err.code === "email_taken" || err.code === "phone_taken") {
          setLoginHint(true);
        }
      } else {
        setError("Не удалось зарегистрироваться.");
      }
    } finally {
      setPending(false);
    }
  }

  return (
    <>
      <AppHeader subtitle="Регистрация" />
      <main id="main" className={styles.main}>
        <h1 className={styles.title}>Регистрация</h1>
        <p className={styles.hint}>
          Роль «Участник» подтверждается сразу. Остальные роли — после утверждения на
          y.valeev@gmail.com. Уже есть аккаунт? <Link href="/login">Войти</Link>
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
              placeholder="Иванов Иван"
            />
          </div>

          <div className={styles.field}>
            <label htmlFor="phone">Телефон</label>
            <input
              id="phone"
              name="phone"
              type="tel"
              required
              inputMode="tel"
              autoComplete="tel"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              disabled={pending}
              placeholder="+7 900 000-00-00"
            />
          </div>

          <div className={styles.field}>
            <label htmlFor="email">Email (для кода входа)</label>
            <input
              id="email"
              name="email"
              type="email"
              required
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              disabled={pending}
              placeholder="you@example.com"
            />
          </div>

          <div className={styles.field}>
            <label htmlFor="role">Запрашиваемая роль</label>
            <select
              id="role"
              name="role"
              value={role}
              onChange={(e) => setRole(e.target.value as Role)}
              disabled={pending}
            >
              {REQUESTABLE_ROLES.map((value) => (
                <option key={value} value={value}>
                  {ROLE_LABELS[value]}
                  {value === "participant" ? " (сразу)" : " (нужно утверждение)"}
                </option>
              ))}
            </select>
          </div>

          <div className={styles.checkboxRow}>
            <input
              id="accept_terms"
              type="checkbox"
              checked={acceptTerms}
              onChange={(e) => setAcceptTerms(e.target.checked)}
              disabled={pending}
            />
            <label htmlFor="accept_terms">
              Принимаю{" "}
              <Link href="/legal/terms_of_use" target="_blank" rel="noreferrer">
                пользовательское соглашение
              </Link>
            </label>
          </div>

          <div className={styles.checkboxRow}>
            <input
              id="accept_privacy"
              type="checkbox"
              checked={acceptPrivacy}
              onChange={(e) => setAcceptPrivacy(e.target.checked)}
              disabled={pending}
            />
            <label htmlFor="accept_privacy">
              Принимаю{" "}
              <Link href="/legal/privacy_policy" target="_blank" rel="noreferrer">
                политику конфиденциальности
              </Link>
            </label>
          </div>

          <div className={styles.checkboxRow}>
            <input
              id="accept_publish_name"
              type="checkbox"
              checked={acceptPublishName}
              onChange={(e) => setAcceptPublishName(e.target.checked)}
              disabled={pending}
            />
            <label htmlFor="accept_publish_name">
              Разрешаю публиковать ФИО и результаты в открытом списке события
            </label>
          </div>

          <div className={styles.checkboxRow}>
            <input
              id="accept_analytics"
              type="checkbox"
              checked={acceptAnalytics}
              onChange={(e) => setAcceptAnalytics(e.target.checked)}
              disabled={pending}
            />
            <label htmlFor="accept_analytics">Разрешаю продуктовую аналитику без телефона и документов</label>
          </div>

          {error ? (
            <p className={styles.error} role="alert">
              {error}
            </p>
          ) : null}
          {loginHint ? (
            <p className={styles.hint} role="status">
              Аккаунт уже есть — <Link href="/login">войдите по телефону</Link>.
            </p>
          ) : null}
          {message ? (
            <p className={styles.hint} role="status">
              {message}
            </p>
          ) : null}

          <button type="submit" className={styles.submit} disabled={pending}>
            {pending ? "Отправляем…" : "Зарегистрироваться"}
          </button>
        </form>
      </main>
    </>
  );
}
