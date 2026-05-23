import { motion } from "framer-motion";
import { CheckCircle2, ShieldCheck, FlaskConical } from "lucide-react";

const container = {
  hidden: {},
  show: { transition: { staggerChildren: 0.08 } },
};
const item = {
  hidden: { opacity: 0, scale: 0.88 },
  show: {
    opacity: 1,
    scale: 1,
    transition: { duration: 0.5, ease: [0.25, 0.46, 0.45, 0.94] as const },
  },
};
const textItem = {
  hidden: { opacity: 0, y: 16 },
  show: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.5, ease: [0.25, 0.46, 0.45, 0.94] as const },
  },
};

const modules = [
  {
    name: "Auth JWT",
    desc: "Inscription, connexion, tokens",
    color: "#3B82F6",
  },
  {
    name: "Upload PDF + FAISS",
    desc: "Extraction et indexation",
    color: "#C46830",
  },
  {
    name: "Q&A RAG + Streaming",
    desc: "Recherche sémantique + SSE",
    color: "#8B5CF6",
  },
  {
    name: "Résumé + Cache",
    desc: "Génération et mise en cache",
    color: "#22C55E",
  },
  {
    name: "Quiz + Scoring",
    desc: "Génération et évaluation",
    color: "#F59E0B",
  },
  {
    name: "Flashcards SM-2",
    desc: "Algorithme et révision espacée",
    color: "#EF4444",
  },
  {
    name: "Mindmap ReactFlow",
    desc: "Visualisation interactive",
    color: "#06B6D4",
  },
  {
    name: "Examen chronométré",
    desc: "Timer, soumission, note A–F",
    color: "#A78BFA",
  },
  {
    name: "Panneau Admin",
    desc: "Gestion cours, stats, utilisateurs",
    color: "#34D399",
  },
];

export default function Slide12() {
  return (
    <div className="relative w-full h-full flex flex-col items-center justify-center bg-edu-bg overflow-hidden">
      {/* Top accent */}
      <div
        className="absolute top-0 left-0 right-0 h-[2px]"
        style={{
          background:
            "linear-gradient(90deg, transparent, #22C55E 30%, #22C55E 70%, transparent)",
        }}
      />
      <div className="absolute inset-0 dot-bg opacity-25 pointer-events-none" />

      <motion.div
        variants={{
          hidden: {},
          show: { transition: { staggerChildren: 0.08 } },
        }}
        initial="hidden"
        animate="show"
        className="relative z-10 flex flex-col items-center px-10 py-10 w-full max-w-5xl"
      >
        <motion.span
          variants={textItem}
          className="font-body text-xs tracking-widest uppercase text-edu-muted mb-3"
        >
          Validation
        </motion.span>

        <motion.h2
          variants={textItem}
          className="font-display font-bold text-center"
          style={{
            fontSize: "clamp(1.8rem, 3.2vw, 3rem)",
            color: "#F2EDE7",
            lineHeight: 1.15,
          }}
        >
          Modules validés &amp;{" "}
          <span style={{ color: "#22C55E" }}>fonctionnels</span>
        </motion.h2>

        {/* Module grid */}
        <motion.div
          variants={container}
          className="mt-9 grid grid-cols-3 gap-3.5 w-full"
        >
          {modules.map((m, idx) => (
            <motion.div
              key={idx}
              variants={item}
              className="flex items-start gap-3 p-4 rounded-xl border"
              style={{ background: "#161210", borderColor: "#2A2420" }}
            >
              <CheckCircle2
                className="w-4 h-4 mt-0.5 flex-shrink-0"
                style={{ color: m.color }}
              />
              <div>
                <div
                  className="font-body font-semibold text-edu-text"
                  style={{ fontSize: "0.85rem" }}
                >
                  {m.name}
                </div>
                <div
                  className="font-body text-edu-muted"
                  style={{ fontSize: "0.72rem" }}
                >
                  {m.desc}
                </div>
              </div>
            </motion.div>
          ))}
        </motion.div>

        {/* Test types bar */}
        <motion.div
          variants={textItem}
          className="mt-7 flex items-center gap-8 flex-wrap justify-center"
        >
          {[
            { icon: FlaskConical, label: "Tests unitaires", color: "#3B82F6" },
            {
              icon: ShieldCheck,
              label: "Tests d'intégration",
              color: "#C46830",
            },
            { icon: CheckCircle2, label: "Tests E2E LLM", color: "#22C55E" },
          ].map((t, i) => {
            const Icon = t.icon;
            return (
              <div key={i} className="flex items-center gap-2">
                <Icon className="w-4 h-4" style={{ color: t.color }} />
                <span
                  className="font-body text-edu-secondary"
                  style={{ fontSize: "0.85rem" }}
                >
                  {t.label}
                </span>
              </div>
            );
          })}
        </motion.div>

        {/* Tagline */}
        <motion.div
          variants={textItem}
          className="mt-6 px-8 py-3 rounded-full border"
          style={{
            background: "rgba(34,197,94,0.06)",
            borderColor: "rgba(34,197,94,0.2)",
          }}
        >
          <span
            className="font-display font-semibold italic"
            style={{ fontSize: "clamp(1rem, 1.5vw, 1.2rem)", color: "#F2EDE7" }}
          >
            Fonctionnel. <span style={{ color: "#22C55E" }}>Testé.</span>{" "}
            Déployable.
          </span>
        </motion.div>
      </motion.div>
    </div>
  );
}
