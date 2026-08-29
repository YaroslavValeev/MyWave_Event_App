import Link from "next/link";
import { loginHref } from "@/lib/format";

type AuthNeededProps = {
  next: string;
  title?: string;
  actionLabel?: string;
  children: React.ReactNode;
};

/** Закрывает тупик: нет сессии / истекла — понятный CTA на вход с возвратом. */
export function AuthNeeded({
  next,
  title = "Нужен вход",
  actionLabel = "Войти",
  children,
}: AuthNeededProps) {
  return (
    <div className="card" role="status">
      <strong>{title}</strong>
      <p style={{ margin: "0.5rem 0 0.85rem", color: "var(--mist)" }}>{children}</p>
      <Link href={loginHref(next)} className="btn btnPrimary">
        {actionLabel}
      </Link>
    </div>
  );
}
