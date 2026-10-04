import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Kairosity Observatory",
  description: "Investigate agent behavior through connected evidence and human-guided analysis.",
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
