"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { AppHeader } from "@/components/AppHeader";
import {
  ApiError,
  devLogin,
  getLoginOptions,
  loginByKnownPhone,
  requestPhoneOtp,
  saveSession,
  verifyPhoneOtp,
  type TokenResponse,
} from "@/lib/api";
import { postLoginPath } from "@/lib/format";
import type { Role } from "@/lib/roles";
import styles from "./login.module.css";
import { Suspense } from "react";

const OTP_FALLBACK_HINT =
  "Код подтверждения придёт на почту, привязанную к аккаунту. Сообщения на телефон пока не подключены.";

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
  const [optionsLoaded, setOptionsLoaded] = useState(false);
  const [otpRequired, setOtpRequired] = useState(true);
  const [modeMessage, setModeMessage] = useState(OTP_FALLBACK_HINT);

  const nextPath = useMemo(
    () => postLoginPath(searchParams.get("next")),
    [searchParams],
  );

  useEffect(() => {
    let cancelled = false;
    void (async () => {
      try {
        const options = await getLoginOptions();
        if (cancelled) return;
        setOtpRequired(options.otp_required);
        setModeMessage(options.message);
      } catch {
        if (cancelled) return;
        setOtpRequired(true);
        setModeMessage(OTP_FALLBACK_HINT);
      } finally {
        if (!cancelled) setOptionsLoaded(true);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  function finishLogin(result: TokenResponse) {
    saveSession(result.access_token, result.user);
    if (result.user.status === "pending_claim") {
      router.replace("/profile");
    } else {
      router.replace(nextPath);
    }
  }

  async function onPhoneLogin(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setPending(true);
    try {
      const result = await loginByKnownPhone(phone.trim());
      finishLogin(result);
    } catch (err) {
      if (err instanceof ApiError && err.status === 404) {
        setError("Этот номер ещё не в системе. Сначала создайте аккаунт.");
      } else {
        setError(err instanceof ApiError ? err.message : "Не удалось войти.");
      }
    } finally {
      setPending(false);
    }
  }

  async function onRequestOtp(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setHint(null);
    setDevOtp(null);
    setPending(true);
    try {
      const result = await requestPhoneOtp(phone.trim());
      setHint(
        result.email_masked
          ? `Код отправлен на ${result.email_masked}. Действует ${Math.round(result.expires_in_seconds / 60)} мин.`
          : result.message,
      );
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
      finishLogin(result);
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "Неверный код. Запросите новый — действует только последний код (до 10 минут).",
      );
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
          : "Не удалось войти в режиме отладки. Попробуйте позже.",
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
        {!optionsLoaded ? (
          <p className={styles.hint}>Загрузка входа…</p>
        ) : (
          <p className={styles.hint}>
            {modeMessage} Нет аккаунта? <Link href="/register">Создать</Link>
          </p>
        )}

        {optionsLoaded && !otpRequired ? (
          <form className={styles.form} onSubmit={onPhoneLogin} noValidate>
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
            <p className={styles.hint}>
              Код и пароль не нужны, пока не настроена почтовая доставка. Роль уже
              привязана к этому номеру в аккаунте.
            </p>

            {error ? (
              <p className={styles.error} role="alert">
                {error}
                {error.includes("ещё не в системе") ? (
                  <>
                    {" "}
                    <Link href="/register">Регистрация</Link>
                  </>
                ) : null}
              </p>
            ) : null}

            <button type="submit" className={styles.submit} disabled={pending}>
              {pending ? "Входим…" : "Войти"}
            </button>
          </form>
        ) : null}

        {optionsLoaded && otpRequired && step === "phone" ? (
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
        ) : null}

        {optionsLoaded && otpRequired && step === "code" ? (
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
        ) : null}

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
