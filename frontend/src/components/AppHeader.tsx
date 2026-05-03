"use client";

import Link from "next/link";
import Image from "next/image";
import { usePathname, useRouter } from "next/navigation";
import { Plus, LogOut } from "lucide-react";
import { useAuth } from "@/lib/auth";

export default function AppHeader() {
  const pathname = usePathname();
  const router = useRouter();
  const { user, logout } = useAuth();

  // Hide header on landing and auth pages
  if (pathname === "/landing" || pathname === "/auth") return null;

  const navItems = user
    ? [
        { href: "/courses", label: "Cours" },
        { href: "/upload", label: "Ajouter un cours" },
      ]
    : [];

  return (
    <header className="border-b border-border bg-bg-primary/95">
      <nav className="page-container flex min-h-16 items-center justify-between gap-4">
        <Link
          href="/courses"
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

        <div
          className="flex items-center gap-1 sm:gap-2"
          aria-label="Navigation principale"
        >
          {navItems.map((item) => {
            const isActive =
              pathname === item.href || pathname.startsWith(`${item.href}/`);

            return (
              <Link
                key={item.href}
                href={item.href}
                className={`nav-link ${isActive ? "nav-link-active" : ""}`}
                aria-current={isActive ? "page" : undefined}
              >
                {item.href === "/upload" && (
                  <Plus
                    size={15}
                    strokeWidth={1.8}
                    className="hidden sm:block"
                  />
                )}
                {item.label}
              </Link>
            );
          })}

          {user && (
            <button
              onClick={() => {
                logout();
                router.push("/landing");
              }}
              className="nav-link flex items-center gap-1 text-sm"
            >
              <LogOut size={14} />
              Déconnexion
            </button>
          )}
        </div>
      </nav>
    </header>
  );
}
