/**
 * Page d'upload de cours PDF.
 */
"use client";

import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import FileUploader from "@/components/FileUploader";

export default function UploadPage() {
  const router = useRouter();

  const handleComplete = (courseId: string) => {
    router.push(`/course/${courseId}`);
  };

  return (
    <div className="page-container py-16">
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3, ease: "easeOut" }}
      >
        <a
          href="/"
          className="text-xs text-ink-muted hover:text-accent transition-colors"
        >
          ← Retour aux cours
        </a>

        <h1 className="font-display text-3xl font-bold text-ink-primary mt-6">
          Ajouter un cours
        </h1>
        <p className="text-ink-secondary mt-2 text-sm">
          Uploadez un PDF. Le système extrait le texte, découpe le contenu en
          segments et indexe le tout pour la recherche sémantique.
        </p>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3, ease: "easeOut", delay: 0.1 }}
        className="mt-10 max-w-lg"
      >
        <FileUploader onUploadComplete={handleComplete} />
      </motion.div>
    </div>
  );
}
