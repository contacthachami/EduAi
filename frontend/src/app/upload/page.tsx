"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { ArrowLeft, FileCheck2, Lock, Mail } from "lucide-react";
import FileUploader from "@/components/FileUploader";
import { useAuth } from "@/lib/auth";
import axios from "axios";

const FREE_PLAN_LIMIT = 3;

export default function UploadPage() {
  const router = useRouter();
  const { user, loading } = useAuth();
  const [coursesCount, setCoursesCount] = useState<number | null>(null);
  const [quotaLoading, setQuotaLoading] = useState(true);

  useEffect(() => {
    if (!loading && !user) router.replace("/landing");
  }, [loading, user, router]);

  // Fetch courses count to check quota
  useEffect(() => {
    if (!user) return;
    const token =
      typeof window !== "undefined"
        ? localStorage.getItem("eduai_token")
        : null;
    axios
      .get("/api/courses", {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      })
      .then((res) => setCoursesCount(res.data.length))
      .catch(() => setCoursesCount(0))
      .finally(() => setQuotaLoading(false));
  }, [user]);

  if (loading || !user || quotaLoading) return null;

  // ── Free plan limit reached ────────────────────────────────────────────────
  const isBlocked =
    user.plan !== "pro" &&
    coursesCount !== null &&
    coursesCount >= FREE_PLAN_LIMIT;

  if (isBlocked) {
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
            className="mt-5"
          >
            <div className="rounded-xl border border-[#DED8D1] bg-white shadow-sm overflow-hidden">
              {/* Header band */}
              <div className="bg-[#FDF3EE] border-b border-[#F0D9CE] px-6 py-5 flex items-center gap-4">
                <div className="flex h-11 w-11 items-center justify-center rounded-full bg-[#F0E3DA]">
                  <Lock className="w-5 h-5 text-[#B85B2A]" />
                </div>
                <div>
                  <h1 className="text-lg font-bold text-[#171412]">
                    Limite du plan gratuit atteinte
                  </h1>
                  <p className="text-sm text-[#8D837A] mt-0.5">
                    Vous avez utilisé vos{" "}
                    <span className="font-semibold text-[#B85B2A]">
                      {FREE_PLAN_LIMIT}/{FREE_PLAN_LIMIT}
                    </span>{" "}
                    uploads disponibles avec le plan Free.
                  </p>
                </div>
              </div>

              {/* Body */}
              <div className="px-6 py-8 flex flex-col items-center text-center gap-6">
                {/* Usage pills */}
                <div className="flex gap-2">
                  {Array.from({ length: FREE_PLAN_LIMIT }).map((_, i) => (
                    <span
                      key={i}
                      className="w-8 h-2 rounded-full bg-[#B85B2A] opacity-80"
                    />
                  ))}
                  <span className="w-8 h-2 rounded-full bg-[#DED8D1]" />
                </div>

                <p className="max-w-md text-[#5F5750] text-sm leading-relaxed">
                  Pour continuer à uploader des cours sans restriction, passez
                  au{" "}
                  <span className="font-semibold text-[#171412]">plan Pro</span>
                  . Contactez le support pour activer votre plan Pro.
                </p>

                <a
                  href="mailto:support@eduai.app?subject=Passage%20au%20plan%20Pro"
                  className="inline-flex items-center gap-2 px-6 py-3 rounded-lg bg-[#B85B2A] text-white text-sm font-semibold hover:bg-[#9A4B22] transition-colors shadow-sm"
                >
                  <Mail className="w-4 h-4" />
                  Contacter le support
                </a>

                <p className="text-xs text-[#8D837A]">
                  Vous pouvez toujours consulter et utiliser vos{" "}
                  <Link
                    href="/courses"
                    className="underline hover:text-[#B85B2A] transition-colors"
                  >
                    cours existants
                  </Link>
                  .
                </p>
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    );
  }

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
            {/* Quota indicator for free plan */}
            {user.plan !== "pro" && coursesCount !== null && (
              <div className="mt-5 pt-4 border-t border-border">
                <p className="text-xs font-medium text-ink-secondary mb-2">
                  Uploads utilisés
                </p>
                <div className="flex gap-1.5 mb-2">
                  {Array.from({ length: FREE_PLAN_LIMIT }).map((_, i) => (
                    <span
                      key={i}
                      className={`flex-1 h-1.5 rounded-full transition-colors ${
                        i < coursesCount ? "bg-[#B85B2A]" : "bg-[#DED8D1]"
                      }`}
                    />
                  ))}
                </div>
                <p className="text-xs text-ink-muted">
                  {coursesCount}/{FREE_PLAN_LIMIT} cours — Plan Free
                </p>
              </div>
            )}
          </aside>
        </motion.div>
      </div>
    </div>
  );
}
