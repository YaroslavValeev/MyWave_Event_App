"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { AppHeader } from "@/components/AppHeader";
import { ApiError, RulesCatalog, createEvent, getRulesCatalog, getStoredToken } from "@/lib/api";
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
  const [catalog, setCatalog] = useState<RulesCatalog | null>(null);
  const [title, setTitle] = useState("");
  const [slug, setSlug] = useState("");
  const [city, setCity] = useState("");
  const [description, setDescription] = useState("");
  const [selectedDisciplines, setSelectedDisciplines] = useState<string[]>([]);
  const [scoringMode, setScoringMode] = useState("photo_protocol");
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  useEffect(() => {
    getRulesCatalog()
      .then((data) => {
        setCatalog(data);
        setScoringMode(data.defaults.scoring_mode);
        setSelectedDisciplines(data.p0_discipline_codes.slice(0, 1));
      })
      .catch(() => setCatalog(null));
  }, []);

  function toggleDiscipline(code: string) {
    setSelectedDisciplines((prev) =>
      prev.includes(code) ? prev.filter((c) => c !== code) : [...prev, code],
    );
  }

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const token = getStoredToken();
    if (!token) {
      setError("Нужен вход организатора.");
      return;
    }
    if (selectedDisciplines.length === 0) {
      setError("Выберите хотя бы одну дисциплину.");
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
        status: "draft",
        rules_profile: {
          governing_body: catalog?.defaults.governing_body ?? "FVLS",
          sanction_body: catalog?.defaults.sanction_body ?? "IWWF",
          discipline_codes: selectedDisciplines,
          scoring_mode: scoringMode,
        },
      });
      router.replace(`/events/${created.id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Не удалось создать событие");
    } finally {
      setPending(false);
    }
  }

  const disciplineEntries = catalog
    ? Object.entries(catalog.disciplines)
    : [];

  return (
    <>
      <AppHeader subtitle="Новое событие" />
      <main id="main" className={styles.main}>
        <h1 className={styles.title}>Создать событие</h1>
        <p className={styles.hint}>
          FVLS + санкция IWWF. Выберите дисциплины и режим протокола.{" "}
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
          <fieldset className={styles.field}>
            <legend>Дисциплины (P0)</legend>
            {disciplineEntries.length === 0 ? (
              <p className={styles.hint}>Загрузка каталога…</p>
            ) : (
              disciplineEntries.map(([code, meta]) => (
                <label key={code} style={{ display: "block", marginBottom: "0.35rem" }}>
                  <input
                    type="checkbox"
                    checked={selectedDisciplines.includes(code)}
                    onChange={() => toggleDiscipline(code)}
                    disabled={pending}
                  />{" "}
                  {meta.title_ru}
                </label>
              ))
            )}
          </fieldset>
          <div className={styles.field}>
            <label htmlFor="scoring_mode">Режим протокола</label>
            <select
              id="scoring_mode"
              value={scoringMode}
              onChange={(e) => setScoringMode(e.target.value)}
              disabled={pending || !catalog}
            >
              {catalog
                ? Object.entries(catalog.scoring_modes).map(([code, meta]) => (
                    <option key={code} value={code}>
                      {meta.title_ru}
                    </option>
                  ))
                : null}
            </select>
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
