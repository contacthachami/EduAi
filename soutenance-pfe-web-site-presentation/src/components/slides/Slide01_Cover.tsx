import { motion } from "framer-motion";
import ParticleNetwork from "../ParticleNetwork";
import EduAILogo from "../EduAILogo";

const c = { hidden: {}, show: { transition: { staggerChildren: 0.14 } } };
const i = {
  hidden: { opacity: 0, y: 28 },
  show: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.65, ease: [0.25, 0.46, 0.45, 0.94] as const },
  },
};

export default function Slide01() {
  return (
    <div className="relative w-full h-full flex flex-col items-center justify-center bg-edu-bg overflow-hidden">
      {/* Particle background */}
      <ParticleNetwork count={80} />

      {/* Radial glow */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background:
            "radial-gradient(ellipse 70% 65% at 50% 50%, rgba(196,104,48,0.07) 0%, transparent 70%)",
        }}
      />

      {/* Top accent line */}
      <motion.div
        initial={{ scaleX: 0 }}
        animate={{ scaleX: 1 }}
        transition={{
          duration: 1.2,
          delay: 0.2,
          ease: [0.25, 0.46, 0.45, 0.94],
        }}
        className="absolute top-0 left-0 right-0 h-[2px] origin-left"
        style={{
          background:
            "linear-gradient(90deg, transparent, #C46830 30%, #C46830 70%, transparent)",
        }}
      />

      {/* ESTE logo — prominent top-left with card frame */}
      <motion.div
        initial={{ opacity: 0, x: -18 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.8, delay: 0.4 }}
        className="absolute top-6 left-8 flex items-center gap-3"
      >
        <div
          className="px-3 py-2 rounded-xl flex items-center gap-3"
          style={{
            background: "rgba(22,18,16,0.85)",
            border: "1px solid rgba(61,53,48,0.7)",
            backdropFilter: "blur(8px)",
          }}
        >
          <img
            src="./logo_este.png"
            alt="ESTE Essaouira"
            style={{ height: "64px", width: "auto", objectFit: "contain" }}
          />
          <div className="flex flex-col" style={{ lineHeight: 1.3 }}>
            <span
              className="font-body font-semibold text-edu-text"
              style={{ fontSize: "0.72rem" }}
            >
              EST d&apos;Essaouira
            </span>
            <span
              className="font-body text-edu-muted"
              style={{ fontSize: "0.64rem" }}
            >
              Université Cadi Ayyad
            </span>
          </div>
        </div>
      </motion.div>

      {/* Main content */}
      <motion.div
        variants={c}
        initial="hidden"
        animate="show"
        className="relative z-10 flex flex-col items-center text-center max-w-4xl px-8"
      >
        {/* Logo */}
        <motion.div variants={i} className="mb-8">
          <EduAILogo size={80} textSize={46} />
        </motion.div>

        {/* Main title */}
        <motion.h1
          variants={i}
          className="font-display font-bold leading-tight tracking-tight"
          style={{ fontSize: "clamp(2.4rem, 5vw, 4.8rem)", color: "#F2EDE7" }}
        >
          Assistant Pédagogique{" "}
          <span style={{ color: "#C46830" }}>Intelligent</span>
        </motion.h1>

        {/* Subtitle */}
        <motion.p
          variants={i}
          className="mt-5 text-edu-secondary font-body max-w-2xl"
          style={{ fontSize: "clamp(1rem, 1.8vw, 1.3rem)" }}
        >
          Transformer un PDF de cours en espace de compréhension, de révision et
          d&apos;auto-évaluation.
        </motion.p>

        {/* Divider */}
        <motion.div
          variants={i}
          className="mt-9 w-20 h-px"
          style={{
            background:
              "linear-gradient(90deg, transparent, #3D3530, transparent)",
          }}
        />

        {/* Author */}
        <motion.div variants={i} className="mt-8 space-y-2 font-body">
          <p
            className="text-edu-text font-semibold"
            style={{ fontSize: "clamp(1rem, 1.6vw, 1.2rem)" }}
          >
            EL Mehdi HACHAMI
          </p>
          <p
            className="text-edu-secondary"
            style={{ fontSize: "clamp(0.8rem, 1.2vw, 0.95rem)" }}
          >
            Bachelor Ingénierie Informatique — IA &amp; Sciences des Données
          </p>
          <p
            className="text-edu-secondary"
            style={{ fontSize: "clamp(0.8rem, 1.2vw, 0.95rem)" }}
          >
            École Supérieure de Technologie d&apos;Essaouira · Université Cadi
            Ayyad
          </p>
        </motion.div>

        {/* Meta row */}
        <motion.div
          variants={i}
          className="mt-6 flex flex-wrap items-center justify-center gap-x-5 gap-y-1 text-edu-muted font-body"
          style={{ fontSize: "clamp(0.72rem, 1vw, 0.85rem)" }}
        >
          <span>Encadrant : Pr. El Mahdi ERRAJI</span>
          <span className="text-edu-border-strong">·</span>
          <span>Entreprise : 2Pi eLearning SARL</span>
          <span className="text-edu-border-strong">·</span>
          <span>Année 2025/2026</span>
        </motion.div>
      </motion.div>

      {/* Bottom accent line */}
      <motion.div
        initial={{ scaleX: 0 }}
        animate={{ scaleX: 1 }}
        transition={{ duration: 1.2, delay: 1, ease: [0.25, 0.46, 0.45, 0.94] }}
        className="absolute bottom-0 left-0 right-0 h-[2px] origin-left"
        style={{
          background:
            "linear-gradient(90deg, transparent, #C46830 30%, #C46830 70%, transparent)",
        }}
      />
    </div>
  );
}
