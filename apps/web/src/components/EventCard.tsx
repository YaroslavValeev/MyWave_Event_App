import Link from "next/link";
import { StatusBadge } from "@/components/StatusBadge";
import { formatEventPeriod } from "@/lib/format";
import type { EventOut } from "@/lib/api";
import styles from "@/app/events/events.module.css";

type EventCardProps = {
  event: EventOut;
  cta?: string;
};

export function EventCard({ event, cta = "Открыть" }: EventCardProps) {
  return (
    <li className={styles.cardItem}>
      <div className={styles.itemHead}>
        <h2 className={styles.itemTitle}>
          <Link href={`/events/${event.id}`}>{event.title}</Link>
        </h2>
        <StatusBadge status={event.status} />
      </div>
      {event.description ? <p className={styles.itemDesc}>{event.description}</p> : null}
      <dl className={styles.meta}>
        <div>
          <dt>Город</dt>
          <dd>{event.city || "—"}</dd>
        </div>
        <div>
          <dt>Даты</dt>
          <dd>{formatEventPeriod(event.starts_at, event.ends_at)}</dd>
        </div>
        <div>
          <dt>Дисциплины</dt>
          <dd>{event.disciplines || "—"}</dd>
        </div>
      </dl>
      <Link href={`/events/${event.id}`} className="btn btnPrimary btnSm" style={{ marginTop: "0.75rem" }}>
        {cta}
      </Link>
    </li>
  );
}
