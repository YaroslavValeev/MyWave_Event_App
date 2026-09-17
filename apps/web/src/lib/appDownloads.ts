import { apiFetch } from "./api";

export const APP_DOWNLOAD_ANALYTICS = {
  viewed: "mywave_event_app_card_viewed",
  selected: "mywave_event_app_platform_selected",
  clicked: "mywave_event_app_download_clicked",
  succeeded: "mywave_event_app_download_succeeded",
  failed: "mywave_event_app_download_failed",
} as const;

export type AppDownloadArtifactId = "android" | "ios" | "source" | "documentation";

export type AppDownloadArtifactState =
  | "loading"
  | "available"
  | "unavailable"
  | "error"
  | "success";

export type AppDownloadArtifact = {
  id: AppDownloadArtifactId | string;
  label: string;
  platform: string;
  format: string;
  version: string;
  size: string | null;
  last_updated: string;
  action_label: string;
  requirements: string[];
  state: AppDownloadArtifactState | string;
  message: string;
};

export type AppDownloadManifest = {
  app: {
    id: string;
    name: string;
    short_description: string;
    features: string[];
    version: string;
    last_updated: string;
    platforms: string[];
    readiness: string;
    available_count: number;
  };
  artifacts: AppDownloadArtifact[];
  generated_at: string;
};

export type AppDownloadHandoff = {
  artifact_id: string;
  location: string;
  open_in_new_tab: boolean;
  message: string;
};

export function getAppDownloadManifest() {
  return apiFetch<AppDownloadManifest>("/api/v1/app-downloads/manifest");
}

export function getAppDownloadStatus(artifactId: string) {
  return apiFetch<AppDownloadArtifact>(
    `/api/v1/app-downloads/${encodeURIComponent(artifactId)}/status`,
  );
}

export function startAppDownloadHandoff(artifactId: string) {
  return apiFetch<AppDownloadHandoff>(
    `/api/v1/app-downloads/${encodeURIComponent(artifactId)}/handoff`,
    { method: "POST", body: "{}" },
  );
}

export function trackAppDownloadEvent(
  event: string,
  meta: Record<string, string | number | boolean | null | undefined> = {},
  context = "projects/checklist-org",
): void {
  const properties: Record<string, string | number | boolean> = { app_id: "mywave-event-app" };
  for (const [key, value] of Object.entries(meta)) {
    if (value === undefined || value === null) continue;
    properties[key] = value;
  }
  void apiFetch("/api/v1/analytics/events", {
    method: "POST",
    body: JSON.stringify({
      event,
      context,
      channel: "web",
      properties,
    }),
  }).catch(() => {
    /* analytics must not block the UI */
  });
}

export function formatFileSize(size: string | null | undefined): string {
  return size && size.trim() ? size : "Уточняется";
}
