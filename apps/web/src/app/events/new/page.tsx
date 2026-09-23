"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { AppHeader } from "@/components/AppHeader";
import { ApiError, RulesCatalog, createEvent, getRulesCatalog, getStoredToken, getStoredUser } from "@/lib/api";
import { isStaffRole } from "@/lib/roles";
import { AuthNeeded } from "@/components/AuthNeeded";
import styles from "../../login/login.module.css";

const CYR_TO_LAT: Record<string, string> = {
  а: "a",
  б: "b",
  в: "v",
  г: "g",
  д: "d",
  е: "e",
  ё: "e",
  ж: "zh",
  з: "z",
  и: "i",
  й: "y",
  к: "k",
  л: "l",
  м: "m",
  н: "n",
  о: "o",
  п: "p",
  р: "r",
  с: "s",
  т: "t",
  у: "u",
  ф: "f",
  х: "h",
  ц: "ts",
  ч: "ch",
  ш: "sh",
  щ: "sch",
  ъ: "",
  ы: "y",
  ь: "",
  э: "e",
  ю: "yu",
  я: "ya",
};

/** Технический код события для URL — только a-z, 0-9 и дефис. */
function slugify(value: string, yearHint?: string): string {
  const lowered = value.trim().toLowerCase();
  let out = "";
  for (const ch of lowered) {
    if (CYR_TO_LAT[ch] !== undefined) {
      out += CYR_TO_LAT[ch];
    } else if (/[a-z0-9]/.test(ch)) {
      out += ch;
    } else {
      out += "-";
    }
  }
  out = out.replace(/-+/g, "-").replace(/^-|-$/g, "").slice(0, 48);
  if (!out) out = "event";
  if (yearHint && /^\d{4}$/.test(yearHint) && !out.includes(yearHint)) {
    out = `${out}-${yearHint}`.slice(0, 64);
  }
  return out.replace(/-+/g, "-").replace(/^-|-$/g, "") || "event";
}

function dateToIsoStart(date: string): string {
  return `${date}T09:00:00`;
}

function dateToIsoEnd(date: string): string {
  return `${date}T21:00:00`;
}

function friendlyCreateError(err: unknown): string {
  if (!(err instanceof ApiError)) return "Не удалось создать событие";
  const msg = err.message || "";
  if (msg.includes("slug") || err.code === "slug_taken") {
    return "Событие с таким техническим кодом уже есть. Измените название или год в датах и попробуйте снова.";
  }
  if (err.status === 403) {
    return "Создавать события может организатор. Откройте список стартов и подайте заявку как участник — или запросите роль организатора.";
  }
  if (msg.includes("pattern") || msg.includes("body.")) {
    return "Проверьте поля формы: название, даты и дисциплины обязательны.";
  }
  return msg;
}

export default function NewEventPage() {
  const router = useRouter();
  const [catalog, setCatalog] = useState<RulesCatalog | null>(null);
  const [title, setTitle] = useState("");
  const [city, setCity] = useState("");
  const [startsOn, setStartsOn] = useState("");
  const [endsOn, setEndsOn] = useState("");
  const [description, setDescription] = useState("");
  const [selectedDisciplines, setSelectedDisciplines] = useState<string[]>([]);
  const [scoringMode, setScoringMode] = useState("photo_protocol");
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);
  const [gate, setGate] = useState<"loading" | "ok" | "auth" | "forbidden">("loading");

  useEffect(() => {
    const token = getStoredToken();
    const user = getStoredUser();
    if (!token || !user) {
      setGate("auth");
    } else if (!isStaffRole(user.role)) {
      setGate("forbidden");
    } else {
      setGate("ok");
    }
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

  const yearHint = startsOn.slice(0, 4);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const token = getStoredToken();
    if (!token) {
      setGate("auth");
      setError("Нужен вход организатора.");
      return;
    }
    const user = getStoredUser();
    if (!user || !isStaffRole(user.role)) {
      setGate("forbidden");
      return;
    }
    if (!title.trim()) {
      setError("Укажите название события.");
      return;
    }
    if (selectedDisciplines.length === 0) {
      setError("Выберите хотя бы одну дисциплину.");
      return;
    }
    if (!startsOn) {
      setError("Укажите дату начала.");
      return;
    }
    if (!endsOn) {
      setError("Укажите дату окончания.");
      return;
    }
    if (endsOn < startsOn) {
      setError("Дата окончания не может быть раньше даты начала.");
      return;
    }
    setPending(true);
    setError(null);
    try {
      const created = await createEvent(token, {
        title: title.trim(),
        slug: slugify(title, yearHint),
        city: city.trim() || null,
        description: description.trim() || null,
        starts_at: dateToIsoStart(startsOn),
        ends_at: dateToIsoEnd(endsOn),
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
      setError(friendlyCreateError(err));
    } finally {
      setPending(false);
    }
  }

  const disciplineEntries = catalog ? Object.entries(catalog.disciplines) : [];

  return (
    <>
      <AppHeader subtitle="Новое событие" />
      <main id="main" className={styles.main}>
        <h1 className={styles.title}>Создать событие</h1>
        {gate === "auth" ? (
          <AuthNeeded next="/events/new" title="Нужен вход организатора">
            Создавать соревнование может организатор или админ. После входа вернёмся к этой форме.
          </AuthNeeded>
        ) : null}
        {gate === "forbidden" ? (
          <div className="card" role="status">
            <strong>Эта роль не создаёт события</strong>
            <p className={styles.hint}>
              Участник, судья и комментатор работают внутри уже опубликованного старта. Откройте список
              событий и подайте заявку — или запросите роль организатора в «Доступах».
            </p>
            <p className={styles.hint}>
              <Link href="/events" className="btn btnPrimary">
                К списку событий
              </Link>
            </p>
          </div>
        ) : null}
        {gate === "ok" ? (
        <>
        <p className={styles.hint}>
          Черновик соревнования: название, даты, город, дисциплины. Правила по умолчанию — ФВВС, санкция
          международной федерации. <Link href="/events">Назад к списку</Link>
        </p>
        <form className={styles.form} onSubmit={onSubmit} noValidate>
          <div className={styles.field}>
            <label htmlFor="title">Название</label>
            <input
              id="title"
              required
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Например: Чемпионат России — Казань 2026"
              disabled={pending}
            />
            <p className={styles.fieldHint}>Код события создаётся автоматически.</p>
          </div>
          <div className={styles.field}>
            <label htmlFor="city">Город</label>
            <input
              id="city"
              value={city}
              onChange={(e) => setCity(e.target.value)}
              placeholder="Казань"
              disabled={pending}
            />
          </div>
          <div className={styles.field}>
            <label htmlFor="starts_on">Дата начала</label>
            <input
              id="starts_on"
              type="date"
              required
              value={startsOn}
              onChange={(e) => {
                const next = e.target.value;
                setStartsOn(next);
                if (!endsOn || endsOn < next) setEndsOn(next);
              }}
              disabled={pending}
            />
          </div>
          <div className={styles.field}>
            <label htmlFor="ends_on">Дата окончания</label>
            <p className={styles.fieldHint}>Если один день — укажите ту же дату.</p>
            <input
              id="ends_on"
              type="date"
              required
              min={startsOn || undefined}
              value={endsOn}
              onChange={(e) => setEndsOn(e.target.value)}
              disabled={pending}
            />
          </div>
          <fieldset className={styles.choiceList}>
            <legend>Дисциплины</legend>
            <p className={styles.fieldHint}>
              Отметьте галочками, какие виды будут на событии (можно несколько).
            </p>
            {disciplineEntries.length === 0 ? (
              <p className={styles.hint}>Загрузка каталога…</p>
            ) : (
              disciplineEntries.map(([code, meta]) => (
                <div key={code} className={styles.checkboxRow}>
                  <input
                    id={`discipline-${code}`}
                    type="checkbox"
                    checked={selectedDisciplines.includes(code)}
                    onChange={() => toggleDiscipline(code)}
                    disabled={pending}
                  />
                  <label htmlFor={`discipline-${code}`}>{meta.title_ru}</label>
                </div>
              ))
            )}
          </fieldset>
          <div className={styles.field}>
            <label htmlFor="scoring_mode">Как фиксируем результаты</label>
            <p className={styles.fieldHint}>
              Для старта удобнее «Фото протокола» — судья фотографирует лист, организатор проверяет.
            </p>
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
            <label htmlFor="description">Кратко о событии (необязательно)</label>
            <p className={styles.fieldHint}>
              Свободный текст для карточки: площадка, категории, примечание. Можно оставить пустым.
            </p>
            <textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder={"Например:\nоз. Кабан\nЮниоры до 19\nОткрытая группа"}
              disabled={pending}
              rows={4}
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
        </>
        ) : null}
      </main>
    </>
  );
}
