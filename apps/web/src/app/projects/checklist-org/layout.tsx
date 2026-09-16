import type { Metadata } from "next";
import type { ReactNode } from "react";

export const metadata: Metadata = {
  title: "Чек-лист организатора",
  description: "Готовое решение MyWave Event App: описание, статус и скачивание сборок.",
};

export default function OrganizerChecklistLayout({ children }: { children: ReactNode }) {
  return children;
}
