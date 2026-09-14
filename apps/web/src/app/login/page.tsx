"use client";

import { FormEvent, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { AppHeader } from "@/components/AppHeader";
import {
  ApiError,
  devLogin,
  requestPhoneOtp,
  saveSession,
  verifyPhoneOtp,
} from "@/lib/api";
import { postLoginPath } from "@/lib/format";
import type { Role } from "@/lib/roles";
import styles from "./login.module.css";
import { Suspense } from "react";

function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const showDev =
    process.env.NODE_ENV === "development" && searchParams.get("dev") === "1";
  const [phone, setPhone] = useState("");
  const [code, setCode] = useState("");
  const [step, setStep] = useState<"phone" | "code">("phone");
  const [hint, setHint] = useState<string | null>(null);
  const [devOtp, setDevOtp] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  const nextPath = useMemo(
    () => postLoginPath(searchParams.get("next")),
    [searchParams],
  );

  async function onRequestOtp(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setHint(null);
    setDevOtp(null);
    setPending(true);
    try {
      const result = await requestPhoneOtp(phone.trim());
      setHint(result.message);
      if (result.dev_otp) setDevOtp(result.dev_otp);
      setStep("code");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Не удалось запросить код.");
    } finally {
      setPending(false);
    }
  }

  async function onVerify(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setPending(true);
    try {
      const result = await verifyPhoneOtp(phone.trim(), code.trim());
      saveSession(result.access_token, result.user);
      if (result.user.status === "pending_claim") {
        router.replace("/profile");
      } else {
        router.replace(nextPath);
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Неверный код. Если аккаунт ждёт подтверждения — дождитесь решения организатора.");
    } finally {
      setPending(false);
    }
  }

  async function onDevLogin(email: string, role: Role, displayName: string) {
    setError(null);
    setPending(true);
    try {
      const result = await devLogin({ email, role, display_name: displayName });
      saveSession(result.access_token, result.user);
      router.replace(nextPath);
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "Dev-login недоступен. Проверьте, что API запущен на :8000.",
      );
    } finally {
      setPending(false);
    }
  }

  return (
    <>
      <AppHeader subtitle="Вход по телефону" />
      <main id="main" className={styles.main}>
        <h1 className={styles.title}>Вход</h1>
        {searchParams.get("next") ? (
          <p className={styles.hint} role="status">
            После входа вернёмся к прерванному действию.
          </p>
        ) : null}
        <p className={styles.hint}>
          Введите номер телефона. Код отправим на email, привязанный к аккаунту (SMS подключим
          позже). Нет аккаунта? <Link href="/register">Создать</Link>
        </p>

        {step === "phone" ? (
          <form className={styles.form} onSubmit={onRequestOtp} noValidate>
            <div className={styles.field}>
              <label htmlFor="phone">Телефон</label>
              <input
                id="phone"
                name="phone"
                type="tel"
                autoComplete="tel"
                required
                inputMode="tel"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                placeholder="+7 900 000-00-00"
                disabled={pending}
              />
            </div>

            {error ? (
              <p className={styles.error} role="alert">
                {error}
              </p>
            ) : null}

            <button type="submit" className={styles.submit} disabled={pending}>
              {pending ? "Отправляем…" : "Получить код"}
            </button>
          </form>
        ) : (
          <form className={styles.form} onSubmit={onVerify} noValidate>
            <div className={styles.field}>
              <label htmlFor="code">Код из email</label>
              <input
                id="code"
                name="code"
                type="text"
                inputMode="numeric"
                autoComplete="one-time-code"
                required
                maxLength={6}
                value={code}
                onChange={(e) => setCode(e.target.value)}
                placeholder="6 цифр"
                disabled={pending}
              />
            </div>

            {hint ? <p className={styles.hint}>{hint}</p> : null}
            {devOtp ? (
              <p className={styles.hint} role="status">
                Код для разработки: <strong>{devOtp}</strong>
              </p>
            ) : null}

            {error ? (
              <p className={styles.error} role="alert">
                {error}
              </p>
            ) : null}

            <button type="submit" className={styles.submit} disabled={pending}>
              {pending ? "Проверяем…" : "Войти"}
            </button>
            <button
              type="button"
              className={styles.secondary}
              disabled={pending}
              onClick={() => {
                setStep("phone");
                setCode("");
                setError(null);
              }}
            >
              Изменить телефон
            </button>
          </form>
        )}

        {showDev ? (
          <div className={styles.form} style={{ marginTop: "2rem" }}>
            <p className={styles.hint} style={{ marginBottom: "0.75rem" }}>
              Локальная отладка (не показывается без ?dev=1):
            </p>
            <button
              type="button"
              className={styles.secondary}
              disabled={pending}
              onClick={() => void onDevLogin("organizer@example.com", "organizer", "Организатор (dev)")}
            >
              Войти как организатор
            </button>
            <button
              type="button"
              className={styles.secondary}
              disabled={pending}
              style={{ marginTop: "0.5rem" }}
              onClick={() => void onDevLogin("y.valeev@gmail.com", "platform_admin", "Владелец")}
            >
              Войти как admin
            </button>
            <button
              type="button"
              className={styles.secondary}
              disabled={pending}
              style={{ marginTop: "0.5rem" }}
              onClick={() => void onDevLogin("judge@example.com", "judge", "Судья (dev)")}
            >
              Войти как судья
            </button>
          </div>
        ) : null}
      </main>
    </>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={<p className={styles.hint}>Загрузка входа…</p>}>
      <LoginForm />
    </Suspense>
  );
}
