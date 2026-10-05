import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Swarm Mafia · Agent behavior lab",
  description: "Investigate agent behavior, replay versioned traces, and explore controlled test environments with source-linked human review.",
  other: {
    "codex-preview": "development",
  },
  icons: {
    icon: "/favicon.svg",
    shortcut: "/favicon.svg",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">{children}</body>
    </html>
  );
}
