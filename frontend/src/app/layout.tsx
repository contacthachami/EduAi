import type { Metadata } from "next";
import "./globals.css";
import AnimatedTitle from "@/components/AnimatedTitle";

export const metadata: Metadata = {
  title: "EduAI — Assistant Pédagogique Intelligent",
  description:
    "Uploadez un PDF de cours, posez des questions, générez des résumés et des quiz automatiquement.",
  icons: {
    icon: [{ url: "/favicon.svg", type: "image/svg+xml" }],
    shortcut: "/favicon.svg",
    apple: "/favicon.svg",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="fr">
      <body>
        <AnimatedTitle />
        <header className="border-b border-border">
          <nav className="page-container flex items-center justify-between h-14">
            <a
              href="/"
              className="flex items-center gap-2 font-display text-lg font-semibold text-ink-primary tracking-tight"
            >
              <img
                src="/favicon.svg"
                alt="EduAI"
                width={24}
                height={24}
                className="rounded-md"
              />
              EduAI
            </a>
            <div className="flex items-center gap-6">
              <a
                href="/"
                className="text-sm text-ink-secondary hover:text-accent transition-colors duration-200"
              >
                Cours
              </a>
              <a
                href="/upload"
                className="text-sm text-ink-secondary hover:text-accent transition-colors duration-200 border-b border-transparent hover:border-accent"
              >
                Ajouter un cours
              </a>
            </div>
          </nav>
        </header>
        <main className="min-h-[calc(100vh-3.5rem)]">{children}</main>
      </body>
    </html>
  );
}
