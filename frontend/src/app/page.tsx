/**
 * Page d'accueil — Liste des cours (style bibliothèque).
 * Titre en Playfair Display 52px. Tableau minimaliste.
 */
"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Trash2, BookOpen, FileText } from "lucide-react";
import { fetchCourses, deleteCourse, type CourseInfo } from "@/lib/api";

export default function HomePage() {
  const [courses, setCourses] = useState<CourseInfo[]>([]);
  const [loading, setLoading] = useState(true);

  const loadCourses = async () => {
    try {
      const data = await fetchCourses();
      setCourses(data);
    } catch {
      // Silencieux — pas de cours
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCourses();
  }, []);

  const handleDelete = async (id: string) => {
    if (!confirm("Supprimer ce cours et toutes ses données ?")) return;
    try {
      await deleteCourse(id);
      setCourses((prev) => prev.filter((c) => c.id !== id));
    } catch {
      alert("Erreur lors de la suppression.");
    }
  };

  return (
    <div className="page-container py-16">
      {/* En-tête */}
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3, ease: "easeOut" }}
      >
        <h1 className="font-display text-[52px] font-bold text-ink-primary leading-tight">
          Vos cours
        </h1>
        <p className="text-ink-secondary mt-3 text-base">
          Uploadez un PDF de cours pour commencer à poser des questions,
          générer des résumés et créer des quiz de révision.
        </p>
      </motion.div>

      {/* Liste / Tableau */}
      <div className="mt-12">
        {loading ? (
          <p className="text-sm text-ink-muted">Chargement…</p>
        ) : courses.length === 0 ? (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: 0.1 }}
            className="text-center py-20"
          >
            <BookOpen size={18} strokeWidth={1.5} className="mx-auto text-ink-muted mb-3" />
            <p className="text-sm text-ink-muted">Aucun cours pour le moment.</p>
            <a
              href="/upload"
              className="inline-block mt-4 text-sm text-accent hover:text-accent-hover
                         border-b border-accent/30 hover:border-accent transition-colors"
            >
              Ajouter votre premier cours
            </a>
          </motion.div>
        ) : (
          <div className="border-t border-border">
            {courses.map((course, i) => (
              <motion.a
                key={course.id}
                href={`/course/${course.id}`}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, ease: "easeOut", delay: i * 0.05 }}
                className="flex items-center justify-between py-4 px-2 border-b border-border
                           hover:bg-accent-light/20 transition-colors duration-200 group"
              >
                <div className="flex items-center gap-4">
                  <FileText
                    size={16}
                    strokeWidth={1.5}
                    className="text-ink-muted group-hover:text-accent transition-colors"
                  />
                  <div>
                    <h3 className="text-sm font-medium text-ink-primary">
                      {course.name}
                    </h3>
                    <p className="text-xs text-ink-muted mt-0.5">
                      {course.pages} pages · {course.chunks_count} segments
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-4">
                  <span className="text-xs text-ink-muted">
                    {new Date(course.created_at).toLocaleDateString("fr-FR", {
                      day: "numeric",
                      month: "short",
                      year: "numeric",
                    })}
                  </span>
                  <button
                    onClick={(e) => {
                      e.preventDefault();
                      e.stopPropagation();
                      handleDelete(course.id);
                    }}
                    className="text-ink-muted hover:text-error transition-colors opacity-0
                               group-hover:opacity-100"
                    title="Supprimer"
                  >
                    <Trash2 size={14} strokeWidth={1.5} />
                  </button>
                </div>
              </motion.a>
            ))}
          </div>
        )}
      </div>

      {/* Lien ajouter en bas */}
      {courses.length > 0 && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
          className="mt-8"
        >
          <a
            href="/upload"
            className="text-sm text-accent hover:text-accent-hover
                       border-b border-accent/30 hover:border-accent transition-colors"
          >
            Ajouter un cours
          </a>
        </motion.div>
      )}
    </div>
  );
}
