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
const rowAnim = (delay: number) => ({
  hidden: { opacity: 0, x: -20 },
  show: {
    opacity: 1,
    x: 0,
    transition: {
      duration: 0.5,
      delay,
      ease: [0.25, 0.46, 0.45, 0.94] as const,
    },
  },
});

type Indicator = "yes" | "partial" | "no";
const Check = ({ v }: { v: Indicator }) => {
  if (v === "yes")
    return <span style={{ color: "#22C55E", fontWeight: 700 }}>✓</span>;
  if (v === "partial")
    return <span style={{ color: "#C46830", fontWeight: 700 }}>~</span>;
  return <span style={{ color: "#3D3530", fontWeight: 400 }}>✗</span>;
};

const columns = [
  "RAG",
  "Résumé",
  "Quiz",
  "Flash-\ncards",
  "Mind-\nmap",
  "Examen",
  "PDF\nperso",
  "Prix",
];

const rows: { name: string; vals: Indicator[]; highlight?: boolean }[] = [
  {
    name: "ChatGPT",
    vals: ["partial", "partial", "partial", "no", "no", "no", "no", "no"],
  },
  {
    name: "Quizlet",
    vals: ["no", "no", "yes", "yes", "no", "no", "no", "partial"],
  },
  {
    name: "SciSpace",
    vals: ["partial", "yes", "no", "no", "no", "no", "partial", "no"],
  },
  {
    name: "Notion AI",
    vals: ["no", "partial", "no", "no", "partial", "no", "partial", "no"],
  },
  {
    name: "Coursera/EdX",
    vals: ["no", "no", "yes", "no", "no", "partial", "no", "no"],
  },
  {
    name: "Anki",
    vals: ["no", "no", "partial", "yes", "no", "no", "no", "yes"],
  },
  {
    name: "EduAI",
    vals: ["yes", "yes", "yes", "yes", "yes", "yes", "yes", "yes"],
    highlight: true,
  },
];

export default function Slide13() {
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
          className="font-body text-xs tracking-widest uppercase text-edu-muted mb-4"
        >
          Positionnement
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
          EduAI face <span style={{ color: "#C46830" }}>à la concurrence</span>
        </motion.h2>

        <motion.p
          variants={item}
          className="mt-3 font-body text-edu-secondary text-center max-w-xl"
          style={{ fontSize: "clamp(0.8rem, 1.2vw, 0.9rem)" }}
        >
          Aucun outil existant ne combine les 8 dimensions clés d&apos;EduAI
          dans un seul produit.
        </motion.p>

        {/* Comparison table */}
        <motion.div variants={item} className="mt-8 w-full overflow-x-auto">
          <table
            className="w-full border-collapse"
            style={{ fontSize: "clamp(0.72rem, 1.1vw, 0.85rem)" }}
          >
            <thead>
              <tr>
                <th className="text-left px-4 py-3 font-body font-medium text-edu-muted w-28">
                  Solution
                </th>
                {columns.map((col, ci) => (
                  <th
                    key={ci}
                    className="px-3 py-3 font-body font-medium text-center"
                    style={{
                      color: "#A8A09A",
                      whiteSpace: "pre-line",
                      lineHeight: 1.2,
                    }}
                  >
                    {col}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((row, ri) => (
                <motion.tr
                  key={ri}
                  initial="hidden"
                  animate="show"
                  variants={rowAnim(0.1 * ri + 0.3)}
                  className="border-t"
                  style={{
                    borderColor: row.highlight
                      ? "rgba(196,104,48,0.4)"
                      : "#2A2420",
                    background: row.highlight
                      ? "rgba(196,104,48,0.08)"
                      : "transparent",
                  }}
                >
                  <td
                    className="px-4 py-3 font-body font-semibold"
                    style={{ color: row.highlight ? "#C46830" : "#F2EDE7" }}
                  >
                    {row.name}
                    {row.highlight && (
                      <span
                        className="ml-2 font-mono text-xs px-1.5 py-0.5 rounded"
                        style={{
                          background: "rgba(196,104,48,0.15)",
                          color: "#C46830",
                          fontSize: "0.65rem",
                        }}
                      >
                        Notre solution
                      </span>
                    )}
                  </td>
                  {row.vals.map((v, vi) => (
                    <td
                      key={vi}
                      className="px-3 py-3 text-center font-body"
                      style={{ fontSize: "1rem" }}
                    >
                      <Check v={v} />
                    </td>
                  ))}
                </motion.tr>
              ))}
            </tbody>
          </table>
        </motion.div>

        {/* Legend */}
        <motion.div variants={item} className="mt-6 flex gap-8 justify-center">
          {[
            { sym: "✓", label: "Fonctionnalité présente", color: "#22C55E" },
            { sym: "~", label: "Partielle / limitée", color: "#C46830" },
            { sym: "✗", label: "Absente", color: "#6B6359" },
          ].map((l, i) => (
            <div key={i} className="flex items-center gap-2">
              <span
                style={{ color: l.color, fontWeight: 700, fontSize: "0.9rem" }}
              >
                {l.sym}
              </span>
              <span
                className="font-body text-edu-muted"
                style={{ fontSize: "0.78rem" }}
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
