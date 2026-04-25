import type { Metadata } from "next";
import type { ReactNode } from "react";
import "./globals.css";
import AppHeader from "@/components/AppHeader";

export const metadata: Metadata = {
  title: "EduAI - Assistant pédagogique intelligent",
  description:
    "Ajoutez un PDF de cours, posez des questions, consultez une synthèse pédagogique et préparez vos révisions.",
  icons: {
    icon: [{ url: "/favicon.svg", type: "image/svg+xml" }],
    shortcut: "/favicon.svg",
    apple: "/favicon.svg",
  },
};

export default function RootLayout({
  children,
}: {
  children: ReactNode;
}) {
  return (
    <html lang="fr">
      <body>
        <AppHeader />
        <main className="min-h-[calc(100vh-4rem)]">{children}</main>
      </body>
    </html>
  );
}
