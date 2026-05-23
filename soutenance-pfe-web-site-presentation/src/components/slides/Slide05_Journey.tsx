import { motion } from "framer-motion";
import { UserPlus, Upload, Sparkles } from "lucide-react";

const container = {
  hidden: {},
  show: { transition: { staggerChildren: 0.18 } },
};
const item = {
  hidden: { opacity: 0, y: 28 },
  show: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.6, ease: [0.25, 0.46, 0.45, 0.94] as const },
  },
};

const steps = [
  {
    num: "01",
    icon: UserPlus,
    title: "Créer un compte",
    desc: "Inscription en 30 secondes. Authentification sécurisée avec JWT et gestion des rôles.",
    tags: ["JWT Auth", "Rôles utilisateurs", "Session sécurisée"],
    color: "#3B82F6",
  },
  {
    num: "02",
    icon: Upload,
    title: "Importer un PDF",
    desc: "Téléversement du cours. Extraction automatique du texte, chunking et indexation vectorielle.",
    tags: ["PyMuPDF", "Chunking 400t", "FAISS Index"],
    color: "#C46830",
  },
  {
    num: "03",
    icon: Sparkles,
    title: "Apprendre avec l'IA",
    desc: "Accès immédiat aux 6 modules pédagogiques. Résumé, Q&A, quiz, flashcards, mindmap, examen.",
    tags: ["6 modules actifs", "Llama 3.3 70B", "Historique complet"],
    color: "#22C55E",
  },
];

export default function Slide05() {
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
        className="relative z-10 flex flex-col items-center px-10 py-14 w-full max-w-5xl"
      >
        <motion.span
          variants={item}
          className="font-body text-xs tracking-widest uppercase text-edu-muted mb-4"
        >
          Parcours Utilisateur
        </motion.span>

        <motion.h2
          variants={item}
          className="font-display font-bold text-center"
          style={{
            fontSize: "clamp(1.9rem, 3.5vw, 3.2rem)",
            color: "#F2EDE7",
            lineHeight: 1.15,
          }}
        >
          Simple par design.{" "}
          <span style={{ color: "#C46830" }}>Puissant par nature.</span>
        </motion.h2>

        {/* Steps */}
        <motion.div
          variants={container}
          className="mt-12 grid grid-cols-3 gap-6 w-full"
        >
          {steps.map((s, idx) => {
            const Icon = s.icon;
            return (
              <motion.div
                key={idx}
                variants={item}
                className="flex flex-col p-7 rounded-2xl border border-edu-border relative"
                style={{ background: "#161210" }}
              >
                {/* Number */}
                <span
                  className="font-display font-bold absolute top-5 right-6"
                  style={{
                    fontSize: "2.5rem",
                    color: "rgba(196,104,48,0.1)",
                    lineHeight: 1,
                  }}
                >
                  {s.num}
                </span>

                {/* Icon */}
                <div
                  className="w-11 h-11 rounded-xl flex items-center justify-center mb-5"
                  style={{
                    background: `rgba(${s.color === "#3B82F6" ? "59,130,246" : s.color === "#C46830" ? "196,104,48" : "34,197,94"},0.12)`,
                  }}
                >
                  <Icon className="w-5 h-5" style={{ color: s.color }} />
                </div>

                {/* Title */}
                <h3
                  className="font-display font-semibold text-edu-text mb-3"
                  style={{ fontSize: "clamp(1rem, 1.6vw, 1.2rem)" }}
                >
                  {s.title}
                </h3>

                {/* Desc */}
                <p
                  className="font-body text-edu-secondary leading-relaxed mb-5"
                  style={{ fontSize: "clamp(0.8rem, 1.1vw, 0.9rem)" }}
                >
                  {s.desc}
                </p>

                {/* Tags */}
                <div className="mt-auto flex flex-wrap gap-1.5">
                  {s.tags.map((t, ti) => (
                    <span
                      key={ti}
                      className="px-2.5 py-0.5 rounded-full font-mono border border-edu-border text-edu-muted"
                      style={{ fontSize: "0.7rem", background: "#1E1A16" }}
                    >
                      {t}
                    </span>
                  ))}
                </div>
              </motion.div>
            );
          })}
        </motion.div>

        {/* Connector indicators */}
        <motion.div
          variants={item}
          className="mt-8 flex items-center gap-4 text-edu-muted"
          style={{ fontSize: "0.8rem" }}
        >
          <span className="font-body">30 sec d&apos;inscription</span>
          <span>→</span>
          <span className="font-body">Upload instantané</span>
          <span>→</span>
          <span className="font-body" style={{ color: "#C46830" }}>
            Apprentissage immédiat
          </span>
        </motion.div>
      </motion.div>
    </div>
  );
}
