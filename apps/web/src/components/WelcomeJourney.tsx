"use client";

import Link from "next/link";
import { useEffect, useMemo, useState, type ReactNode } from "react";
import { getStoredToken, getStoredUser, listEvents, type EventOut } from "@/lib/api";
import { formatEventPeriod, loginHref } from "@/lib/format";
import { isStaffRole, EVENT_STATUS_LABELS, type EventStatus } from "@/lib/roles";
import styles from "./WelcomeJourney.module.css";

type Goal = "spectator" | "participant" | "judge" | "organizer" | "media";
type Phase = "welcome" | "event" | "organization" | "review";
type OrganizeMode = "create" | "existing";
type IconName = "eye" | "medal" | "scale" | "calendar" | "camera" | "arrow" | "chevron" | "check" | "info" | "user" | "file" | "shield" | "clock";

const GOALS: ReadonlyArray<{
  id: Goal;
  title: string;
  description: string;
  icon: IconName;
  needed: readonly string[];
  nextStep: string;
}> = [
  {
    id: "spectator", title: "Смотреть соревнования",
    description: "Расписание, новости и результаты — без регистрации.", icon: "eye",
    needed: ["Выбрать мероприятие", "Открыть программу, ленту или табло"],
    nextStep: "На странице мероприятия откройте «Табло», «Результаты» или «Ленту»."
  },
  {
    id: "participant", title: "Участвовать",
    description: "Подать заявку и следить за своим стартом.", icon: "medal",
    needed: ["Войти или зарегистрироваться", "Выбрать мероприятие и категорию", "Проверить сведения профиля и необходимые согласия", "Отправить заявку и дождаться решения организатора"],
    nextStep: "На странице мероприятия откройте «Заявки». Выберите категорию и заполните отмеченные поля."
  },
  {
    id: "judge", title: "Работать судьёй",
    description: "Открыть назначенный старт и внести оценки.", icon: "scale",
    needed: ["Войти с подтверждённым назначением судьи", "Выбрать своё мероприятие и заезд", "Выбрать участника и заполнить критерии", "Сохранить оценку и проверить подтверждение сервера"],
    nextStep: "На странице мероприятия откройте «Судейство». Доступные действия определяются назначением и правилами соревнования."
  },
  {
    id: "organizer", title: "Организовать мероприятие",
    description: "Создать событие или продолжить подготовку.", icon: "calendar",
    needed: ["Войти с подтверждёнными полномочиями", "Указать название, место и даты нового события — если создаёте его", "Проверить категории, документы, роли и заявки", "Перейти к следующему пункту чек-листа"],
    nextStep: "На странице мероприятия используйте «Что делать дальше?». Новое событие создаётся через отдельную форму."
  },
  {
    id: "media", title: "Опубликовать материал",
    description: "Фото, новость или пост о мероприятии.", icon: "camera",
    needed: ["Войти и проверить доступную роль автора", "Выбрать мероприятие", "Заполнить заголовок и текст; при необходимости добавить фото", "Проверить публикацию и отправить на публикацию или модерацию"],
    nextStep: "На странице мероприятия откройте «Ленту события» и заполните редактор. Публикация доступна только уполномоченным ролям."
  }
];

const ICON_PATH: Record<IconName, ReactNode> = {
  eye: <><path d="M2 12s3.5-6 10-6 10 6 10 6-3.5 6-10 6S2 12 2 12Z"/><circle cx="12" cy="12" r="2.5"/></>,
  medal: <><path d="m7 2 5 8 5-8M5 2l5 8m9-8-5 8"/><circle cx="12" cy="15" r="5"/><path d="m10 15 1.5 1.5L14 14"/></>,
  scale: <><path d="M12 3v18M4 7h16M5 7l-3 7h6L5 7Zm14 0-3 7h6l-3-7ZM8 21h8"/></>,
  calendar: <><rect x="3" y="5" width="18" height="16" rx="2"/><path d="M7 3v4m10-4v4M3 10h18m-13 5h3m3 0h3"/></>,
  camera: <><path d="M3 7h4l2-3h6l2 3h4v13H3V7Z"/><circle cx="12" cy="13" r="4"/></>,
  arrow: <><path d="M5 12h14m-6-6 6 6-6 6"/></>,
  chevron: <><path d="m9 18 6-6-6-6"/></>,
  check: <><path d="m4 12 5 5L20 6"/></>,
  info: <><circle cx="12" cy="12" r="10"/><path d="M12 11v6m0-10h.01"/></>,
  user: <><circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/></>,
  file: <><path d="M5 3h9l5 5v13H5V3Zm9 0v5h5M8 13h8M8 17h8"/></>,
  shield: <><path d="m12 2 8 4v6c0 5-3.5 8.5-8 10-4.5-1.5-8-5-8-10V6l8-4Z"/><path d="m9 12 2 2 4-4"/></>,
  clock: <><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 3"/></>
};

function Icon({ name, size = 23 }: { name: IconName; size?: number }) {
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{ICON_PATH[name]}</svg>;
}

export function WelcomeJourney() {
  const [phase, setPhase] = useState<Phase>("welcome");
  const [goal, setGoal] = useState<Goal | null>(null);
  const [mode, setMode] = useState<OrganizeMode>("existing");
  const [eventId, setEventId] = useState<string>("");
  const [events, setEvents] = useState<EventOut[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [fetchError, setFetchError] = useState("");
  const [fieldError, setFieldError] = useState("");
  const [user, setUser] = useState<ReturnType<typeof getStoredUser>>(null);
  const currentGoal = GOALS.find((g) => g.id === goal) ?? null;
  const selectedEvent = useMemo(() => events.find((e) => String(e.id) === eventId), [eventId, events]);

  useEffect(() => {
    let cancelled = false;
    setUser(getStoredUser());
    listEvents(getStoredToken())
      .catch(() => listEvents())
      .then((list) => { if (!cancelled) setEvents(Array.isArray(list) ? list : []); })
      .catch(() => { if (!cancelled) setFetchError("Не удалось загрузить список мероприятий. Проверьте соединение и попробуйте ещё раз."); })
      .finally(() => { if (!cancelled) setIsLoading(false); });
    return () => { cancelled = true; };
  }, []);

  function selectGoal(next: Goal) {
    setGoal(next);
    setFieldError("");
    setEventId("");
    setMode("existing");
    setPhase(next === "organizer" ? "organization" : "event");
  }

  function moveForward() {
    if (phase === "organization") {
      setFieldError("");
      setPhase(mode === "create" ? "review" : "event");
      return;
    }
    if (phase === "event") {
      if (!eventId) { setFieldError("Сначала выберите мероприятие, чтобы продолжить."); return; }
      setFieldError("");
      setPhase("review");
    }
  }

  function back() {
    setFieldError("");
    if (phase === "review") setPhase(goal === "organizer" && mode === "create" ? "organization" : "event");
    else if (phase === "event" && goal === "organizer") setPhase("organization");
    else setPhase("welcome");
  }

  const wantsNewEvent = goal === "organizer" && mode === "create";
  const targetHref = wantsNewEvent
    ? "/events/new"
    : selectedEvent
      ? `/events/${selectedEvent.id}`
      : "/events";
  const canCreate = Boolean(user && isStaffRole(user.role));
  const requiresAuth = goal !== "spectator";
  // Role choice never grants permissions — login/staff gates stay on existing pages/API.
  const finalHref = !requiresAuth || user ? targetHref : loginHref(targetHref);
  const finalText = !requiresAuth
    ? "Открыть мероприятие"
    : !user
      ? "Войти и продолжить"
      : wantsNewEvent && !canCreate
        ? "Посмотреть мероприятия"
        : wantsNewEvent
          ? "Создать мероприятие"
          : "Открыть мероприятие";
  const authorizedHref = wantsNewEvent && user && !canCreate ? "/events" : finalHref;

  return (
    <div className={styles.layout}>
      <div className={styles.main}>
        {phase === "welcome" ? (
          <>
            <section className={styles.hero}>
              <div className={styles.kicker}>MYWAVE EVENT · CHAMP APP</div>
              <h1>Добро пожаловать.<br/><span>Что вы хотите сделать?</span></h1>
              <p>Выберите задачу — приложение покажет следующий шаг и объяснит, какие сведения потребуется заполнить.</p>
            </section>
            <div className={styles.sectionHead}><div><h2>Начните с вашей цели</h2><p>Не нужно разбираться во всех разделах заранее.</p></div><span className={styles.stepCount}>Шаг 1 из 3</span></div>
            <div className={styles.goalGrid}>
              {GOALS.map((g) => (
                <button key={g.id} type="button" className={styles.goalCard} onClick={() => selectGoal(g.id)}>
                  <span className={styles.goalIcon}><Icon name={g.icon} /></span>
                  <span className={styles.goalWords}><strong>{g.title}</strong><small>{g.description}</small></span>
                  <span className={styles.goalArrow}><Icon name="chevron" size={20}/></span>
                </button>
              ))}
            </div>
            <p className={styles.footNote}>Выбор задачи не меняет ваши права доступа. Действия с соревнованием подтверждаются сервером.</p>
            <Link href="/events" className={styles.simpleLink}>Перейти сразу к списку мероприятий <Icon name="arrow" size={16}/></Link>
          </>
        ) : (
          <>
            <div className={styles.crumbs}><button type="button" onClick={back} className={styles.back}>← Назад</button><span>{currentGoal?.title}</span><span className={styles.stepCount}>{phase === "review" ? "Шаг 3 из 3" : "Шаг 2 из 3"}</span></div>
            <div className={styles.progress} aria-hidden="true"><div style={{ width: phase === "review" ? "100%" : "66.7%" }}/></div>
            <section className={styles.panel} aria-labelledby="journey-title">
              {phase === "organization" ? (
                <>
                  <div className={styles.kicker}>ОРГАНИЗАЦИЯ</div><h1 id="journey-title">С чего вы хотите начать?</h1>
                  <p className={styles.explain}>Выберите одно действие. Все остальные настройки появятся в нужное время.</p>
                  <div className={styles.optionList} role="radiogroup" aria-label="Как начать организацию">
                    {([{ id: "create", title: "Создать новое мероприятие", desc: "Название, даты и место будут в следующей форме.", icon: "calendar" }, { id: "existing", title: "Продолжить подготовку", desc: "Выберите мероприятие, чтобы увидеть его задачи.", icon: "check" }] as const).map((option) => (
                      <button key={option.id} type="button" role="radio" aria-checked={mode === option.id} className={`${styles.option} ${mode === option.id ? styles.selected : ""}`} onClick={() => setMode(option.id)}>
                        <span className={styles.goalIcon}><Icon name={option.icon}/></span><span><strong>{option.title}</strong><small>{option.desc}</small></span><span className={styles.radioMarker}>{mode === option.id ? "●" : "○"}</span>
                      </button>
                    ))}
                  </div>
                </>
              ) : null}
              {phase === "event" ? (
                <>
                  <div className={styles.kicker}>ВЫБОР СОБЫТИЯ</div><h1 id="journey-title">Какое мероприятие вас интересует?</h1>
                  <p className={styles.explain}>Это обязательный шаг. Выберите событие, чтобы видеть только относящиеся к нему действия.</p>
                  {isLoading ? <p role="status">Загружаем мероприятия…</p> : null}
                  {fetchError ? <div className={styles.error} role="alert">{fetchError} <Link href="/events">Открыть список</Link></div> : null}
                  {!isLoading && !fetchError && events.length === 0 ? <div className={styles.empty}>Доступных мероприятий пока нет. <Link href="/events">Проверить список событий</Link></div> : null}
                  <div className={styles.optionList} role="radiogroup" aria-label="Мероприятие" aria-describedby={fieldError ? "event-choice-error" : undefined}>
                    {events.map((ev) => (
                      <button key={ev.id} type="button" role="radio" aria-checked={eventId === String(ev.id)} className={`${styles.option} ${eventId === String(ev.id) ? styles.selected : ""}`} onClick={() => { setEventId(String(ev.id)); setFieldError(""); }}>
                        <span className={styles.goalIcon}><Icon name="calendar"/></span><span><strong>{ev.title}</strong><small>{ev.city || "Место уточняется"} · {formatEventPeriod(ev.starts_at, ev.ends_at)}</small></span><span className={styles.status}>{EVENT_STATUS_LABELS[ev.status as EventStatus] ?? ev.status}</span>
                      </button>
                    ))}
                  </div>
                  {fieldError ? <p id="event-choice-error" role="alert" className={styles.error}>{fieldError}</p> : null}
                </>
              ) : null}
              {phase === "review" && currentGoal ? (
                <>
                  <div className={styles.kicker}>ВАШ СЛЕДУЮЩИЙ ШАГ</div><h1 id="journey-title">Вы готовы продолжить</h1>
                  <p className={styles.explain}>Подскажем, что понадобится на следующем экране. Ничего пока не отправлено.</p>
                  <div className={styles.summary}>
                    <div><span>Цель</span><strong>{currentGoal.title}</strong></div>
                    <div><span>Мероприятие</span><strong>{wantsNewEvent ? "Новое мероприятие" : selectedEvent?.title ?? "Не выбрано"}</strong></div>
                  </div>
                  <h2 className={styles.h3}>Что нужно будет сделать</h2>
                  <ol className={styles.checkList}>{currentGoal.needed.map((task) => <li key={task}><span><Icon name="check" size={16}/></span>{task}</li>)}</ol>
                  <div className={styles.nextHint}><Icon name="info" size={20}/><p>{currentGoal.nextStep}</p></div>
                  {wantsNewEvent && user && !canCreate ? <div className={styles.warn} role="status"><Icon name="shield" size={20}/><span>У текущей учётной записи нет подтверждённых прав создания мероприятий. Запросите доступ у администратора. Просмотр событий остаётся доступен.</span></div> : null}
                  {requiresAuth && !user ? <div className={styles.nextHint}><Icon name="user" size={20}/><p>Для продолжения понадобится вход. Если у вас нет аккаунта, <Link href="/register">создайте его</Link>. Судейские, медиа- и организаторские права подтверждаются отдельно.</p></div> : null}
                </>
              ) : null}
              <div className={styles.actions}>
                <button type="button" className={styles.secondary} onClick={back}>Назад</button>
                {phase === "review" ? <Link className={styles.primary} href={authorizedHref}>{finalText} <Icon name="arrow" size={17}/></Link> : <button type="button" className={styles.primary} onClick={moveForward}>Продолжить <Icon name="arrow" size={17}/></button>}
              </div>
            </section>
            <div className={styles.changeGoal}><button type="button" onClick={() => { setPhase("welcome"); setFieldError(""); }}>Изменить задачу</button></div>
          </>
        )}
      </div>
      <aside className={styles.aside} aria-label="О сервисе">
        <div className={styles.asideBox}><div className={styles.asideIcon}><Icon name="clock"/></div><h2>Каждое действие — на своём месте</h2><p>Champ App объединяет заявки, судейство, публикации и результаты. Сначала вы выбираете цель, затем система объясняет следующий шаг.</p></div>
        <div className={styles.asideBox}><strong>Как это работает</strong><ol><li>Выберите задачу</li><li>Укажите мероприятие</li><li>Перейдите к нужному действию</li></ol><p>Необязательные разделы не мешают основному маршруту.</p></div>
      </aside>
    </div>
  );
}
