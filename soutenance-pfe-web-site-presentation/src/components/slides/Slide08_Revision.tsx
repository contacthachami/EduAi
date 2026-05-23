import { motion } from "framer-motion";
import { HelpCircle, CreditCard, Map } from "lucide-react";

const container = {
  hidden: {},
  show: { transition: { staggerChildren: 0.15 } },
};
const item = {
  hidden: { opacity: 0, y: 28 },
  show: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.6, ease: [0.25, 0.46, 0.45, 0.94] as const },
  },
};

const modules = [
  {
    icon: HelpCircle,
    title: "Quiz Intelligents",
    keyword: "Tester",
    color: "#3B82F6",
    bg: "#1a2236",
    border: "#2a3a5a",
    points: [
      "QCM générés depuis le cours",
      "Scoring immédiat avec corrections",
      "3 niveaux : facile / moyen / difficile",
    ],
  },
  {
    icon: CreditCard,
    title: "Flashcards SM-2",
    keyword: "Mémoriser",
    color: "#C46830",
    bg: "#261a12",
    border: "#4a3020",
    points: [
      "Algorithme de répétition espacée",
      "Cartes créées automatiquement",
      "Mémorisation durable (type Anki)",
    ],
  },
  {
    icon: Map,
    title: "Carte Mentale",
    keyword: "Relier",
    color: "#22C55E",
    bg: "#12261e",
    border: "#1e4030",
    points: [
      "ReactFlow — nœuds interactifs",
      "Visualiser les liens entre concepts",
      "Structure arborescente du cours",
    ],
  },
];

export default function Slide08() {
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
      <div className="absolute inset-0 dot-bg opacity-30 pointer-events-none" />

      <motion.div
        variants={container}
        initial="hidden"
        animate="show"
        className="relative z-10 flex flex-col items-center px-10 py-12 w-full max-w-5xl"
      >
        <motion.span
          variants={item}
          className="font-body text-xs tracking-widest uppercase text-edu-muted mb-4"
        >
          Fonctionnalités — Révision
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
          Réviser <span style={{ color: "#C46830" }}>activement</span>, pas
          passivement
        </motion.h2>

        {/* Three columns */}
        <motion.div
          variants={container}
          className="mt-12 grid grid-cols-3 gap-6 w-full"
        >
          {modules.map((m, idx) => {
            const Icon = m.icon;
            return (
              <motion.div
                key={idx}
                variants={item}
                className="flex flex-col p-7 rounded-2xl"
                style={{ background: m.bg, border: `1px solid ${m.border}` }}
              >
                {/* Icon + keyword */}
                <div className="flex items-center justify-between mb-5">
                  <div
                    className="w-11 h-11 rounded-xl flex items-center justify-center"
                    style={{
                      background: `rgba(${m.color === "#3B82F6" ? "59,130,246" : m.color === "#C46830" ? "196,104,48" : "34,197,94"},0.15)`,
                    }}
                  >
                    <Icon className="w-5 h-5" style={{ color: m.color }} />
                  </div>
                  <span
                    className="font-mono font-semibold px-2.5 py-1 rounded-full text-xs"
                    style={{
                      color: m.color,
                      background: `rgba(${m.color === "#3B82F6" ? "59,130,246" : m.color === "#C46830" ? "196,104,48" : "34,197,94"},0.12)`,
                    }}
                  >
                    {m.keyword}
                  </span>
                </div>

                {/* Title */}
                <h3
                  className="font-display font-semibold text-edu-text mb-4"
                  style={{ fontSize: "clamp(1rem, 1.6vw, 1.2rem)" }}
                >
                  {m.title}
                </h3>

                {/* Points */}
                <ul className="space-y-2.5">
                  {m.points.map((p, pi) => (
                    <li key={pi} className="flex items-start gap-2">
                      <div
                        className="mt-1.5 w-1.5 h-1.5 rounded-full flex-shrink-0"
                        style={{ background: m.color }}
                      />
                      <span
                        className="font-body text-edu-secondary"
                        style={{ fontSize: "0.82rem" }}
                      >
                        {p}
                      </span>
                    </li>
                  ))}
                </ul>
              </motion.div>
            );
          })}
        </motion.div>

        <motion.p
          variants={item}
          className="mt-10 font-body text-edu-muted text-center"
          style={{ fontSize: "0.88rem" }}
        >
          Trois approches complémentaires — tester, mémoriser, structurer.
        </motion.p>
      </motion.div>
    </div>
  );
}
