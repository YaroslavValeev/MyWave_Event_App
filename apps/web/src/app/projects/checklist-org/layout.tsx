import type { Metadata } from "next";
import type { ReactNode } from "react";

export const metadata: Metadata = {
  title: "Чек-лист организатора",
  description: "11 разделов подготовки площадки и выдача MyWave Event App.",
};

export default function OrganizerChecklistLayout({ children }: { children: ReactNode }) {
  return children;
}
