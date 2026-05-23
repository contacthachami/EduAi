import { motion } from "framer-motion";
import {
  Timer,
  FileQuestion,
  Send,
  BarChart3,
  Award,
  CheckCircle2,
} from "lucide-react";

const container = {
  hidden: {},
  show: { transition: { staggerChildren: 0.1 } },
};
const item = {
  hidden: { opacity: 0, y: 22 },
  show: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.55, ease: [0.25, 0.46, 0.45, 0.94] as const },
  },
};

const features = [
  { icon: Timer, text: "Chronomètre intégré", color: "#3B82F6" },
  {
    icon: FileQuestion,
    text: "Questions générées depuis le cours réel",
    color: "#C46830",
  },
  {
    icon: Send,
    text: "Soumission automatique à la fin du temps",
    color: "#8B5CF6",
  },
  { icon: BarChart3, text: "Score, pourcentage et note A–F", color: "#22C55E" },
  {
    icon: Award,
    text: "Corrections pédagogiques détaillées",
    color: "#F59E0B",
  },
  {
    icon: CheckCircle2,
    text: "Conditions proches d'un examen réel",
    color: "#EF4444",
  },
];

const grades = [
  { grade: "A", range: "90–100%", color: "#22C55E" },
  { grade: "B", range: "80–89%", color: "#3B82F6" },
  { grade: "C", range: "70–79%", color: "#F59E0B" },
  { grade: "D", range: "60–69%", color: "#C46830" },
  { grade: "F", range: "< 60%", color: "#EF4444" },
];

export default function Slide09() {
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

      {/* Left — features */}
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
          Fonctionnalité — Examen
        </motion.span>

        <motion.h2
          variants={item}
          className="font-display font-bold"
          style={{
            fontSize: "clamp(1.8rem, 3.2vw, 3rem)",
            color: "#F2EDE7",
            lineHeight: 1.15,
          }}
        >
          Mode Examen <span style={{ color: "#C46830" }}>Simulé</span>
        </motion.h2>

        <motion.p
          variants={item}
          className="mt-4 font-body text-edu-secondary"
          style={{ fontSize: "clamp(0.82rem, 1.2vw, 0.95rem)", maxWidth: 380 }}
        >
          Répondre à la question concrète de l&apos;étudiant avant l&apos;examen
          réel : <em>« Suis-je prêt ? »</em>
        </motion.p>

        <div className="mt-8 space-y-3">
          {features.map((f, idx) => {
            const Icon = f.icon;
            return (
              <motion.div
                key={idx}
                variants={item}
                className="flex items-center gap-3"
              >
                <div
                  className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0"
                  style={{
                    background: `rgba(${f.color === "#3B82F6" ? "59,130,246" : f.color === "#C46830" ? "196,104,48" : f.color === "#8B5CF6" ? "139,92,246" : f.color === "#22C55E" ? "34,197,94" : f.color === "#F59E0B" ? "245,158,11" : "239,68,68"},0.12)`,
                  }}
                >
                  <Icon className="w-3.5 h-3.5" style={{ color: f.color }} />
                </div>
                <span
                  className="font-body text-edu-secondary"
                  style={{ fontSize: "0.88rem" }}
                >
                  {f.text}
                </span>
              </motion.div>
            );
          })}
        </div>
      </motion.div>

      {/* Right — grade scale + circular visual */}
      <motion.div
        variants={container}
        initial="hidden"
        animate="show"
        className="flex-1 flex flex-col justify-center items-center px-12 py-16 gap-8"
      >
        {/* Circular timer visual */}
        <motion.div variants={item} className="relative">
          <svg width={170} height={170} viewBox="0 0 170 170">
            {/* Background circle */}
            <circle
              cx="85"
              cy="85"
              r="72"
              fill="none"
              stroke="#2A2420"
              strokeWidth="10"
            />
            {/* Progress arc — 75% */}
            <motion.circle
              cx="85"
              cy="85"
              r="72"
              fill="none"
              stroke="#C46830"
              strokeWidth="10"
              strokeLinecap="round"
              strokeDasharray={`${2 * Math.PI * 72}`}
              initial={{ strokeDashoffset: 2 * Math.PI * 72 }}
              animate={{ strokeDashoffset: 2 * Math.PI * 72 * 0.25 }}
              transition={{ duration: 1.5, delay: 0.5, ease: "easeOut" }}
              transform="rotate(-90 85 85)"
            />
            {/* Score text */}
            <text
              x="85"
              y="78"
              textAnchor="middle"
              fill="#F2EDE7"
              fontSize="32"
              fontWeight="700"
              fontFamily="'Playfair Display', serif"
            >
              75%
            </text>
            <text
              x="85"
              y="100"
              textAnchor="middle"
              fill="#A8A09A"
              fontSize="12"
              fontFamily="'DM Sans', sans-serif"
            >
              Score exemple
            </text>
          </svg>
        </motion.div>

        {/* Grade scale */}
        <motion.div variants={item} className="w-full max-w-xs">
          <div className="font-body text-edu-muted text-xs mb-3 text-center">
            Échelle de notation
          </div>
          <div className="space-y-1.5">
            {grades.map((g, idx) => (
              <div
                key={idx}
                className="flex items-center gap-3 px-4 py-2 rounded-lg"
                style={{
                  background:
                    g.grade === "B" ? "rgba(59,130,246,0.08)" : "#161210",
                  border:
                    g.grade === "B"
                      ? "1px solid rgba(59,130,246,0.25)"
                      : "1px solid #2A2420",
                }}
              >
                <span
                  className="font-display font-bold w-6 text-center"
                  style={{ color: g.color, fontSize: "1rem" }}
                >
                  {g.grade}
                </span>
                <span
                  className="font-mono text-edu-muted flex-1"
                  style={{ fontSize: "0.75rem" }}
                >
                  {g.range}
                </span>
                <div
                  className="w-2 h-2 rounded-full"
                  style={{ background: g.color }}
                />
              </div>
            ))}
          </div>
        </motion.div>
      </motion.div>
    </div>
  );
}
