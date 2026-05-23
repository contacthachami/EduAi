import { motion } from "framer-motion";
import {
  FileX,
  HelpCircle,
  NotebookPen,
  BarChart2,
  Target,
} from "lucide-react";

const container = {
  hidden: {},
  show: { transition: { staggerChildren: 0.1 } },
};
const item = {
  hidden: { opacity: 0, x: 30 },
  show: {
    opacity: 1,
    x: 0,
    transition: { duration: 0.55, ease: [0.25, 0.46, 0.45, 0.94] as const },
  },
};
const titleAnim = {
  hidden: { opacity: 0, y: 30 },
  show: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.7, ease: [0.25, 0.46, 0.45, 0.94] as const },
  },
};

const problems = [
  {
    icon: FileX,
    text: "PDF dense et passif — aucune interactivité",
    color: "#C46830",
  },
  {
    icon: HelpCircle,
    text: "Aucune aide à la compréhension des notions",
    color: "#C46830",
  },
  {
    icon: NotebookPen,
    text: "Création manuelle et fastidieuse de fiches",
    color: "#C46830",
  },
  {
    icon: Target,
    text: "Pas d'auto-évaluation ni de mesure du niveau",
    color: "#C46830",
  },
  {
    icon: BarChart2,
    text: "Aucun suivi de progression ni d'historique",
    color: "#C46830",
  },
];

export default function Slide02() {
  return (
    <div className="relative w-full h-full flex bg-edu-bg overflow-hidden">
      {/* Subtle grid */}
      <div className="absolute inset-0 grid-bg opacity-50 pointer-events-none" />

      {/* Top accent */}
      <div
        className="absolute top-0 left-0 right-0 h-[2px]"
        style={{
          background:
            "linear-gradient(90deg, transparent, #C46830 30%, #C46830 70%, transparent)",
        }}
      />

      {/* Left side — bold statement */}
      <motion.div
        variants={container}
        initial="hidden"
        animate="show"
        className="flex-1 flex flex-col justify-center px-14 py-16 border-r border-edu-border"
      >
        <motion.div variants={titleAnim} className="mb-4">
          <span className="font-body text-xs tracking-widest uppercase text-edu-muted">
            Le Problème
          </span>
        </motion.div>

        <motion.h2
          variants={titleAnim}
          className="font-display font-bold leading-tight"
          style={{ fontSize: "clamp(2rem, 4vw, 3.8rem)", color: "#F2EDE7" }}
        >
          Le PDF ne suffit
          <br />
          <span style={{ color: "#C46830" }}>pas pour apprendre</span>
        </motion.h2>

        <motion.p
          variants={titleAnim}
          className="mt-6 text-edu-secondary font-body leading-relaxed"
          style={{ fontSize: "clamp(0.9rem, 1.4vw, 1.05rem)", maxWidth: 360 }}
        >
          L&apos;étudiant reçoit un document dense et passif. Sans outil adapté,
          comprendre, mémoriser et s&apos;auto-évaluer restent des tâches
          isolées et chronophages.
        </motion.p>

        <motion.div
          variants={titleAnim}
          className="mt-10 inline-flex items-center gap-3 px-5 py-3 rounded-lg border border-edu-border"
          style={{
            background: "rgba(196,104,48,0.07)",
            maxWidth: "fit-content",
          }}
        >
          <div
            className="w-2 h-2 rounded-full animate-pulse-slow"
            style={{ background: "#C46830" }}
          />
          <span
            className="font-body text-edu-secondary"
            style={{ fontSize: "0.85rem" }}
          >
            Besoin non adressé dans l&apos;enseignement traditionnel
          </span>
        </motion.div>
      </motion.div>

      {/* Right side — problem cards */}
      <motion.div
        variants={container}
        initial="hidden"
        animate="show"
        className="flex-1 flex flex-col justify-center gap-3 px-12 py-16"
      >
        {problems.map((p, idx) => {
          const Icon = p.icon;
          return (
            <motion.div
              key={idx}
              variants={item}
              className="flex items-start gap-4 p-4 rounded-xl border border-edu-border"
              style={{ background: "#161210" }}
            >
              <div
                className="mt-0.5 flex-shrink-0 w-8 h-8 rounded-lg flex items-center justify-center"
                style={{ background: "rgba(196,104,48,0.12)" }}
              >
                <Icon className="w-4 h-4" style={{ color: "#C46830" }} />
              </div>
              <span
                className="font-body text-edu-secondary leading-snug"
                style={{ fontSize: "clamp(0.82rem, 1.2vw, 0.95rem)" }}
              >
                {p.text}
              </span>
            </motion.div>
          );
        })}

        {/* Result badge */}
        <motion.div
          variants={item}
          className="mt-3 p-4 rounded-xl"
          style={{
            background: "rgba(196,104,48,0.06)",
            border: "1px solid rgba(196,104,48,0.18)",
          }}
        >
          <p
            className="font-body text-center"
            style={{
              color: "#C46830",
              fontSize: "clamp(0.82rem, 1.2vw, 0.95rem)",
            }}
          >
            Résultat — L&apos;étudiant reste seul face à son PDF, sans outils
            pour apprendre efficacement.
          </p>
        </motion.div>
      </motion.div>
    </div>
  );
}
