import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "EduAI — Assistant Pédagogique Intelligent",
  description:
    "Uploadez un PDF de cours, posez des questions, générez des résumés et des quiz automatiquement.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="fr">
      <body>
        <header className="border-b border-border">
          <nav className="page-container flex items-center justify-between h-14">
            <a
              href="/"
              className="font-display text-lg font-semibold text-ink-primary tracking-tight"
            >
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
