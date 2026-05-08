"use client";

import { useCallback, useId, useState } from "react";
import { useDropzone } from "react-dropzone";
import { AnimatePresence, motion } from "framer-motion";
import {
  AlertCircle,
  CheckCircle2,
  FileText,
  Loader2,
  Lock,
  Mail,
  UploadCloud,
  X,
} from "lucide-react";
import { uploadCourse } from "@/lib/api";

interface FileUploaderProps {
  onUploadComplete?: (courseId: string) => void;
  submitLabel?: string;
}

const MAX_FILE_SIZE = 50 * 1024 * 1024;

function formatFileSize(bytes: number) {
  const mb = bytes / (1024 * 1024);
  return `${mb < 1 ? mb.toFixed(1) : Math.round(mb * 10) / 10} MB`;
}

function courseNameFromFile(file: File) {
  return file.name
    .replace(/\.pdf$/i, "")
    .replace(/[_-]+/g, " ")
    .trim();
}

export default function FileUploader({
  onUploadComplete,
  submitLabel = "Indexer ce cours",
}: FileUploaderProps) {
  const hintId = useId();
  const errorId = useId();
  const [file, setFile] = useState<File | null>(null);
  const [courseName, setCourseName] = useState("");
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [progress, setProgress] = useState<string | null>(null);

  const onDrop = useCallback(
    (accepted: File[]) => {
      setError(null);
      const selected = accepted[0];
      if (!selected) return;

      setFile(selected);
      if (!courseName.trim()) {
        setCourseName(courseNameFromFile(selected));
      }
    },
    [courseName],
  );

  const { getRootProps, getInputProps, isDragActive, isFocused } = useDropzone({
    onDrop,
    onDropRejected: (rejections) => {
      const rejection = rejections[0];
      const code = rejection?.errors[0]?.code;
      if (code === "file-too-large") {
        setError("Le fichier sélectionné doit être inférieur à 50 MB.");
      } else if (code === "file-invalid-type") {
        setError("Le fichier sélectionné doit être un PDF.");
      } else {
        setError(
          "Impossible de sélectionner ce fichier. Vérifiez le format PDF.",
        );
      }
    },
    accept: { "application/pdf": [".pdf"] },
    maxFiles: 1,
    maxSize: MAX_FILE_SIZE,
    multiple: false,
  });

  const removeFile = () => {
    setFile(null);
    setError(null);
    setProgress(null);
  };

  const handleSubmit = async () => {
    if (!file || !courseName.trim() || uploading) return;
    setUploading(true);
    setError(null);
    setProgress("Préparation du document et extraction du texte...");

    try {
      const result = await uploadCourse(file, courseName.trim());
      setProgress("Cours ajouté. Ouverture de l'espace de travail...");
      onUploadComplete?.(result.course_id);
    } catch (err: unknown) {
      let message =
        "Le cours n'a pas pu être ajouté. Réessayez dans un instant.";
      if (err && typeof err === "object" && "response" in err) {
        const response = (err as { response?: { data?: { detail?: string } } })
          .response;
        if (response?.data?.detail) message = response.data.detail;
      } else if (err instanceof Error) {
        message = err.message;
      }
      setError(message === "UPGRADE_REQUIRED" ? "UPGRADE_REQUIRED" : message);
      setProgress(null);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="space-y-5">
      <div
        {...getRootProps()}
        className={`group rounded-panel border bg-bg-card p-6 text-left transition duration-200 ease-out sm:p-7 ${
          isDragActive
            ? "border-accent bg-accent-soft"
            : "border-dashed border-border-strong hover:border-accent hover:bg-bg-subtle"
        } ${isFocused ? "ring-2 ring-accent ring-offset-2 ring-offset-bg-primary" : ""}`}
        aria-describedby={`${hintId}${error ? ` ${errorId}` : ""}`}
      >
        <input {...getInputProps()} />
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center">
          <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-card border border-border bg-bg-subtle text-accent">
            <UploadCloud size={22} strokeWidth={1.8} />
          </div>
          <div className="min-w-0 flex-1">
            <p className="text-base font-semibold text-ink-primary">
              {isDragActive
                ? "Déposez le PDF dans cette zone"
                : "Déposez un PDF ou sélectionnez un fichier"}
            </p>
            <p id={hintId} className="mt-1 text-sm text-ink-secondary">
              Un seul document PDF, jusqu&apos;à 50 MB. Vous pourrez poser des
              questions, consulter la synthèse et générer un quiz.
            </p>
          </div>
          <span className="btn-secondary pointer-events-none hidden sm:inline-flex">
            Choisir un PDF
          </span>
        </div>
      </div>

      <AnimatePresence initial={false}>
        {file && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.2, ease: "easeOut" }}
            className="panel p-4"
          >
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-card bg-accent-soft text-accent">
                <FileText size={18} strokeWidth={1.8} />
              </div>
              <div className="min-w-0 flex-1">
                <p
                  className="truncate text-sm font-semibold text-ink-primary"
                  title={file.name}
                >
                  {file.name}
                </p>
                <p className="caption">{formatFileSize(file.size)}</p>
              </div>
              <button
                type="button"
                onClick={removeFile}
                className="icon-button"
                aria-label="Retirer le fichier sélectionné"
                disabled={uploading}
              >
                <X size={17} strokeWidth={1.8} />
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {file && (
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.2, ease: "easeOut" }}
        >
          <label htmlFor="course-name" className="label">
            Nom du cours
          </label>
          <input
            id="course-name"
            type="text"
            value={courseName}
            onChange={(event) => setCourseName(event.target.value)}
            placeholder="Ex. Réseaux de neurones convolutifs"
            className="field"
            disabled={uploading}
          />
        </motion.div>
      )}

      {error &&
        (error === "UPGRADE_REQUIRED" ? (
          <div
            id={errorId}
            role="alert"
            className="rounded-lg border border-[#F0D9CE] bg-[#FDF3EE] p-4 flex flex-col gap-3"
          >
            <div className="flex items-center gap-2">
              <Lock size={16} className="text-[#B85B2A] shrink-0" />
              <span className="text-sm font-semibold text-[#171412]">
                Limite du plan gratuit atteinte
              </span>
            </div>
            <p className="text-sm text-[#5F5750] leading-relaxed">
              Vous avez utilisé vos <strong>3 uploads</strong> disponibles avec
              le plan Free. Passez au plan <strong>Pro</strong> pour un accès
              illimité.
            </p>
            <a
              href="mailto:support@eduai.app?subject=Passage%20au%20plan%20Pro"
              className="inline-flex items-center gap-2 self-start px-4 py-2 rounded-md bg-[#B85B2A] text-white text-xs font-semibold hover:bg-[#9A4B22] transition-colors"
            >
              <Mail size={13} />
              Contacter le support
            </a>
          </div>
        ) : (
          <div
            id={errorId}
            role="alert"
            className="status-message status-message-error flex items-start gap-2"
          >
            <AlertCircle
              size={16}
              strokeWidth={1.8}
              className="mt-0.5 shrink-0"
            />
            <span>{error}</span>
          </div>
        ))}

      {progress && (
        <div
          role="status"
          aria-live="polite"
          className="status-message status-message-info flex items-start gap-2"
        >
          {uploading ? (
            <Loader2
              size={16}
              strokeWidth={1.8}
              className="mt-0.5 shrink-0 animate-spin text-accent"
            />
          ) : (
            <CheckCircle2
              size={16}
              strokeWidth={1.8}
              className="mt-0.5 shrink-0 text-success"
            />
          )}
          <span>{progress}</span>
        </div>
      )}

      {file && (
        <motion.button
          type="button"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.2 }}
          onClick={handleSubmit}
          disabled={uploading || !courseName.trim()}
          className="btn-primary w-full"
        >
          {uploading && (
            <Loader2 size={17} strokeWidth={1.8} className="animate-spin" />
          )}
          {uploading ? "Indexation en cours" : submitLabel}
        </motion.button>
      )}
    </div>
  );
}
