import { motion } from "framer-motion";
import {
  Target,
  BookOpen,
  Cpu,
  TrendingUp,
  MonitorPlay,
  Flag,
} from "lucide-react";

const sections = [
  {
    num: "01",
    title: "Introduction",
    description: "Problème étudiant, contexte & enjeux du marché marocain",
    icon: Target,
    color: "#3B82F6",
    slides: "Slides 3 – 4",
  },
  {
    num: "02",
    title: "Solution EduAI",
    description: "Vision produit, parcours utilisateur & 6 fonctionnalités IA",
    icon: BookOpen,
    color: "#C46830",
    slides: "Slides 5 – 10",
  },
  {
    num: "03",
    title: "Architecture Technique",
    description: "Pipeline IA, stack Full-Stack & validation des modules",
    icon: Cpu,
    color: "#8B5CF6",
    slides: "Slides 11 – 13",
  },
  {
    num: "04",
    title: "Impact & Business",
    description: "Différenciation concurrentielle & modèle économique SaaS",
    icon: TrendingUp,
    color: "#22C55E",
    slides: "Slides 14 – 15",
  },
  {
    num: "05",
    title: "Démo Live",
    description:
      "Application déployée en production — exploration des 6 modules",
    icon: MonitorPlay,
    color: "#F59E0B",
    slides: "Slide 16",
  },
  {
    num: "06",
    title: "Conclusion",
    description: "Bilan du projet, apports & perspectives futures",
    icon: Flag,
    color: "#EF4444",
    slides: "Slide 17",
  },
];

const container = {
  hidden: {},
  show: { transition: { staggerChildren: 0.09 } },
};
const item = {
  hidden: { opacity: 0, x: -24 },
  show: {
    opacity: 1,
    x: 0,
    transition: { duration: 0.5, ease: [0.25, 0.46, 0.45, 0.94] as const },
  },
};

export default function SlideSommaire() {
  return (
    <div className="relative w-full h-full flex flex-col items-center justify-center bg-edu-bg overflow-hidden">
      {/* Top accent */}
      <div
        className="absolute top-0 left-0 right-0 h-[2px]"
        style={{
          background:
            "linear-gradient(90deg, transparent, #C46830 30%, #C46830 70%, transparent)",
        }}
      />
      <div className="absolute inset-0 grid-bg opacity-30 pointer-events-none" />

      <motion.div
        variants={container}
        initial="hidden"
        animate="show"
        className="relative z-10 w-full max-w-5xl px-12 py-10"
      >
        {/* Header */}
        <motion.div variants={item} className="mb-10 text-center">
          <span className="font-body text-xs tracking-widest uppercase text-edu-muted">
            Soutenance PFE — EduAI
          </span>
          <h2
            className="font-display font-bold mt-2"
            style={{
              fontSize: "clamp(2rem, 3.5vw, 3rem)",
              color: "#F2EDE7",
              lineHeight: 1.15,
            }}
          >
            Plan de <span style={{ color: "#C46830" }}>Présentation</span>
          </h2>
        </motion.div>

        {/* 2-column grid of sections */}
        <div className="grid grid-cols-2 gap-4">
          {sections.map((s, idx) => {
            const Icon = s.icon;
            return (
              <motion.div
                key={idx}
                variants={item}
                className="flex items-center gap-4 p-5 rounded-xl border border-edu-border"
                style={{ background: "#161210" }}
              >
                {/* Icon */}
                <div
                  className="flex-shrink-0 w-11 h-11 rounded-xl flex items-center justify-center"
                  style={{ background: `${s.color}18` }}
                >
                  <Icon className="w-5 h-5" style={{ color: s.color }} />
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-baseline gap-2 flex-wrap">
                    <span
                      className="font-mono font-bold"
                      style={{ color: s.color, fontSize: "0.65rem" }}
                    >
                      {s.num}
                    </span>
                    <span
                      className="font-display font-semibold text-edu-text"
                      style={{ fontSize: "1rem" }}
                    >
                      {s.title}
                    </span>
                    <span
                      className="font-mono text-edu-muted ml-auto"
                      style={{ fontSize: "0.65rem", whiteSpace: "nowrap" }}
                    >
                      {s.slides}
                    </span>
                  </div>
                  <p
                    className="font-body text-edu-secondary mt-1 leading-snug"
                    style={{ fontSize: "0.78rem" }}
                  >
                    {s.description}
                  </p>
                </div>
              </motion.div>
            );
          })}
        </div>

        {/* Duration hint */}
        <motion.div
          variants={item}
          className="mt-8 text-center font-body text-edu-muted"
          style={{ fontSize: "0.78rem" }}
        >
          Durée estimée :{" "}
          <span className="text-edu-secondary">~20 minutes</span> · Suivi
          d&apos;une démonstration live et d&apos;une session Q&amp;R
        </motion.div>
      </motion.div>
    </div>
  );
}
