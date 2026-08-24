"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { AppHeader } from "@/components/AppHeader";
import { ApiError, createEvent, getStoredToken } from "@/lib/api";
import styles from "../../login/login.module.css";

function slugify(value: string): string {
  return value
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9а-яё]+/gi, "-")
    .replace(/[а-яё]/gi, "x")
    .replace(/-+/g, "-")
    .replace(/^-|-$/g, "")
    .slice(0, 64) || "event";
}

export default function NewEventPage() {
  const router = useRouter();
  const [title, setTitle] = useState("");
  const [slug, setSlug] = useState("");
  const [city, setCity] = useState("");
  const [description, setDescription] = useState("");
  const [disciplines, setDisciplines] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const token = getStoredToken();
    if (!token) {
      setError("Нужен вход организатора.");
      return;
    }
    setPending(true);
    setError(null);
    try {
      const created = await createEvent(token, {
        title: title.trim(),
        slug: (slug || slugify(title)).trim(),
        city: city.trim() || null,
        description: description.trim() || null,
        disciplines: disciplines.trim() || null,
        status: "draft",
      });
      router.replace(`/events/${created.id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Не удалось создать событие");
    } finally {
      setPending(false);
    }
  }

  return (
    <>
      <AppHeader subtitle="Новое событие" />
      <main id="main" className={styles.main}>
        <h1 className={styles.title}>Создать событие</h1>
        <p className={styles.hint}>
          Доступно ролям organizer+. Черновик можно опубликовать позже через API.{" "}
          <Link href="/events">Назад</Link>
        </p>
        <form className={styles.form} onSubmit={onSubmit} noValidate>
          <div className={styles.field}>
            <label htmlFor="title">Название</label>
            <input
              id="title"
              required
              value={title}
              onChange={(e) => {
                setTitle(e.target.value);
                if (!slug) setSlug(slugify(e.target.value));
              }}
              disabled={pending}
            />
          </div>
          <div className={styles.field}>
            <label htmlFor="slug">Slug (латиница-цифры-дефис)</label>
            <input
              id="slug"
              required
              pattern="^[a-z0-9]+(?:-[a-z0-9]+)*$"
              value={slug}
              onChange={(e) => setSlug(e.target.value)}
              disabled={pending}
            />
          </div>
          <div className={styles.field}>
            <label htmlFor="city">Город</label>
            <input id="city" value={city} onChange={(e) => setCity(e.target.value)} disabled={pending} />
          </div>
          <div className={styles.field}>
            <label htmlFor="disciplines">Дисциплины</label>
            <input
              id="disciplines"
              value={disciplines}
              onChange={(e) => setDisciplines(e.target.value)}
              disabled={pending}
            />
          </div>
          <div className={styles.field}>
            <label htmlFor="description">Описание</label>
            <input
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              disabled={pending}
            />
          </div>
          {error ? (
            <p className={styles.error} role="alert">
              {error}
            </p>
          ) : null}
          <button type="submit" className={styles.submit} disabled={pending}>
            {pending ? "Создаём…" : "Создать черновик"}
          </button>
        </form>
      </main>
    </>
  );
}
