import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "HydroSentinel",
  description: "AI-assisted water anomaly and leak-detection decision support for buildings and managed facilities",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
