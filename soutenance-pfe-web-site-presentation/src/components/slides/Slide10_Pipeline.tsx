import { motion } from "framer-motion";

const container = {
  hidden: {},
  show: { transition: { staggerChildren: 0.1 } },
};
const item = {
  hidden: { opacity: 0, y: 18 },
  show: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.5, ease: [0.25, 0.46, 0.45, 0.94] as const },
  },
};
const stageAnim = {
  hidden: { opacity: 0, scaleX: 0.6 },
  show: {
    opacity: 1,
    scaleX: 1,
    transition: { duration: 0.55, ease: [0.25, 0.46, 0.45, 0.94] as const },
  },
};

const stages = [
  {
    step: "01",
    label: "PDF",
    tech: "PyMuPDF",
    detail: "Extraction texte brut",
    color: "#A8A09A",
    bg: "#1E1A16",
    border: "#3D3530",
  },
  {
    step: "02",
    label: "Chunker",
    tech: "400t / 50t",
    detail: "Overlap pour le contexte",
    color: "#3B82F6",
    bg: "#1a2236",
    border: "#2a3a5a",
  },
  {
    step: "03",
    label: "Embedding",
    tech: "MiniLM",
    detail: "384 dimensions · multilingue",
    color: "#6366F1",
    bg: "#1a1836",
    border: "#2a2860",
  },
  {
    step: "04",
    label: "FAISS",
    tech: "IndexFlatIP",
    detail: "Similarité cosinus normalisée",
    color: "#8B5CF6",
    bg: "#22183a",
    border: "#3a2560",
  },
  {
    step: "05",
    label: "RAG",
    tech: "Top-3",
    detail: "Chunks les plus pertinents",
    color: "#C46830",
    bg: "#261a12",
    border: "#4a3020",
  },
  {
    step: "06",
    label: "Llama 3.3",
    tech: "70B · Groq",
    detail: "Génération contextualisée",
    color: "#E07A3C",
    bg: "#2d1e0f",
    border: "#5a3a1a",
  },
  {
    step: "07",
    label: "Sorties",
    tech: "6 modules",
    detail: "Résumé · Quiz · Flash · …",
    color: "#22C55E",
    bg: "#12261e",
    border: "#1e4030",
  },
];

export default function Slide10() {
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
        className="relative z-10 flex flex-col items-center px-8 py-12 w-full"
      >
        {/* Header */}
        <motion.span
          variants={item}
          className="font-body text-xs tracking-widest uppercase text-edu-muted mb-3"
        >
          Architecture Technique
        </motion.span>

        <motion.h2
          variants={item}
          className="font-display font-bold text-center"
          style={{
            fontSize: "clamp(1.8rem, 3vw, 2.8rem)",
            color: "#F2EDE7",
            lineHeight: 1.15,
          }}
        >
          Pipeline IA —{" "}
          <span style={{ color: "#C46830" }}>Le Coeur Technique</span>
        </motion.h2>

        <motion.p
          variants={item}
          className="mt-3 font-body text-edu-secondary text-center max-w-2xl"
          style={{ fontSize: "clamp(0.8rem, 1.2vw, 0.92rem)" }}
        >
          Du PDF brut à la réponse pédagogique : 7 étapes orchestrées en temps
          réel.
        </motion.p>

        {/* Pipeline stages */}
        <motion.div
          variants={container}
          className="mt-10 flex items-stretch gap-2 w-full max-w-6xl flex-wrap justify-center"
        >
          {stages.map((s, idx) => (
            <div key={idx} className="flex items-center gap-2">
              <motion.div
                variants={stageAnim}
                className="flex flex-col items-center gap-2 px-4 py-5 rounded-xl"
                style={{
                  background: s.bg,
                  border: `1px solid ${s.border}`,
                  minWidth: 110,
                  flex: 1,
                }}
              >
                <span
                  className="font-mono text-edu-muted"
                  style={{ fontSize: "0.65rem" }}
                >
                  {s.step}
                </span>
                <span
                  className="font-display font-semibold"
                  style={{ color: s.color, fontSize: "0.92rem" }}
                >
                  {s.label}
                </span>
                <span
                  className="font-mono font-medium"
                  style={{ color: s.color, fontSize: "0.72rem" }}
                >
                  {s.tech}
                </span>
                <div className="w-full h-px" style={{ background: s.border }} />
                <span
                  className="font-body text-edu-muted text-center"
                  style={{ fontSize: "0.68rem", lineHeight: 1.3 }}
                >
                  {s.detail}
                </span>
              </motion.div>

              {idx < stages.length - 1 && (
                <motion.span
                  variants={item}
                  className="text-edu-muted text-lg font-light flex-shrink-0"
                >
                  →
                </motion.span>
              )}
            </div>
          ))}
        </motion.div>

        {/* Legend */}
        <motion.div
          variants={item}
          className="mt-8 flex flex-wrap gap-5 justify-center"
        >
          {[
            { color: "#A8A09A", label: "Document" },
            { color: "#3B82F6", label: "NLP / Preprocessing" },
            { color: "#8B5CF6", label: "Vector DB" },
            { color: "#E07A3C", label: "LLM / RAG" },
            { color: "#22C55E", label: "Sorties pédagogiques" },
          ].map((l, i) => (
            <div key={i} className="flex items-center gap-2">
              <div
                className="w-2 h-2 rounded-full"
                style={{ background: l.color }}
              />
              <span
                className="font-body text-edu-muted"
                style={{ fontSize: "0.75rem" }}
              >
                {l.label}
              </span>
            </div>
          ))}
        </motion.div>
      </motion.div>
    </div>
  );
}
