import type { CapacitorConfig } from "@capacitor/cli";

/**
 * Hosted-URL mode (ADR-0014): WebView loads staging/production Next.js app.
 * Replace server.url before release. Do not claim APK readiness without Gradle build.
 */
const config: CapacitorConfig = {
  appId: "app.mywave.event",
  appName: "Champ App",
  webDir: "www",
  server: {
    // Owner: set public HTTPS URL of apps/web
    url: process.env.CAPACITOR_SERVER_URL || "http://127.0.0.1:3000",
    cleartext: true,
  },
  android: {
    allowMixedContent: true,
  },
};

export default config;
