/**
 * FileUploader — Drag & drop pour upload de PDF.
 * Style éditorial sobre, pas de SVG blob.
 */
"use client";

import { useState, useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { motion, AnimatePresence } from "framer-motion";
import { Upload, FileText, X, Loader2 } from "lucide-react";
import { uploadCourse } from "@/lib/api";

interface FileUploaderProps {
  onUploadComplete?: (courseId: string) => void;
}

export default function FileUploader({ onUploadComplete }: FileUploaderProps) {
  const [file, setFile] = useState<File | null>(null);
  const [courseName, setCourseName] = useState("");
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [progress, setProgress] = useState<string | null>(null);

  const onDrop = useCallback((accepted: File[]) => {
    setError(null);
    if (accepted.length > 0) {
      const f = accepted[0];
      if (f.size > 50 * 1024 * 1024) {
        setError("Fichier trop volumineux (maximum 50 MB).");
        return;
      }
      setFile(f);
      if (!courseName) {
        setCourseName(f.name.replace(/\.pdf$/i, ""));
      }
    }
  }, [courseName]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { "application/pdf": [".pdf"] },
    maxFiles: 1,
    multiple: false,
  });

  const handleSubmit = async () => {
    if (!file || !courseName.trim()) return;
    setUploading(true);
    setError(null);
    setProgress("Extraction du texte…");

    try {
      const result = await uploadCourse(file, courseName.trim());
      setProgress(null);
      onUploadComplete?.(result.course_id);
    } catch (err: unknown) {
      let msg = "Erreur lors de l'upload.";
      if (err && typeof err === "object" && "response" in err) {
        const resp = (err as { response?: { data?: { detail?: string } } }).response;
        if (resp?.data?.detail) {
          msg = resp.data.detail;
        }
      } else if (err instanceof Error) {
        msg = err.message;
      }
      setError(msg);
      setProgress(null);
    } finally {
      setUploading(false);
    }
  };

  const removeFile = () => {
    setFile(null);
    setError(null);
    setProgress(null);
  };

  return (
    <div className="space-y-6">
      {/* Zone de drop */}
      <div
        {...getRootProps()}
        className={`
          border border-dashed rounded-card p-10 text-center cursor-pointer
          transition-colors duration-200
          ${isDragActive
            ? "border-accent bg-accent-light"
            : "border-border-strong hover:border-accent hover:bg-accent-light/30"
          }
        `}
      >
        <input {...getInputProps()} />
        <Upload
          size={18}
          strokeWidth={1.5}
          className="mx-auto mb-3 text-ink-muted"
        />
        <p className="text-sm text-ink-secondary">
          {isDragActive
            ? "Déposez le fichier ici…"
            : "Glissez un fichier PDF ici, ou cliquez pour sélectionner"}
        </p>
        <p className="text-xs text-ink-muted mt-1">PDF uniquement — 50 MB max</p>
      </div>

      {/* Fichier sélectionné */}
      <AnimatePresence>
        {file && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.3, ease: "easeOut" }}
            className="card px-4 py-3 flex items-center justify-between"
          >
            <div className="flex items-center gap-3">
              <FileText size={16} strokeWidth={1.5} className="text-accent" />
              <div>
                <p className="text-sm font-medium text-ink-primary">{file.name}</p>
                <p className="text-xs text-ink-muted">
                  {(file.size / (1024 * 1024)).toFixed(1)} MB
                </p>
              </div>
            </div>
            <button
              onClick={removeFile}
              className="text-ink-muted hover:text-error transition-colors"
              aria-label="Retirer le fichier"
            >
              <X size={16} strokeWidth={1.5} />
            </button>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Nom du cours */}
      {file && (
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, ease: "easeOut", delay: 0.05 }}
        >
          <label className="block text-sm text-ink-secondary mb-1.5">
            Nom du cours
          </label>
          <input
            type="text"
            value={courseName}
            onChange={(e) => setCourseName(e.target.value)}
            placeholder="Ex : Deep Learning — M122"
            className="w-full px-4 py-2.5 text-sm border border-border rounded-card
                       bg-bg-card text-ink-primary placeholder-ink-muted
                       focus:outline-none focus:border-accent transition-colors"
          />
        </motion.div>
      )}

      {/* Erreur */}
      {error && (
        <p className="text-sm text-error">{error}</p>
      )}

      {/* Progression */}
      {progress && (
        <div className="flex items-center gap-2 text-sm text-ink-secondary">
          <Loader2 size={14} strokeWidth={1.5} className="animate-spin text-accent" />
          {progress}
        </div>
      )}

      {/* Bouton upload */}
      {file && (
        <motion.button
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.1 }}
          onClick={handleSubmit}
          disabled={uploading || !courseName.trim()}
          className="btn-primary w-full disabled:opacity-40 disabled:cursor-not-allowed"
        >
          {uploading ? "Traitement en cours…" : "Indexer ce cours"}
        </motion.button>
      )}
    </div>
  );
}
