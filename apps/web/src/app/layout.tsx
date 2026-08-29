import type { Metadata, Viewport } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "MyWave Event App",
    template: "%s · MyWave Event App",
  },
  description: "Цифровая платформа соревнований MyWave — события, роли, судейство.",
  applicationName: "MyWave Event App",
  manifest: "/manifest.webmanifest",
  appleWebApp: {
    capable: true,
    title: "MyWave Event",
    statusBarStyle: "default",
  },
  icons: {
    icon: [{ url: "/icons/icon.svg", type: "image/svg+xml" }],
  },
};

export const viewport: Viewport = {
  themeColor: "#e7f6f4",
  width: "device-width",
  initialScale: 1,
  maximumScale: 5,
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ru">
      <body>
        <a className="skipLink" href="#main">
          Перейти к содержимому
        </a>
        <div className="shell">{children}</div>
      </body>
    </html>
  );
}
