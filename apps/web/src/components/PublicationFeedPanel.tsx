"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  ApiError,
  PublicationMediaOut,
  PublicationOut,
  PublicationType,
  createPublication,
  getStoredToken,
  getStoredUser,
  listPublicationAuthorRoles,
  listPublications,
  moderatePublication,
  publicationMediaUrl,
  uploadPublicationMedia,
} from "@/lib/api";
import {
  LocalPublicationDraft,
  listPublicationDrafts,
  removePublicationDraft,
  savePublicationDraft,
} from "@/lib/publicationDrafts";
import { ROLE_LABELS, Role, isBroadcastRole, isStaffRole } from "@/lib/roles";
import styles from "./PublicationFeedPanel.module.css";

type Props = {
  eventId: string;
  isArchived?: boolean;
};

const STATUS_LABELS: Record<PublicationOut["status"], string> = {
  draft: "Черновик",
  pending_moderation: "На модерации",
  published: "Опубликовано",
  rejected: "Отклонено",
  void: "Аннулировано",
};

function roleLabel(role: string): string {
  return ROLE_LABELS[role as Role] ?? role;
}

function readFileAsDataUrl(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result));
    reader.onerror = () => reject(reader.error);
    reader.readAsDataURL(file);
  });
}

function dataUrlToFile(dataUrl: string, name: string): File {
  const [meta, encoded] = dataUrl.split(",");
  const mime = meta.match(/data:([^;]+)/)?.[1] ?? "image/jpeg";
  const bytes = atob(encoded);
  const buffer = new Uint8Array(bytes.length);
  for (let index = 0; index < bytes.length; index += 1) buffer[index] = bytes.charCodeAt(index);
  return new File([buffer], name, { type: mime });
}

function PublicationImage({
  eventId,
  publicationId,
  media,
}: {
  eventId: string;
  publicationId: number;
  media: PublicationMediaOut;
}) {
  const [src, setSrc] = useState("");

  useEffect(() => {
    const controller = new AbortController();
    let objectUrl = "";
    async function load() {
      const token = getStoredToken();
      const response = await fetch(publicationMediaUrl(media.download_path), {
        headers: token ? { Authorization: `Bearer ${token}` } : undefined,
        signal: controller.signal,
      });
      if (!response.ok) return;
      objectUrl = URL.createObjectURL(await response.blob());
      setSrc(objectUrl);
    }
    void load();
    return () => {
      controller.abort();
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [eventId, media.download_path, publicationId]);

  return src ? (
    <img className={styles.publicationImage} src={src} alt={media.file_name} />
  ) : null;
}

export function PublicationFeedPanel({ eventId, isArchived = false }: Props) {
  const user = getStoredUser();
  const canCreate = Boolean(user && (isStaffRole(user.role) || isBroadcastRole(user.role)));
  const canModerate = Boolean(user && isStaffRole(user.role));
  const allowedTypes = useMemo<PublicationType[]>(
    () => (user && isStaffRole(user.role) ? ["post", "news"] : ["post"]),
    [user],
  );

  const [publications, setPublications] = useState<PublicationOut[]>([]);
  const [authorRoles, setAuthorRoles] = useState<string[]>([]);
  const [localDrafts, setLocalDrafts] = useState<LocalPublicationDraft[]>([]);
  const [type, setType] = useState<PublicationType>("post");
  const [authorRole, setAuthorRole] = useState(user?.role ?? "");
  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");
  const [image, setImage] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState("");
  const [activeDraftId, setActiveDraftId] = useState<string | undefined>();
  const [previewOpen, setPreviewOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [offlineBanner, setOfflineBanner] = useState(false);
  const [loaded, setLoaded] = useState(false);

  const refresh = useCallback(async () => {
    const token = getStoredToken();
    try {
      const [items, roles] = await Promise.all([
        listPublications(token, eventId),
        token && canCreate ? listPublicationAuthorRoles(token, eventId) : Promise.resolve([]),
      ]);
      setPublications(items);
      setAuthorRoles(roles);
      if (roles.length > 0) setAuthorRole((current) => current || roles[0]);
      setError(null);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Не удалось загрузить ленту");
    } finally {
      setLoaded(true);
    }
  }, [canCreate, eventId]);

  useEffect(() => {
    setLocalDrafts(listPublicationDrafts(eventId));
    void refresh();
  }, [eventId, refresh]);

  useEffect(() => {
    if (!image) {
      setImagePreview("");
      return;
    }
    const url = URL.createObjectURL(image);
    setImagePreview(url);
    return () => URL.revokeObjectURL(url);
  }, [image]);

  function resetForm() {
    setTitle("");
    setBody("");
    setType("post");
    setImage(null);
    setActiveDraftId(undefined);
    setPreviewOpen(false);
  }

  async function saveOffline(status: "draft" | "queued") {
    try {
      const saved = savePublicationDraft(eventId, {
        id: activeDraftId,
        title: title.trim(),
        body: body.trim(),
        type,
        authorRole,
        imageDataUrl: image ? await readFileAsDataUrl(image) : undefined,
        imageName: image?.name,
        status,
      });
      setActiveDraftId(saved.id);
      setLocalDrafts(listPublicationDrafts(eventId));
      setOfflineBanner(true);
      setMessage(null);
      setError(null);
    } catch {
      setError("Не удалось сохранить локальный черновик. Возможно, хранилище браузера заполнено.");
    }
  }

  async function submit(intent: "draft" | "publish") {
    if (!title.trim()) {
      setError("Добавьте заголовок публикации.");
      return;
    }
    if (!navigator.onLine) {
      await saveOffline(intent === "publish" ? "queued" : "draft");
      return;
    }
    const token = getStoredToken();
    if (!token || !canCreate) {
      setError("Войдите с ролью автора публикаций.");
      return;
    }
    setBusy(true);
    setMessage(null);
    setError(null);
    setOfflineBanner(false);
    try {
      const idempotencyKey = crypto.randomUUID();
      let created = await createPublication(token, eventId, {
        type,
        title: title.trim(),
        body: body.trim(),
        author_role: authorRole,
        intent,
        idempotency_key: idempotencyKey,
      });
      if (image) {
        created = await uploadPublicationMedia(token, eventId, created.id, image);
      }
      if (activeDraftId) removePublicationDraft(eventId, activeDraftId);
      setLocalDrafts(listPublicationDrafts(eventId));
      setMessage(
        created.status === "pending_moderation"
          ? "Публикация отправлена на модерацию."
          : intent === "draft"
            ? "Черновик сохранён на сервере."
            : "Публикация опубликована.",
      );
      resetForm();
      await refresh();
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "Не удалось сохранить публикацию. Если текст создался, повторно прикрепите изображение.",
      );
    } finally {
      setBusy(false);
    }
  }

  async function onModerate(publication: PublicationOut, action: "publish" | "reject") {
    const token = getStoredToken();
    if (!token || !canModerate) return;
    const note =
      action === "reject"
        ? window.prompt("Причина отклонения (необязательно):")?.trim() || undefined
        : undefined;
    setBusy(true);
    setError(null);
    setMessage(null);
    try {
      await moderatePublication(token, eventId, publication.id, { action, note });
      setMessage(action === "publish" ? "Публикация одобрена." : "Публикация отклонена.");
      await refresh();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Не удалось выполнить модерацию");
    } finally {
      setBusy(false);
    }
  }

  function openLocalDraft(draft: LocalPublicationDraft) {
    setTitle(draft.title);
    setBody(draft.body);
    setType(draft.type);
    setAuthorRole(draft.authorRole || user?.role || "");
    setActiveDraftId(draft.id);
    setImage(
      draft.imageDataUrl
        ? dataUrlToFile(draft.imageDataUrl, draft.imageName ?? "publication-image.jpg")
        : null,
    );
    setMessage("Локальный черновик открыт для редактирования.");
    setError(null);
  }

  function discardLocalDraft(draftId: string) {
    removePublicationDraft(eventId, draftId);
    if (activeDraftId === draftId) resetForm();
    setLocalDrafts(listPublicationDrafts(eventId));
  }

  return (
    <section className={styles.layout} aria-labelledby="publication-feed-title">
      <div className={styles.heading}>
        <div>
          <h2 id="publication-feed-title">Лента события</h2>
          <span className={styles.muted}>Новости организаторов и материалы с площадки</span>
        </div>
      </div>

      {offlineBanner ? (
        <p className={styles.banner} role="status">
          Нет сети — черновик сохранён локально
        </p>
      ) : null}
      {message ? <p className={styles.success} role="status">{message}</p> : null}
      {error ? <p className={styles.error} role="alert">{error}</p> : null}

      {canCreate && !isArchived ? (
        <div className={styles.composer}>
          <div className={styles.heading}>
            <h3>Новая публикация</h3>
            <span className={styles.muted}>JPG, PNG или WebP · до 10 МБ</span>
          </div>
          <div className={styles.form}>
            <div className={styles.selectRow}>
              <label className={styles.field}>
                Тип
                <select
                  className={styles.select}
                  value={type}
                  onChange={(event) => setType(event.target.value as PublicationType)}
                  disabled={busy}
                >
                  {allowedTypes.includes("post") ? <option value="post">Пост</option> : null}
                  {allowedTypes.includes("news") ? <option value="news">Новость</option> : null}
                </select>
              </label>
              <label className={styles.field}>
                Роль автора
                <select
                  className={styles.select}
                  value={authorRole}
                  onChange={(event) => setAuthorRole(event.target.value)}
                  disabled={busy}
                >
                  {(authorRoles.length ? authorRoles : user ? [user.role] : []).map((role) => (
                    <option key={role} value={role}>{roleLabel(role)}</option>
                  ))}
                </select>
              </label>
            </div>
            <label className={styles.field}>
              Заголовок
              <input
                className={styles.input}
                value={title}
                maxLength={255}
                onChange={(event) => setTitle(event.target.value)}
                placeholder="Что произошло на событии?"
                disabled={busy}
              />
            </label>
            <label className={styles.field}>
              Текст
              <textarea
                className={styles.textarea}
                value={body}
                maxLength={20000}
                onChange={(event) => setBody(event.target.value)}
                placeholder="Расскажите подробнее"
                disabled={busy}
              />
            </label>
            <div className={styles.fileRow}>
              <label className={`btn btnSecondary ${styles.fileButton}`}>
                Снять фото
                <input
                  type="file"
                  accept="image/jpeg,image/png,image/webp"
                  capture="environment"
                  onChange={(event) => setImage(event.target.files?.[0] ?? null)}
                  disabled={busy}
                />
              </label>
              <label className={`btn btnSecondary ${styles.fileButton}`}>
                Выбрать из галереи
                <input
                  type="file"
                  accept="image/jpeg,image/png,image/webp"
                  onChange={(event) => setImage(event.target.files?.[0] ?? null)}
                  disabled={busy}
                />
              </label>
              {image ? (
                <button type="button" className="btn btnGhost" onClick={() => setImage(null)}>
                  Убрать фото
                </button>
              ) : null}
            </div>
            {imagePreview ? (
              <img className={styles.imagePreview} src={imagePreview} alt="Предпросмотр выбранного изображения" />
            ) : null}
            <div className={styles.actions}>
              <button type="button" className="btn btnSecondary" disabled={busy} onClick={() => void submit("draft")}>
                Черновик
              </button>
              <button
                type="button"
                className="btn btnSecondary"
                disabled={busy || !title.trim()}
                onClick={() => setPreviewOpen((value) => !value)}
              >
                Предпросмотр
              </button>
              <button type="button" className="btn btnPrimary" disabled={busy} onClick={() => void submit("publish")}>
                {busy ? "Сохраняем…" : "Опубликовать"}
              </button>
            </div>
          </div>
        </div>
      ) : null}

      {previewOpen ? (
        <article className={styles.preview} aria-label="Предпросмотр публикации">
          <span className={styles.muted}>{type === "news" ? "Новость" : "Пост"} · {roleLabel(authorRole)}</span>
          <h3>{title}</h3>
          <p className={styles.publicationBody}>{body || "Без текста"}</p>
          {imagePreview ? <img className={styles.imagePreview} src={imagePreview} alt="" /> : null}
        </article>
      ) : null}

      {localDrafts.length > 0 ? (
        <div>
          <h3>Локальные черновики ({localDrafts.length})</h3>
          <ul className={styles.draftList}>
            {localDrafts.map((draft) => (
              <li key={draft.id} className={styles.localDraft}>
                <div className={styles.draftHead}>
                  <div>
                    <strong>{draft.title || "Без заголовка"}</strong>
                    <div className={styles.muted}>
                      {draft.status === "queued" ? "Ожидает отправки" : "Черновик"} ·{" "}
                      {new Date(draft.updatedAt).toLocaleString("ru-RU")}
                    </div>
                  </div>
                  <div className={styles.actions}>
                    {canCreate && !isArchived ? (
                      <button type="button" className="btn btnSecondary btnSm" onClick={() => openLocalDraft(draft)}>
                        Открыть
                      </button>
                    ) : null}
                    <button type="button" className="btn btnDanger btnSm" onClick={() => discardLocalDraft(draft.id)}>
                      Удалить
                    </button>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      <ul className={styles.publicationList}>
        {publications.length === 0 ? (
          <li className={styles.empty}>{loaded ? "Публикаций пока нет." : "Загружаем ленту…"}</li>
        ) : (
          publications.map((publication) => {
            const editable =
              canModerate || String(publication.author_user_id) === String(user?.id);
            return (
              <li key={publication.id}>
                <article className={styles.publication}>
                  <div className={styles.publicationHead}>
                    <div>
                      <span className={styles.publicationMeta}>
                        {publication.type === "news" ? "Новость" : "Пост"} ·{" "}
                        {publication.author_display_name} · {roleLabel(publication.author_role)}
                      </span>
                      <h3>{publication.title}</h3>
                    </div>
                    {publication.status !== "published" && editable ? (
                      <span className={styles.badge}>{STATUS_LABELS[publication.status]}</span>
                    ) : null}
                  </div>
                  <p className={styles.publicationBody}>{publication.body}</p>
                  {publication.media.map((media) => (
                    <PublicationImage
                      key={media.id}
                      eventId={eventId}
                      publicationId={publication.id}
                      media={media}
                    />
                  ))}
                  <div className={styles.publicationMeta}>
                    {new Date(publication.published_at ?? publication.created_at).toLocaleString("ru-RU")}
                    {publication.moderation_note ? ` · ${publication.moderation_note}` : ""}
                  </div>
                  {canModerate && publication.status === "pending_moderation" ? (
                    <div className={styles.actions}>
                      <button
                        type="button"
                        className="btn btnPrimary btnSm"
                        disabled={busy}
                        onClick={() => void onModerate(publication, "publish")}
                      >
                        Одобрить
                      </button>
                      <button
                        type="button"
                        className="btn btnDanger btnSm"
                        disabled={busy}
                        onClick={() => void onModerate(publication, "reject")}
                      >
                        Отклонить
                      </button>
                    </div>
                  ) : null}
                </article>
              </li>
            );
          })
        )}
      </ul>
    </section>
  );
}
