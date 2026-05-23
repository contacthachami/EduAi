import { motion } from "framer-motion";
import { MessageSquare, Search, Database, Cpu, FileCheck } from "lucide-react";

const container = {
  hidden: {},
  show: { transition: { staggerChildren: 0.12 } },
};
const item = {
  hidden: { opacity: 0, y: 22 },
  show: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.55, ease: [0.25, 0.46, 0.45, 0.94] as const },
  },
};
const flowItem = {
  hidden: { opacity: 0, scale: 0.9 },
  show: {
    opacity: 1,
    scale: 1,
    transition: { duration: 0.5, ease: [0.25, 0.46, 0.45, 0.94] as const },
  },
};

const flow = [
  {
    icon: MessageSquare,
    label: "Question",
    sub: "de l'étudiant",
    color: "#F2EDE7",
    bg: "#261F1A",
    border: "#3D3530",
  },
  {
    icon: Search,
    label: "Embedding",
    sub: "MiniLM 384d",
    color: "#3B82F6",
    bg: "#1a2236",
    border: "#2a3a5a",
  },
  {
    icon: Database,
    label: "FAISS",
    sub: "Top-3 chunks",
    color: "#8B5CF6",
    bg: "#22183a",
    border: "#3a2560",
  },
  {
    icon: Cpu,
    label: "Llama 3.3",
    sub: "70B via Groq",
    color: "#C46830",
    bg: "#261a12",
    border: "#4a3020",
  },
  {
    icon: FileCheck,
    label: "Réponse",
    sub: "+ sources citées",
    color: "#22C55E",
    bg: "#12261e",
    border: "#1e4030",
  },
];

const highlights = [
  { label: "Streaming SSE", desc: "Réponse progressive en temps réel" },
  { label: "Sources vérifiables", desc: "Références aux passages du cours" },
  { label: "Historique", desc: "Contexte de conversation conservé" },
  { label: "Fallback extractif", desc: "CamemBERT si LLM indisponible" },
];

export default function Slide06() {
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
      <div className="absolute inset-0 grid-bg opacity-35 pointer-events-none" />

      <motion.div
        variants={container}
        initial="hidden"
        animate="show"
        className="relative z-10 flex flex-col items-center px-10 py-12 w-full max-w-5xl"
      >
        <motion.span
          variants={item}
          className="font-body text-xs tracking-widest uppercase text-edu-muted mb-3"
        >
          Fonctionnalité — Q&amp;A
        </motion.span>

        <motion.h2
          variants={item}
          className="font-display font-bold text-center"
          style={{
            fontSize: "clamp(1.8rem, 3.2vw, 3rem)",
            color: "#F2EDE7",
            lineHeight: 1.15,
          }}
        >
          Q&amp;A contextualisé{" "}
          <span style={{ color: "#C46830" }}>avec RAG</span>
        </motion.h2>

        <motion.p
          variants={item}
          className="mt-3 font-body text-edu-secondary text-center max-w-xl"
          style={{ fontSize: "clamp(0.8rem, 1.2vw, 0.95rem)" }}
        >
          Les réponses sont ancrées dans le cours réel de l&apos;étudiant, pas
          dans la mémoire générale du modèle.
        </motion.p>

        {/* Pipeline flow */}
        <motion.div
          variants={container}
          className="mt-10 flex items-center gap-2 flex-wrap justify-center w-full"
        >
          {flow.map((f, idx) => {
            const Icon = f.icon;
            return (
              <div key={idx} className="flex items-center gap-2">
                <motion.div
                  variants={flowItem}
                  className="flex flex-col items-center gap-2 px-5 py-4 rounded-xl"
                  style={{
                    background: f.bg,
                    border: `1px solid ${f.border}`,
                    minWidth: 100,
                  }}
                >
                  <Icon className="w-5 h-5" style={{ color: f.color }} />
                  <span
                    className="font-body font-semibold text-edu-text"
                    style={{ fontSize: "0.85rem" }}
                  >
                    {f.label}
                  </span>
                  <span
                    className="font-mono text-edu-muted text-center"
                    style={{ fontSize: "0.68rem" }}
                  >
                    {f.sub}
                  </span>
                </motion.div>
                {idx < flow.length - 1 && (
                  <motion.span
                    variants={item}
                    className="text-edu-muted text-lg font-light"
                  >
                    →
                  </motion.span>
                )}
              </div>
            );
          })}
        </motion.div>

        {/* RAG badge */}
        <motion.div
          variants={item}
          className="mt-6 px-5 py-2 rounded-full border font-mono text-sm"
          style={{
            background: "rgba(196,104,48,0.08)",
            border: "1px solid rgba(196,104,48,0.25)",
            color: "#C46830",
          }}
        >
          RAG — Retrieval Augmented Generation · Réponse ancrée dans le cours
        </motion.div>

        {/* Highlight features */}
        <motion.div
          variants={container}
          className="mt-8 grid grid-cols-4 gap-3 w-full"
        >
          {highlights.map((h, idx) => (
            <motion.div
              key={idx}
              variants={item}
              className="p-3.5 rounded-xl border border-edu-border text-center"
              style={{ background: "#161210" }}
            >
              <div
                className="font-body font-semibold text-edu-text mb-1"
                style={{ fontSize: "0.82rem" }}
              >
                {h.label}
              </div>
              <div
                className="font-body text-edu-muted"
                style={{ fontSize: "0.72rem" }}
              >
                {h.desc}
              </div>
            </motion.div>
          ))}
        </motion.div>
      </motion.div>
    </div>
  );
}
