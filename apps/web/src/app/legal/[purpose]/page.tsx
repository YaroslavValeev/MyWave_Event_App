"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { AppHeader } from "@/components/AppHeader";
import { ApiError, fetchLegalDocument, type LegalDocument } from "@/lib/api";
import styles from "../../login/login.module.css";

export default function LegalDocumentPage() {
  const params = useParams<{ purpose: string }>();
  const purpose = params.purpose;
  const [doc, setDoc] = useState<LegalDocument | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void fetchLegalDocument(purpose)
      .then(setDoc)
      .catch((err) => {
        setError(err instanceof ApiError ? err.message : "Не удалось загрузить документ.");
      });
  }, [purpose]);

  return (
    <>
      <AppHeader subtitle="Документы" />
      <main id="main" className={styles.main}>
        {error ? (
          <p className={styles.error} role="alert">
            {error}
          </p>
        ) : null}
        {doc ? (
          <>
            <h1 className={styles.title}>{doc.title}</h1>
            <p className={styles.hint}>
              Версия {doc.version}.{" "}
              <Link href="/register">К регистрации</Link>
            </p>
            <article className={styles.prose} aria-label={doc.title}>
              {(doc.body || doc.summary).split("\n").map((line, index) =>
                line.startsWith("# ") ? (
                  <h2 key={index}>{line.replace(/^#+\s/, "")}</h2>
                ) : line.startsWith("## ") ? (
                  <h2 key={index}>{line.replace(/^#+\s/, "")}</h2>
                ) : line.trim() ? (
                  <p key={index}>{line}</p>
                ) : null,
              )}
            </article>
          </>
        ) : !error ? (
          <p className={styles.hint}>Загружаем документ…</p>
        ) : null}
      </main>
    </>
  );
}
