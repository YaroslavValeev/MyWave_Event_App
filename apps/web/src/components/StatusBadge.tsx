import { EVENT_STATUS_LABELS, isEventStatus, type EventStatus } from "@/lib/roles";
import styles from "./StatusBadge.module.css";

type StatusBadgeProps = {
  status: EventStatus | string;
};

export function StatusBadge({ status }: StatusBadgeProps) {
  const known = isEventStatus(status);
  const label = known ? EVENT_STATUS_LABELS[status] : status;
  const toneClass = known ? styles[status] : styles.unknown;

  return (
    <span className={`${styles.badge} ${toneClass}`} title={label}>
      {label}
    </span>
  );
}
