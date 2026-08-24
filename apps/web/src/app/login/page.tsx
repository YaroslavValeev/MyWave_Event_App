"use client";

import { FormEvent, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { AppHeader } from "@/components/AppHeader";
import {
  ApiError,
  requestPhoneOtp,
  saveSession,
  verifyPhoneOtp,
} from "@/lib/api";
import styles from "./login.module.css";

export default function LoginPage() {
  const router = useRouter();
  const [phone, setPhone] = useState("");
  const [code, setCode] = useState("");
  const [step, setStep] = useState<"phone" | "code">("phone");
  const [hint, setHint] = useState<string | null>(null);
  const [devOtp, setDevOtp] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

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
      router.replace("/events");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Неверный код или аккаунт не активен.");
    } finally {
      setPending(false);
    }
  }

  return (
    <>
      <AppHeader subtitle="Вход по телефону" />
      <main id="main" className={styles.main}>
        <h1 className={styles.title}>Вход</h1>
        <p className={styles.hint}>
          Войдите по номеру телефона. Код придёт на email аккаунта (SMS подключим позже).
          Нет аккаунта? <Link href="/register">Зарегистрироваться</Link>
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
              <label htmlFor="code">Код из письма</label>
              <input
                id="code"
                name="code"
                type="text"
                inputMode="numeric"
                autoComplete="one-time-code"
                required
                value={code}
                onChange={(e) => setCode(e.target.value)}
                placeholder="6 цифр"
                disabled={pending}
              />
            </div>

            {hint ? <p className={styles.hint}>{hint}</p> : null}
            {devOtp ? (
              <p className={styles.hint} role="status">
                Dev-код: <strong>{devOtp}</strong>
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
      </main>
    </>
  );
}
