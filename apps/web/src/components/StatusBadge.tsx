import { EVENT_STATUS_LABELS, isEventStatus } from "@/lib/roles";
import {
  APPLICATION_STATUS_LABELS,
  ENTRY_STATUS_LABELS,
  HEAT_STATUS_LABELS,
  PROTOCOL_STATUS_LABELS,
  RESULT_STATUS_LABELS,
} from "@/lib/labels";
import styles from "./StatusBadge.module.css";

type BadgeKind = "event" | "result" | "heat" | "application" | "protocol" | "entry";

type StatusBadgeProps = {
  status: string;
  kind?: BadgeKind;
};

const MAPS: Record<BadgeKind, Record<string, string>> = {
  event: EVENT_STATUS_LABELS,
  result: RESULT_STATUS_LABELS,
  heat: HEAT_STATUS_LABELS,
  application: APPLICATION_STATUS_LABELS,
  protocol: PROTOCOL_STATUS_LABELS,
  entry: ENTRY_STATUS_LABELS,
};

export function StatusBadge({ status, kind = "event" }: StatusBadgeProps) {
  const label = MAPS[kind][status] ?? (kind === "event" && isEventStatus(status) ? EVENT_STATUS_LABELS[status] : status);
  const toneClass = styles[status] ?? styles.unknown;

  return (
    <span className={`${styles.badge} ${toneClass}`} title={label}>
      {label}
    </span>
  );
}
