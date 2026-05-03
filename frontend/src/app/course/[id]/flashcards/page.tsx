"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import { api } from "@/lib/auth";
import {
  RotateCcw,
  ChevronLeft,
  ChevronRight,
  Brain,
  Check,
  ArrowLeft,
  Download,
} from "lucide-react";

interface Flashcard {
  id: string;
  front: string;
  back: string;
  difficulty: string;
}

export default function FlashcardsPage() {
  const params = useParams();
  const courseId = params.id as string;
  const [cards, setCards] = useState<Flashcard[]>([]);
  const [current, setCurrent] = useState(0);
  const [flipped, setFlipped] = useState(false);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [reviewMode, setReviewMode] = useState(false);

  useEffect(() => {
    loadCards();
  }, [courseId]);

  const loadCards = async () => {
    try {
      const res = await api.get(`/api/flashcards/deck/${courseId}`);
      setCards(res.data.cards || []);
    } catch {
      setCards([]);
    } finally {
      setLoading(false);
    }
  };

  const generate = async () => {
    setGenerating(true);
    try {
      await api.post("/api/flashcards/generate", {
        course_id: courseId,
        count: 15,
      });
      await loadCards();
    } catch (err: any) {
      alert(
        err.response?.data?.detail ||
          "Erreur lors de la génération des flashcards.",
      );
    }
    setGenerating(false);
  };

  const submitReview = async (quality: number) => {
    if (!cards[current]) return;
    try {
      await api.post("/api/flashcards/review", {
        flashcard_id: cards[current].id,
        quality,
      });
    } catch {}
    next();
  };

  const next = () => {
    setFlipped(false);
    setCurrent((c) => (c + 1) % cards.length);
  };

  const prev = () => {
    setFlipped(false);
    setCurrent((c) => (c - 1 + cards.length) % cards.length);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#F6F3EF] flex items-center justify-center">
        <div className="animate-pulse text-[#5F5750]">Chargement...</div>
      </div>
    );
  }

  const handleExport = async () => {
    try {
      const res = await api.get(`/api/export/flashcards/${courseId}`, {
        responseType: "blob",
      });
      const disposition = res.headers["content-disposition"] || "";
      const match = disposition.match(/filename="([^"]+)"/);
      const filename = match ? match[1] : `flashcards_${courseId}.pdf`;
      const url = window.URL.createObjectURL(res.data);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch {
      alert("Erreur lors de l'export PDF des flashcards.");
    }
  };

  if (cards.length === 0) {
    return (
      <div className="min-h-screen bg-[#F6F3EF] flex flex-col items-center justify-center p-6 relative">
        <Link
          href={`/course/${courseId}`}
          className="absolute top-6 left-6 inline-flex items-center gap-1.5 text-sm text-[#5F5750] hover:text-[#B85B2A] transition"
        >
          <ArrowLeft className="w-4 h-4" /> Retour au cours
        </Link>
        <div className="text-center">
          <Brain className="w-16 h-16 text-[#B85B2A] mx-auto mb-4" />
          <h2 className="font-serif text-xl font-bold text-[#171412] mb-2">
            Flashcards
          </h2>
          <p className="text-[#5F5750] mb-6">
            Aucune flashcard générée pour ce cours.
          </p>
          <button
            onClick={generate}
            disabled={generating}
            className="px-6 py-2.5 rounded-md bg-[#B85B2A] text-white font-medium hover:bg-[#9A4B22] transition-colors disabled:opacity-50"
          >
            {generating ? "Génération..." : "Générer les flashcards"}
          </button>
        </div>
      </div>
    );
  }

  const card = cards[current];

  return (
    <div className="min-h-screen bg-[#F6F3EF] flex flex-col items-center justify-center p-6 relative">
      <Link
        href={`/course/${courseId}`}
        className="absolute top-6 left-6 inline-flex items-center gap-1.5 text-sm text-[#5F5750] hover:text-[#B85B2A] transition"
      >
        <ArrowLeft className="w-4 h-4" /> Retour au cours
      </Link>
      <button
        onClick={handleExport}
        title="Télécharger en PDF"
        className="absolute top-6 right-6 inline-flex items-center gap-1.5 text-sm text-[#5F5750] hover:text-[#B85B2A] transition"
      >
        <Download className="w-4 h-4" /> Export PDF
      </button>
      <div className="w-full max-w-lg">
        {/* Progress */}
        <div className="flex items-center justify-between mb-4">
          <span className="text-sm text-[#8D837A]">
            {current + 1} / {cards.length}
          </span>
          <span className="text-xs px-2 py-0.5 rounded bg-[#B85B2A]/10 text-[#B85B2A] font-medium">
            {card.difficulty}
          </span>
        </div>

        {/* Card */}
        <motion.div
          onClick={() => setFlipped(!flipped)}
          className="relative w-full aspect-[3/2] cursor-pointer perspective-1000"
        >
          <AnimatePresence mode="wait">
            <motion.div
              key={flipped ? "back" : "front"}
              initial={{ rotateY: 90, opacity: 0 }}
              animate={{ rotateY: 0, opacity: 1 }}
              exit={{ rotateY: -90, opacity: 0 }}
              transition={{ duration: 0.25 }}
              className={`absolute inset-0 rounded-lg border border-[#DED8D1] shadow-md p-8 flex items-center justify-center text-center ${
                flipped ? "bg-[#B85B2A]/5" : "bg-white"
              }`}
            >
              <div>
                <p className="text-xs text-[#8D837A] mb-2">
                  {flipped ? "Réponse" : "Question"}
                </p>
                <p className="text-lg text-[#171412] font-medium leading-relaxed">
                  {flipped ? card.back : card.front}
                </p>
              </div>
            </motion.div>
          </AnimatePresence>
        </motion.div>

        <p className="text-center text-xs text-[#8D837A] mt-2">
          Cliquer pour retourner
        </p>

        {/* Navigation */}
        <div className="flex items-center justify-center gap-4 mt-6">
          <button
            onClick={prev}
            className="p-2 rounded-full hover:bg-[#DED8D1]/50"
          >
            <ChevronLeft className="w-5 h-5 text-[#5F5750]" />
          </button>
          <button
            onClick={() => setFlipped(!flipped)}
            className="p-2 rounded-full hover:bg-[#DED8D1]/50"
          >
            <RotateCcw className="w-5 h-5 text-[#5F5750]" />
          </button>
          <button
            onClick={next}
            className="p-2 rounded-full hover:bg-[#DED8D1]/50"
          >
            <ChevronRight className="w-5 h-5 text-[#5F5750]" />
          </button>
        </div>

        {/* SM-2 Review buttons (shown when flipped) */}
        {flipped && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-6 flex justify-center gap-2"
          >
            {[
              { q: 1, label: "Raté", color: "bg-red-100 text-red-700" },
              {
                q: 3,
                label: "Difficile",
                color: "bg-yellow-100 text-yellow-700",
              },
              { q: 4, label: "Bien", color: "bg-blue-100 text-blue-700" },
              { q: 5, label: "Facile", color: "bg-green-100 text-green-700" },
            ].map(({ q, label, color }) => (
              <button
                key={q}
                onClick={() => submitReview(q)}
                className={`px-3 py-1.5 rounded-md text-sm font-medium ${color} hover:opacity-80 transition`}
              >
                {label}
              </button>
            ))}
          </motion.div>
        )}
      </div>
    </div>
  );
}
