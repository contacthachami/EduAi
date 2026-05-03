"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";
import { motion } from "framer-motion";
import { useAuth } from "@/lib/auth";
import {
  BookOpen,
  Brain,
  Target,
  Map,
  FileText,
  Zap,
  Shield,
  BarChart3,
  ArrowRight,
} from "lucide-react";

const features = [
  {
    icon: Brain,
    title: "Résumés IA",
    desc: "Fiches pédagogiques générées chapitre par chapitre via NLP + LLM.",
  },
  {
    icon: Target,
    title: "Quiz adaptatifs",
    desc: "Questions QCM intelligentes qui ciblent vos lacunes.",
  },
  {
    icon: BookOpen,
    title: "Flashcards SM-2",
    desc: "Révision espacée scientifiquement prouvée pour la mémoire longue.",
  },
  {
    icon: Map,
    title: "Carte mentale",
    desc: "Visualisez les liens entre concepts, chapitres et détails.",
  },
  {
    icon: FileText,
    title: "Mode examen",
    desc: "Simulez un examen en conditions réelles avec chronomètre.",
  },
  {
    icon: BarChart3,
    title: "Suivi de progression",
    desc: "Suivez vos scores et séries de révision au quotidien.",
  },
];

export default function LandingPage() {
  const { user, loading, loadFromStorage } = useAuth();
  const router = useRouter();

  useEffect(() => {
    loadFromStorage();
  }, []);

  useEffect(() => {
    if (!loading && user) {
      router.replace("/courses");
    }
  }, [loading, user, router]);

  if (loading) return null;

  return (
    <div className="min-h-screen bg-[#F6F3EF]">
      {/* Navbar */}
      <nav className="border-b border-[#DED8D1] bg-white/80 backdrop-blur sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Image
              src="/favicon.svg"
              alt=""
              width={26}
              height={26}
              className="rounded-md"
            />
            <span className="font-serif text-xl font-bold text-[#171412]">
              EduAI
            </span>
          </div>
          <button
            onClick={() => router.push("/auth")}
            className="px-4 py-2 rounded-md bg-[#B85B2A] text-white text-sm font-medium hover:bg-[#9A4B22] transition"
          >
            Commencer gratuitement
          </button>
        </div>
      </nav>

      {/* Hero */}
      <section className="max-w-4xl mx-auto px-6 pt-20 pb-16 text-center">
        <motion.h1
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="font-serif text-4xl md:text-5xl font-bold text-[#171412] leading-tight"
        >
          Apprenez mieux,
          <br />
          <span className="text-[#B85B2A]">pas plus longtemps</span>
        </motion.h1>
        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="mt-6 text-lg text-[#5F5750] max-w-2xl mx-auto"
        >
          Uploadez vos cours PDF. EduAI les analyse avec du NLP avancé et génère
          automatiquement des résumés, flashcards, quiz et cartes mentales pour
          booster vos révisions.
        </motion.p>
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="mt-8 flex items-center justify-center gap-4"
        >
          <button
            onClick={() => router.push("/auth")}
            className="px-6 py-3 rounded-md bg-[#B85B2A] text-white font-medium hover:bg-[#9A4B22] transition flex items-center gap-2"
          >
            Créer mon compte <ArrowRight className="w-4 h-4" />
          </button>
        </motion.div>

        {/* Trust badges */}
        <div className="mt-10 flex items-center justify-center gap-6 text-xs text-[#8D837A]">
          <span className="flex items-center gap-1">
            <Shield className="w-3.5 h-3.5" /> Données sécurisées
          </span>
          <span className="flex items-center gap-1">
            <Zap className="w-3.5 h-3.5" /> 100% gratuit
          </span>
          <span className="flex items-center gap-1">
            <Brain className="w-3.5 h-3.5" /> IA française
          </span>
        </div>
      </section>

      {/* Features */}
      <section className="max-w-6xl mx-auto px-6 py-16">
        <h2 className="font-serif text-2xl font-bold text-[#171412] text-center mb-10">
          Tout ce qu'il faut pour réussir
        </h2>
        <div className="grid md:grid-cols-3 gap-6">
          {features.map((f, i) => (
            <motion.div
              key={f.title}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.05 }}
              className="bg-white rounded-lg border border-[#DED8D1] p-6"
            >
              <f.icon className="w-8 h-8 text-[#B85B2A] mb-3" />
              <h3 className="font-medium text-[#171412] mb-1">{f.title}</h3>
              <p className="text-sm text-[#5F5750]">{f.desc}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Pipeline section */}
      <section className="bg-white border-y border-[#DED8D1] py-16">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <h2 className="font-serif text-2xl font-bold text-[#171412] mb-4">
            Pipeline NLP professionnel
          </h2>
          <p className="text-[#5F5750] mb-8">
            EduAI combine plusieurs couches de traitement pour des résultats de
            qualité.
          </p>
          <div className="flex flex-wrap justify-center gap-3">
            {[
              "PyMuPDF",
              "spaCy NLP",
              "BERT Embeddings",
              "FAISS",
              "TextRank",
              "Groq LLM",
            ].map((tech) => (
              <span
                key={tech}
                className="px-3 py-1.5 rounded-full bg-[#F6F3EF] border border-[#DED8D1] text-sm text-[#5F5750] font-medium"
              >
                {tech}
              </span>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="max-w-4xl mx-auto px-6 py-20 text-center">
        <h2 className="font-serif text-3xl font-bold text-[#171412] mb-4">
          Prêt à transformer vos révisions ?
        </h2>
        <button
          onClick={() => router.push("/auth")}
          className="px-8 py-3 rounded-md bg-[#B85B2A] text-white font-medium text-lg hover:bg-[#9A4B22] transition"
        >
          Commencer maintenant
        </button>
      </section>

      {/* Footer */}
      <footer className="border-t border-[#DED8D1] py-6 text-center text-xs text-[#8D837A]">
        © 2026 EduAI — Plateforme d'apprentissage intelligent
      </footer>
    </div>
  );
}
