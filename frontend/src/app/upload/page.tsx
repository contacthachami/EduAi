"use client";

import { useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { ArrowLeft, FileCheck2 } from "lucide-react";
import FileUploader from "@/components/FileUploader";
import { useAuth } from "@/lib/auth";

export default function UploadPage() {
  const router = useRouter();
  const { user, loading } = useAuth();

  useEffect(() => {
    if (!loading && !user) router.replace("/landing");
  }, [loading, user, router]);

  if (loading || !user) return null;

  return (
    <div className="page-container py-8 sm:py-12">
      <div className="mx-auto max-w-content">
        <Link href="/courses" className="btn-ghost -ml-3">
          <ArrowLeft size={16} strokeWidth={1.8} />
          Retour aux cours
        </Link>

        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.25, ease: "easeOut" }}
          className="mt-5 grid gap-8 lg:grid-cols-[minmax(0,1fr)_300px]"
        >
          <section className="panel overflow-hidden">
            <div className="border-b border-border bg-bg-subtle px-5 py-5 sm:px-7">
              <p className="eyebrow">Nouveau document</p>
              <h1 className="mt-2 text-3xl font-bold text-ink-primary">
                Ajouter un cours
              </h1>
              <p className="mt-3 max-w-2xl text-sm text-ink-secondary">
                Sélectionnez un PDF de cours. EduAI extrait le texte, prépare
                les segments de recherche et ouvre ensuite l&apos;espace de
                travail.
              </p>
            </div>
            <div className="px-5 py-5 sm:px-7 sm:py-6">
              <FileUploader
                onUploadComplete={(courseId) =>
                  router.push(`/course/${courseId}`)
                }
              />
            </div>
          </section>

          <aside className="rounded-panel border border-border bg-bg-subtle p-5">
            <div className="flex h-10 w-10 items-center justify-center rounded-card bg-accent-soft text-accent">
              <FileCheck2 size={19} strokeWidth={1.8} />
            </div>
            <h2 className="mt-4 text-base font-semibold text-ink-primary">
              Avant l&apos;indexation
            </h2>
            <ul className="mt-3 space-y-2 text-sm text-ink-secondary">
              <li>Utilisez un PDF lisible contenant le texte du cours.</li>
              <li>Donnez un nom clair pour le retrouver rapidement.</li>
              <li>Gardez le document sous la limite de 50 MB.</li>
            </ul>
          </aside>
        </motion.div>
      </div>
    </div>
  );
}
