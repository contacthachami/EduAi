"use client";

import Link from "next/link";
import Image from "next/image";
import { usePathname } from "next/navigation";
import { Plus } from "lucide-react";

const navItems = [
  { href: "/", label: "Cours" },
  { href: "/upload", label: "Ajouter un cours" },
];

export default function AppHeader() {
  const pathname = usePathname();

  return (
    <header className="border-b border-border bg-bg-primary/95">
      <nav className="page-container flex min-h-16 items-center justify-between gap-4">
        <Link
          href="/"
          className="flex min-h-10 items-center gap-2 rounded-card pr-2 font-display text-lg font-semibold text-ink-primary"
          aria-label="EduAI, revenir aux cours"
        >
          <Image
            src="/favicon.svg"
            alt=""
            width={26}
            height={26}
            className="rounded-md"
          />
          <span>EduAI</span>
        </Link>

        <div className="flex items-center gap-1 sm:gap-2" aria-label="Navigation principale">
          {navItems.map((item) => {
            const isActive =
              item.href === "/"
                ? pathname === "/"
                : pathname === item.href || pathname.startsWith(`${item.href}/`);

            return (
              <Link
                key={item.href}
                href={item.href}
                className={`nav-link ${isActive ? "nav-link-active" : ""}`}
                aria-current={isActive ? "page" : undefined}
              >
                {item.href === "/upload" && (
                  <Plus size={15} strokeWidth={1.8} className="hidden sm:block" />
                )}
                {item.label}
              </Link>
            );
          })}
        </div>
      </nav>
    </header>
  );
}
