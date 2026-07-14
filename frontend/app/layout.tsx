import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "HydroSentinel",
  description: "AI-assisted school water infrastructure monitoring",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}