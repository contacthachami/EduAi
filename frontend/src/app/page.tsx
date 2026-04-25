"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import {
  AlertCircle,
  ArrowRight,
  BookOpen,
  CalendarDays,
  FileText,
  Layers,
  Loader2,
  Trash2,
  UploadCloud,
} from "lucide-react";
import FileUploader from "@/components/FileUploader";
import { deleteCourse, fetchCourses, type CourseInfo } from "@/lib/api";

function formatDate(value: string) {
  return new Date(value).toLocaleDateString("fr-FR", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

export default function HomePage() {
  const router = useRouter();
  const [courses, setCourses] = useState<CourseInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<CourseInfo | null>(null);
  const [deleting, setDeleting] = useState(false);

  const recentCourses = useMemo(
    () =>
      [...courses].sort(
        (a, b) =>
          new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
      ),
    [courses],
  );

  const loadCourses = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchCourses();
      setCourses(data);
    } catch {
      setError("Impossible de charger vos cours pour le moment.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCourses();
  }, []);

  const confirmDelete = async () => {
    if (!deleteTarget) return;
    setDeleting(true);
    try {
      await deleteCourse(deleteTarget.id);
      setCourses((prev) => prev.filter((course) => course.id !== deleteTarget.id));
      setDeleteTarget(null);
    } catch {
      setError("Le cours n'a pas pu être supprimé. Réessayez dans un instant.");
    } finally {
      setDeleting(false);
    }
  };

  return (
    <div className="page-container py-8 sm:py-12">
      <section className="grid gap-8 lg:grid-cols-[minmax(0,1fr)_360px] lg:items-start">
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.25, ease: "easeOut" }}
          className="panel overflow-hidden"
        >
          <div className="border-b border-border bg-bg-subtle px-5 py-5 sm:px-7">
            <div className="flex items-start gap-4">
              <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-card bg-accent text-white">
                <UploadCloud size={21} strokeWidth={1.8} />
              </div>
              <div className="min-w-0">
                <p className="eyebrow">Assistant pédagogique</p>
                <h1 className="mt-2 text-3xl font-bold text-ink-primary sm:text-4xl">
                  Ajoutez votre cours PDF
                </h1>
                <p className="mt-3 max-w-2xl text-sm text-ink-secondary sm:text-base">
                  Transformez un support de cours en espace de travail :
                  questions contextualisées, synthèse pédagogique et quiz de
                  révision.
                </p>
              </div>
            </div>
          </div>
          <div className="px-5 py-5 sm:px-7 sm:py-6">
            <FileUploader
              submitLabel="Créer l'espace de travail"
              onUploadComplete={(courseId) => router.push(`/course/${courseId}`)}
            />
          </div>
        </motion.div>

        <motion.aside
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.25, ease: "easeOut", delay: 0.05 }}
          className="rounded-panel border border-border bg-bg-subtle p-5"
        >
          <p className="eyebrow">Méthode de travail</p>
          <div className="mt-4 space-y-4">
            <WorkflowStep
              index="01"
              title="Ajoutez un PDF"
              text="Le document est extrait et indexé pour la recherche dans le cours."
            />
            <WorkflowStep
              index="02"
              title="Interrogez le contenu"
              text="Les réponses restent ancrées dans les pages du document."
            />
            <WorkflowStep
              index="03"
              title="Révisez efficacement"
              text="Consultez la synthèse puis entraînez-vous avec un quiz."
            />
          </div>
        </motion.aside>
      </section>

      <section className="mt-10">
        <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="eyebrow">Bibliothèque</p>
            <h2 className="mt-1 text-2xl font-semibold text-ink-primary">
              Cours récents
            </h2>
          </div>
          <Link href="/upload" className="btn-secondary w-full sm:w-auto">
            Ajouter un cours
            <ArrowRight size={16} strokeWidth={1.8} />
          </Link>
        </div>

        {error && (
          <div
            role="alert"
            className="status-message status-message-error mb-4 flex items-start gap-2"
          >
            <AlertCircle size={16} strokeWidth={1.8} className="mt-0.5 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {loading ? (
          <LoadingCourses />
        ) : recentCourses.length === 0 ? (
          <EmptyCourses />
        ) : (
          <div className="grid gap-3">
            {recentCourses.map((course, index) => (
              <motion.div
                key={course.id}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.2, ease: "easeOut", delay: index * 0.03 }}
                className="panel interactive-card"
              >
                <div className="flex flex-col gap-4 p-4 sm:flex-row sm:items-center sm:justify-between">
                  <Link
                    href={`/course/${course.id}`}
                    className="group flex min-w-0 flex-1 items-start gap-3 rounded-card"
                  >
                    <div className="mt-0.5 flex h-10 w-10 shrink-0 items-center justify-center rounded-card bg-accent-soft text-accent">
                      <FileText size={18} strokeWidth={1.8} />
                    </div>
                    <div className="min-w-0">
                      <h3 className="truncate text-sm font-semibold text-ink-primary group-hover:text-accent-hover">
                        {course.name}
                      </h3>
                      <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-ink-muted">
                        <span className="inline-flex items-center gap-1">
                          <BookOpen size={13} strokeWidth={1.8} />
                          {course.pages} pages
                        </span>
                        <span className="inline-flex items-center gap-1">
                          <Layers size={13} strokeWidth={1.8} />
                          {course.chunks_count} segments
                        </span>
                        <span className="inline-flex items-center gap-1">
                          <CalendarDays size={13} strokeWidth={1.8} />
                          {formatDate(course.created_at)}
                        </span>
                      </div>
                    </div>
                  </Link>
                  <div className="flex items-center justify-end gap-2">
                    <Link
                      href={`/course/${course.id}`}
                      className="btn-ghost text-sm"
                    >
                      Ouvrir
                      <ArrowRight size={15} strokeWidth={1.8} />
                    </Link>
                    <button
                      type="button"
                      onClick={() => setDeleteTarget(course)}
                      className="icon-button hover:bg-error-light hover:text-error"
                      aria-label={`Supprimer ${course.name}`}
                    >
                      <Trash2 size={17} strokeWidth={1.8} />
                    </button>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        )}
      </section>

      {deleteTarget && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-ink-primary/30 px-4"
          role="presentation"
        >
          <div
            role="dialog"
            aria-modal="true"
            aria-labelledby="delete-title"
            className="w-full max-w-md rounded-panel border border-border bg-bg-card p-5 shadow-card"
          >
            <h2 id="delete-title" className="text-xl font-semibold text-ink-primary">
              Supprimer ce cours ?
            </h2>
            <p className="mt-2 text-sm text-ink-secondary">
              Cette action supprimera le cours « {deleteTarget.name} » et ses
              données associées.
            </p>
            <div className="mt-5 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
              <button
                type="button"
                className="btn-secondary"
                onClick={() => setDeleteTarget(null)}
                disabled={deleting}
              >
                Annuler
              </button>
              <button
                type="button"
                className="btn-primary bg-error hover:bg-error"
                onClick={confirmDelete}
                disabled={deleting}
              >
                {deleting && (
                  <Loader2 size={16} strokeWidth={1.8} className="animate-spin" />
                )}
                Supprimer
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function WorkflowStep({
  index,
  title,
  text,
}: {
  index: string;
  title: string;
  text: string;
}) {
  return (
    <div className="flex gap-3">
      <span className="font-mono text-xs font-medium text-accent">{index}</span>
      <div>
        <h3 className="text-sm font-semibold text-ink-primary">{title}</h3>
        <p className="mt-1 text-sm text-ink-secondary">{text}</p>
      </div>
    </div>
  );
}

function LoadingCourses() {
  return (
    <div className="grid gap-3" role="status" aria-live="polite">
      {[0, 1, 2].map((item) => (
        <div key={item} className="panel p-4">
          <div className="flex animate-pulse items-center gap-3">
            <div className="h-10 w-10 rounded-card bg-bg-secondary" />
            <div className="flex-1 space-y-2">
              <div className="h-3 w-2/3 rounded bg-bg-secondary" />
              <div className="h-3 w-1/3 rounded bg-bg-secondary" />
            </div>
          </div>
        </div>
      ))}
      <span className="sr-only">Chargement des cours</span>
    </div>
  );
}

function EmptyCourses() {
  return (
    <div className="rounded-panel border border-dashed border-border-strong bg-bg-subtle px-5 py-10 text-center">
      <BookOpen size={24} strokeWidth={1.8} className="mx-auto text-ink-muted" />
      <h3 className="mt-3 text-base font-semibold text-ink-primary">
        Aucun cours indexé
      </h3>
      <p className="mx-auto mt-2 max-w-md text-sm text-ink-secondary">
        Ajoutez un PDF ci-dessus pour créer votre premier espace de travail
        pédagogique.
      </p>
    </div>
  );
}
