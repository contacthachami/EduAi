import { motion } from "framer-motion";
import ParticleNetwork from "../ParticleNetwork";
import EduAILogo from "../EduAILogo";

const container = {
  hidden: {},
  show: { transition: { staggerChildren: 0.15 } },
};
const item = {
  hidden: { opacity: 0, y: 28 },
  show: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.7, ease: [0.25, 0.46, 0.45, 0.94] as const },
  },
};
const keyword = {
  hidden: { opacity: 0, scale: 0.8 },
  show: {
    opacity: 1,
    scale: 1,
    transition: { duration: 0.55, ease: [0.25, 0.46, 0.45, 0.94] as const },
  },
};

export default function Slide15() {
  return (
    <div className="relative w-full h-full flex flex-col items-center justify-center bg-edu-bg overflow-hidden">
      {/* Particle network */}
      <div className="absolute inset-0 opacity-25 pointer-events-none">
        <ParticleNetwork />
      </div>

      {/* Radial glow */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background:
            "radial-gradient(ellipse 55% 50% at 50% 50%, rgba(196,104,48,0.10) 0%, transparent 75%)",
        }}
      />

      {/* Top accent */}
      <div
        className="absolute top-0 left-0 right-0 h-[2px]"
        style={{
          background:
            "linear-gradient(90deg, transparent, #C46830 30%, #C46830 70%, transparent)",
        }}
      />
      {/* Bottom accent */}
      <div
        className="absolute bottom-0 left-0 right-0 h-[2px]"
        style={{
          background:
            "linear-gradient(90deg, transparent, #C46830 30%, #C46830 70%, transparent)",
        }}
      />

      <motion.div
        variants={container}
        initial="hidden"
        animate="show"
        className="relative z-10 flex flex-col items-center px-12 py-16 max-w-3xl text-center"
      >
        {/* EduAI Logo */}
        <motion.div variants={item}>
          <EduAILogo size={64} showText={false} />
        </motion.div>

        {/* Quote */}
        <motion.blockquote
          variants={item}
          className="mt-10 font-display italic"
          style={{
            fontSize: "clamp(1.1rem, 2vw, 1.55rem)",
            color: "#F2EDE7",
            lineHeight: 1.6,
          }}
        >
          «&thinsp;EduAI ne remplace pas l&apos;enseignant.{" "}
          <span style={{ color: "#C46830" }}>
            Il donne à chaque étudiant un compagnon de révision intelligent,
            accessible et contextualisé.
          </span>
          &thinsp;»
        </motion.blockquote>

        {/* Three keywords */}
        <motion.div
          variants={container}
          className="mt-10 flex gap-6 justify-center"
        >
          {["Comprendre.", "Réviser.", "S'auto-évaluer."].map((kw, idx) => (
            <motion.span
              key={idx}
              variants={keyword}
              className="font-display font-bold"
              style={{
                fontSize: "clamp(1.1rem, 2vw, 1.4rem)",
                color: idx === 1 ? "#C46830" : "#F2EDE7",
              }}
            >
              {kw}
            </motion.span>
          ))}
        </motion.div>

        {/* Thank you */}
        <motion.div variants={item} className="mt-10">
          <div
            className="font-body text-edu-secondary"
            style={{ fontSize: "0.92rem" }}
          >
            Merci pour votre attention
          </div>
          <div
            className="font-mono text-edu-muted mt-1"
            style={{ fontSize: "0.78rem" }}
          >
            Questions &amp; Réponses
          </div>
        </motion.div>

        {/* ESTE Logo — larger, prominent */}
        <motion.div
          variants={item}
          className="mt-8 flex flex-col items-center gap-2"
        >
          <img
            src="./logo_este.png"
            alt="ESTE Essaouira"
            style={{
              height: "60px",
              width: "auto",
              objectFit: "contain",
              opacity: 0.85,
            }}
            onError={(e) => {
              (e.target as HTMLImageElement).style.display = "none";
            }}
          />
          <span
            className="font-body text-edu-muted"
            style={{ fontSize: "0.72rem" }}
          >
            École Supérieure de Technologie d&apos;Essaouira
          </span>
        </motion.div>
      </motion.div>
    </div>
  );
}
