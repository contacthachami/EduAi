import { motion } from "framer-motion";
import {
  MessageSquare,
  FileText,
  HelpCircle,
  CreditCard,
  Map,
  BookOpen,
} from "lucide-react";

const container = {
  hidden: {},
  show: { transition: { staggerChildren: 0.1 } },
};
const item = {
  hidden: { opacity: 0, y: 20 },
  show: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.55, ease: [0.25, 0.46, 0.45, 0.94] as const },
  },
};

const modules = [
  { icon: FileText, label: "Résumé pédagogique", color: "#3B82F6" },
  { icon: MessageSquare, label: "Q&A contextualisé", color: "#8B5CF6" },
  { icon: HelpCircle, label: "Quiz adaptatifs", color: "#C46830" },
  { icon: CreditCard, label: "Flashcards SM-2", color: "#22C55E" },
  { icon: Map, label: "Carte mentale", color: "#F59E0B" },
  { icon: BookOpen, label: "Examen simulé", color: "#EF4444" },
];

export default function Slide04() {
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

      <div className="absolute inset-0 grid-bg opacity-40 pointer-events-none" />

      <motion.div
        variants={container}
        initial="hidden"
        animate="show"
        className="relative z-10 flex flex-col items-center text-center px-10 py-14 w-full max-w-5xl"
      >
        <motion.span
          variants={item}
          className="font-body text-xs tracking-widest uppercase text-edu-muted mb-4"
        >
          La Vision
        </motion.span>

        <motion.h2
          variants={item}
          className="font-display font-bold"
          style={{
            fontSize: "clamp(1.9rem, 3.6vw, 3.4rem)",
            color: "#F2EDE7",
            lineHeight: 1.15,
          }}
        >
          EduAI transforme un document{" "}
          <span style={{ color: "#C46830" }}>statique</span>
          <br />
          en parcours d&apos;apprentissage{" "}
          <span style={{ color: "#C46830" }}>intelligent</span>
        </motion.h2>

        {/* Flow diagram */}
        <motion.div
          variants={item}
          className="mt-12 flex items-center gap-4 w-full justify-center flex-wrap"
        >
          {/* PDF box */}
          <div className="flex flex-col items-center gap-2">
            <div
              className="px-6 py-4 rounded-xl border border-edu-border flex flex-col items-center gap-2"
              style={{ background: "#1E1A16", minWidth: 110 }}
            >
              <FileText className="w-8 h-8 text-edu-muted" />
              <span className="font-body text-edu-secondary font-medium text-sm">
                PDF Cours
              </span>
            </div>
            <span className="font-body text-edu-muted text-xs">
              Support initial
            </span>
          </div>

          {/* Arrow */}
          <motion.div
            variants={item}
            className="text-edu-muted text-2xl font-light mx-1"
          >
            →
          </motion.div>

          {/* EduAI core */}
          <div className="flex flex-col items-center gap-2">
            <div
              className="px-8 py-4 rounded-xl flex flex-col items-center gap-2"
              style={{
                background:
                  "linear-gradient(135deg, rgba(196,104,48,0.18), rgba(196,104,48,0.08))",
                border: "1px solid rgba(196,104,48,0.35)",
                minWidth: 150,
              }}
            >
              <svg viewBox="0 0 64 64" width={34} height={34}>
                <defs>
                  <linearGradient id="fv-g" x1="0" y1="0" x2="1" y2="1">
                    <stop offset="0%" stopColor="#E07A3C" />
                    <stop offset="100%" stopColor="#C45A1F" />
                  </linearGradient>
                </defs>
                <rect
                  x="2"
                  y="2"
                  width="60"
                  height="60"
                  rx="14"
                  fill="url(#fv-g)"
                />
                <path
                  d="M19 18 H45 V25 H27 V29 H42 V35 H27 V39 H45 V46 H19 Z"
                  fill="#FFF"
                />
                <circle cx="48" cy="18" r="4" fill="#FFE7A3" />
                <circle cx="48" cy="18" r="2" fill="#FFF" />
              </svg>
              <span
                className="font-body font-bold text-sm"
                style={{ color: "#C46830" }}
              >
                Pipeline IA
              </span>
              <span className="font-body text-edu-muted text-xs text-center">
                RAG · NLP · LLM
              </span>
            </div>
            <span className="font-body text-edu-muted text-xs">
              Traitement intelligent
            </span>
          </div>

          {/* Arrow */}
          <motion.div
            variants={item}
            className="text-edu-muted text-2xl font-light mx-1"
          >
            →
          </motion.div>

          {/* Modules grid */}
          <div className="flex flex-col items-center gap-2">
            <div className="grid grid-cols-3 gap-2">
              {modules.map((m, idx) => {
                const Icon = m.icon;
                return (
                  <div
                    key={idx}
                    className="px-3 py-2.5 rounded-lg border border-edu-border flex flex-col items-center gap-1.5"
                    style={{ background: "#161210", minWidth: 90 }}
                  >
                    <Icon className="w-4 h-4" style={{ color: m.color }} />
                    <span
                      className="font-body text-edu-secondary text-center leading-tight"
                      style={{ fontSize: "0.72rem" }}
                    >
                      {m.label}
                    </span>
                  </div>
                );
              })}
            </div>
            <span className="font-body text-edu-muted text-xs">
              6 modules pédagogiques
            </span>
          </div>
        </motion.div>

        {/* Bottom tagline */}
        <motion.p
          variants={item}
          className="mt-10 font-body text-edu-muted"
          style={{ fontSize: "clamp(0.8rem, 1.1vw, 0.95rem)" }}
        >
          Un seul import · Six façons d&apos;apprendre · Aucun effort de
          configuration
        </motion.p>
      </motion.div>
    </div>
  );
}
