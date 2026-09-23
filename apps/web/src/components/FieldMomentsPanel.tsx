"use client";

import { useRef, useState } from "react";
import {
  ApiError,
  FieldMomentOut,
  HeatOut,
  fieldMomentFileUrl,
  getStoredToken,
  updateFieldMoment,
  uploadFieldMoment,
} from "@/lib/api";
import { FIELD_MOMENT_STATUS_LABELS, FIELD_POV_LABELS, labelOf } from "@/lib/labels";
import styles from "../app/events/events.module.css";

type FieldMomentsPanelProps = {
  eventId: string;
  heats: HeatOut[];
  selectedHeatId: number | null;
  canModerate: boolean;
  archived: boolean;
  items: FieldMomentOut[];
  onChange: (items: FieldMomentOut[]) => void;
};

export function FieldMomentsPanel({
  eventId,
  heats,
  selectedHeatId,
  canModerate,
  archived,
  items,
  onChange,
}: FieldMomentsPanelProps) {
  const photoRef = useRef<HTMLInputElement>(null);
  const videoRef = useRef<HTMLInputElement>(null);
  const galleryRef = useRef<HTMLInputElement>(null);
  const [pov, setPov] = useState("backstage");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [previews, setPreviews] = useState<Record<number, string>>({});

  async function sendFile(file: File | undefined) {
    const token = getStoredToken();
    if (!token || !file || archived) return;
    setBusy(true);
    setError(null);
    try {
      const created = await uploadFieldMoment(token, eventId, file, {
        pov,
        heat_id: selectedHeatId ?? undefined,
      });
      onChange([created, ...items]);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Не удалось сохранить момент");
    } finally {
      setBusy(false);
    }
  }

  async function openFile(moment: FieldMomentOut) {
    const token = getStoredToken();
    if (!token) return;
    if (previews[moment.id]) {
      window.open(previews[moment.id], "_blank", "noopener,noreferrer");
      return;
    }
    const res = await fetch(fieldMomentFileUrl(eventId, moment.id), {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) {
      setError("Не удалось открыть файл");
      return;
    }
    const url = URL.createObjectURL(await res.blob());
    setPreviews((prev) => ({ ...prev, [moment.id]: url }));
    window.open(url, "_blank", "noopener,noreferrer");
  }

  async function setStatus(moment: FieldMomentOut, status: string) {
    const token = getStoredToken();
    if (!token || !canModerate) return;
    try {
      const updated = await updateFieldMoment(token, eventId, moment.id, { status });
      onChange(items.map((item) => (item.id === updated.id ? updated : item)));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Не удалось обновить статус");
    }
  }

  return (
    <section className={styles.workspace} aria-labelledby="field-moments-title">
      <h2 id="field-moments-title" className={styles.itemTitle}>
        Моменты события
      </h2>
      <p className={styles.muted}>
        За кулисами, взгляд пилота, маршал на старте — короткие кадры для эфира. Это не протокол судьи.
        На телефоне откроется камера; на компьютере можно выбрать файл. iPhone может отдать HEIC — это
        допустимо.
      </p>
      {archived ? (
        <p className={styles.muted}>Событие в архиве — съёмка закрыта.</p>
      ) : (
        <div className={styles.panel}>
          <label className={styles.muted} htmlFor="field-pov">
            Откуда снимаем
          </label>
          <select
            id="field-pov"
            className={styles.fieldControl}
            value={pov}
            onChange={(e) => setPov(e.target.value)}
            disabled={busy}
          >
            {Object.entries(FIELD_POV_LABELS).map(([code, label]) => (
              <option key={code} value={code}>
                {label}
              </option>
            ))}
          </select>
          {selectedHeatId ? (
            <p className={styles.muted} style={{ marginTop: "0.5rem" }}>
              Привязка к заезду: {heats.find((h) => h.id === selectedHeatId)?.code || selectedHeatId}
            </p>
          ) : null}
          <div className={styles.actions}>
            <button
              type="button"
              className="btn btnPrimary"
              disabled={busy}
              onClick={() => photoRef.current?.click()}
            >
              Снять фото
            </button>
            <button
              type="button"
              className="btn btnPrimary"
              disabled={busy}
              onClick={() => videoRef.current?.click()}
            >
              Снять видео
            </button>
            <button
              type="button"
              className="btn btnSecondary"
              disabled={busy}
              onClick={() => galleryRef.current?.click()}
            >
              Из галереи
            </button>
          </div>
          <input
            ref={photoRef}
            type="file"
            accept="image/*"
            capture="environment"
            hidden
            onChange={(e) => {
              const file = e.target.files?.[0];
              e.target.value = "";
              void sendFile(file);
            }}
          />
          <input
            ref={videoRef}
            type="file"
            accept="video/*"
            capture="environment"
            hidden
            onChange={(e) => {
              const file = e.target.files?.[0];
              e.target.value = "";
              void sendFile(file);
            }}
          />
          <input
            ref={galleryRef}
            type="file"
            accept="image/*,video/*"
            hidden
            onChange={(e) => {
              const file = e.target.files?.[0];
              e.target.value = "";
              void sendFile(file);
            }}
          />
          {busy ? <p className={styles.muted}>Сохраняем…</p> : null}
          {error ? (
            <p className={styles.error} role="alert">
              {error}
            </p>
          ) : null}
        </div>
      )}
      <ul className={styles.list}>
        {items.length === 0 ? (
          <li className={styles.item}>
            <span className={styles.muted}>Пока нет кадров. Первый снимок — с телефона на площадке.</span>
          </li>
        ) : (
          items.map((moment) => (
            <li key={moment.id} className={styles.item}>
              <div className={styles.itemHead}>
                <strong>
                  {moment.title} · {labelOf(FIELD_POV_LABELS, moment.pov)}
                </strong>
                <span className={styles.muted}>
                  {moment.media_kind === "video" ? "Видео" : "Фото"} ·{" "}
                  {labelOf(FIELD_MOMENT_STATUS_LABELS, moment.status)}
                </span>
              </div>
              <div className={styles.actions}>
                <button type="button" className="btn btnPrimary btnSm" onClick={() => void openFile(moment)}>
                  Открыть
                </button>
                {canModerate && moment.status !== "approved" ? (
                  <button
                    type="button"
                    className="btn btnSecondary btnSm"
                    onClick={() => void setStatus(moment, "approved")}
                  >
                    Для эфира
                  </button>
                ) : null}
                {canModerate && moment.status !== "withheld" ? (
                  <button
                    type="button"
                    className="btn btnSecondary btnSm"
                    onClick={() => void setStatus(moment, "withheld")}
                  >
                    Скрыть
                  </button>
                ) : null}
              </div>
            </li>
          ))
        )}
      </ul>
    </section>
  );
}
