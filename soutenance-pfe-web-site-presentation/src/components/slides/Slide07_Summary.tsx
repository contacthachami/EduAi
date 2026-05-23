import { motion } from "framer-motion";
import {
  BrainCircuit,
  Zap,
  Database,
  Download,
  ChevronRight,
} from "lucide-react";

const container = {
  hidden: {},
  show: { transition: { staggerChildren: 0.11 } },
};
const item = {
  hidden: { opacity: 0, y: 20 },
  show: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.55, ease: [0.25, 0.46, 0.45, 0.94] as const },
  },
};

const steps = [
  {
    icon: BrainCircuit,
    label: "Analyse NLP",
    sub: "spaCy — extraction des idées clés",
    color: "#3B82F6",
  },
  {
    icon: Zap,
    label: "Reformulation LLM",
    sub: "Llama 3.3 70B — style pédagogique",
    color: "#C46830",
  },
  {
    icon: Database,
    label: "Mise en cache",
    sub: "MongoDB — évite les recalculs",
    color: "#8B5CF6",
  },
  {
    icon: Download,
    label: "Export PDF",
    sub: "ReportLab — téléchargement direct",
    color: "#22C55E",
  },
];

export default function Slide07() {
  return (
    <div className="relative w-full h-full flex bg-edu-bg overflow-hidden">
      {/* Top accent */}
      <div
        className="absolute top-0 left-0 right-0 h-[2px]"
        style={{
          background:
            "linear-gradient(90deg, transparent, #C46830 30%, #C46830 70%, transparent)",
        }}
      />
      <div className="absolute inset-0 grid-bg opacity-35 pointer-events-none" />

      {/* Left side */}
      <motion.div
        variants={container}
        initial="hidden"
        animate="show"
        className="flex-1 flex flex-col justify-center px-14 py-16 border-r border-edu-border"
      >
        <motion.span
          variants={item}
          className="font-body text-xs tracking-widest uppercase text-edu-muted mb-4"
        >
          Fonctionnalité — Résumé
        </motion.span>

        <motion.h2
          variants={item}
          className="font-display font-bold"
          style={{
            fontSize: "clamp(1.9rem, 3.5vw, 3.2rem)",
            color: "#F2EDE7",
            lineHeight: 1.15,
          }}
        >
          Résumé <span style={{ color: "#C46830" }}>pédagogique</span>
          <br />
          par chapitre
        </motion.h2>

        <motion.p
          variants={item}
          className="mt-6 font-body text-edu-secondary leading-relaxed"
          style={{ fontSize: "clamp(0.85rem, 1.3vw, 1rem)", maxWidth: 380 }}
        >
          Le résumé n&apos;est pas un simple copier-coller. Il identifie les
          concepts essentiels et les reformule dans un style pédagogique adapté
          à la révision.
        </motion.p>

        {/* Feature tags */}
        <motion.div variants={item} className="mt-8 flex flex-wrap gap-2">
          {[
            "Par chapitre",
            "Concepts clés extraits",
            "Mise en cache MongoDB",
            "Export PDF",
          ].map((t, i) => (
            <span
              key={i}
              className="px-3 py-1 rounded-full border border-edu-border font-body text-edu-secondary"
              style={{
                fontSize: "0.78rem",
                background: "rgba(196,104,48,0.06)",
              }}
            >
              {t}
            </span>
          ))}
        </motion.div>

        {/* Objective box */}
        <motion.div
          variants={item}
          className="mt-8 p-5 rounded-xl border"
          style={{
            background: "rgba(196,104,48,0.06)",
            borderColor: "rgba(196,104,48,0.2)",
            maxWidth: 380,
          }}
        >
          <p
            className="font-body text-edu-secondary"
            style={{ fontSize: "0.88rem" }}
          >
            <span style={{ color: "#C46830" }}>Objectif —</span> Identifier
            l&apos;essentiel du cours sans remplacer la lecture originale.
          </p>
        </motion.div>
      </motion.div>

      {/* Right side — pipeline steps */}
      <motion.div
        variants={container}
        initial="hidden"
        animate="show"
        className="flex-1 flex flex-col justify-center px-12 py-16 gap-4"
      >
        <motion.h3
          variants={item}
          className="font-body font-semibold text-edu-muted text-sm mb-2"
        >
          Pipeline de génération
        </motion.h3>

        {steps.map((s, idx) => {
          const Icon = s.icon;
          return (
            <motion.div
              key={idx}
              variants={item}
              className="flex items-start gap-4"
            >
              {/* Connector line */}
              <div className="flex flex-col items-center">
                <div
                  className="w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0"
                  style={{
                    background: `rgba(${s.color === "#3B82F6" ? "59,130,246" : s.color === "#C46830" ? "196,104,48" : s.color === "#8B5CF6" ? "139,92,246" : "34,197,94"},0.12)`,
                  }}
                >
                  <Icon className="w-4 h-4" style={{ color: s.color }} />
                </div>
                {idx < steps.length - 1 && (
                  <div
                    className="w-px h-6 mt-1"
                    style={{ background: "#3D3530" }}
                  />
                )}
              </div>
              <div className="pb-3">
                <div
                  className="font-body font-semibold text-edu-text"
                  style={{ fontSize: "0.92rem" }}
                >
                  {s.label}
                </div>
                <div
                  className="font-mono text-edu-muted"
                  style={{ fontSize: "0.72rem" }}
                >
                  {s.sub}
                </div>
              </div>
            </motion.div>
          );
        })}

        {/* Result */}
        <motion.div
          variants={item}
          className="mt-4 p-4 rounded-xl border border-edu-border"
          style={{ background: "#161210" }}
        >
          <div className="flex items-center gap-2 mb-2">
            <ChevronRight className="w-4 h-4" style={{ color: "#C46830" }} />
            <span
              className="font-body font-semibold text-edu-text"
              style={{ fontSize: "0.88rem" }}
            >
              Résultat
            </span>
          </div>
          <p
            className="font-body text-edu-secondary"
            style={{ fontSize: "0.82rem" }}
          >
            Résumé structuré par chapitre, avec titre, concepts clés et contenu
            synthétique. Exportable en PDF.
          </p>
        </motion.div>
      </motion.div>
    </div>
  );
}
