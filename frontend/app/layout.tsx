import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "HydroSentinel | Water Anomaly Decision Support",
  description:
    "Context-aware water anomaly and leak-detection decision-support prototype using simulated telemetry for buildings and managed facilities.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
