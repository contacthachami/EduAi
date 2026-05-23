import { useEffect, useState } from "react";
import { motion } from "framer-motion";

const container = {
  hidden: {},
  show: { transition: { staggerChildren: 0.13 } },
};
const item = {
  hidden: { opacity: 0, y: 24 },
  show: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.6, ease: [0.25, 0.46, 0.45, 0.94] as const },
  },
};

function Counter({ target, suffix = "" }: { target: number; suffix?: string }) {
  const [val, setVal] = useState(0);
  useEffect(() => {
    const dur = 2200;
    const start = Date.now();
    const tick = () => {
      const p = Math.min((Date.now() - start) / dur, 1);
      const e = 1 - Math.pow(1 - p, 3);
      setVal(Math.round(target * e));
      if (p < 1) requestAnimationFrame(tick);
    };
    const raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [target]);
  return (
    <>
      {val.toLocaleString("fr-FR")}
      {suffix}
    </>
  );
}

const stats = [
  {
    value: 1200000,
    label: "étudiants",
    sublabel: "dans l'enseignement supérieur marocain",
    suffix: "",
  },
  {
    value: 400000,
    label: "étudiants connectés",
    sublabel: "ciblables — déjà équipés et connectés",
    suffix: "",
  },
  {
    value: 5000,
    label: "utilisateurs",
    sublabel: "objectif première année d'opération",
    suffix: "",
  },
];

const badges = [
  "Maroc Digital 2030",
  "Adoption numérique croissante",
  "Accessibilité mobile/web",
  "Prix adapté aux étudiants",
];

export default function Slide03() {
  return (
    <div className="relative w-full h-full flex flex-col bg-edu-bg overflow-hidden">
      {/* Top accent */}
      <div
        className="absolute top-0 left-0 right-0 h-[2px]"
        style={{
          background:
            "linear-gradient(90deg, transparent, #C46830 30%, #C46830 70%, transparent)",
        }}
      />

      {/* Dot grid */}
      <div className="absolute inset-0 dot-bg opacity-40 pointer-events-none" />

      <motion.div
        variants={container}
        initial="hidden"
        animate="show"
        className="relative z-10 flex flex-col items-center justify-center flex-1 px-10 py-16 text-center"
      >
        {/* Label */}
        <motion.span
          variants={item}
          className="font-body text-xs tracking-widest uppercase text-edu-muted mb-4"
        >
          Contexte &amp; Marché
        </motion.span>

        {/* Title */}
        <motion.h2
          variants={item}
          className="font-display font-bold"
          style={{
            fontSize: "clamp(2rem, 3.8vw, 3.6rem)",
            color: "#F2EDE7",
            lineHeight: 1.1,
          }}
        >
          Un besoin massif
          <br />
          <span style={{ color: "#C46830" }}>et actuel au Maroc</span>
        </motion.h2>

        {/* Stats */}
        <motion.div
          variants={container}
          className="mt-12 grid grid-cols-3 gap-6 w-full max-w-4xl"
        >
          {stats.map((s, idx) => (
            <motion.div
              key={idx}
              variants={item}
              className="flex flex-col items-center p-7 rounded-2xl border border-edu-border"
              style={{ background: "#161210" }}
            >
              <div
                className="font-display font-bold"
                style={{
                  fontSize: "clamp(2rem, 3.5vw, 3.2rem)",
                  color: "#C46830",
                  lineHeight: 1,
                }}
              >
                <Counter target={s.value} suffix={s.suffix} />
              </div>
              <div
                className="mt-2 font-body font-semibold text-edu-text"
                style={{ fontSize: "clamp(0.85rem, 1.2vw, 1rem)" }}
              >
                {s.label}
              </div>
              <div
                className="mt-1.5 font-body text-edu-muted text-center"
                style={{ fontSize: "clamp(0.72rem, 0.9vw, 0.82rem)" }}
              >
                {s.sublabel}
              </div>
            </motion.div>
          ))}
        </motion.div>

        {/* Context badges */}
        <motion.div
          variants={item}
          className="mt-10 flex flex-wrap justify-center gap-3"
        >
          {badges.map((b, idx) => (
            <span
              key={idx}
              className="px-4 py-1.5 rounded-full border border-edu-border font-body text-edu-secondary"
              style={{
                fontSize: "clamp(0.72rem, 1vw, 0.85rem)",
                background: "rgba(196,104,48,0.05)",
              }}
            >
              {b}
            </span>
          ))}
        </motion.div>
      </motion.div>
    </div>
  );
}
