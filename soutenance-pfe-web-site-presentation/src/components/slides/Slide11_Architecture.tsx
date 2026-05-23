import { motion } from "framer-motion";
import { Monitor, Globe, Server, Cpu, Database, Container } from "lucide-react";

const container = {
  hidden: {},
  show: { transition: { staggerChildren: 0.12 } },
};
const item = {
  hidden: { opacity: 0, x: -30 },
  show: {
    opacity: 1,
    x: 0,
    transition: { duration: 0.55, ease: [0.25, 0.46, 0.45, 0.94] as const },
  },
};

const layers = [
  {
    icon: Monitor,
    title: "Utilisateur",
    sub: "Navigateur web — Chrome, Firefox, Edge",
    techs: [],
    color: "#A8A09A",
    bg: "#1E1A16",
    border: "#3D3530",
    height: 56,
  },
  {
    icon: Globe,
    title: "Frontend",
    sub: "Interface utilisateur réactive",
    techs: [
      "Next.js 14",
      "React 18",
      "TypeScript",
      "Tailwind CSS",
      "Framer Motion",
    ],
    color: "#3B82F6",
    bg: "#1a2236",
    border: "#2a3a5a",
    height: 72,
  },
  {
    icon: Server,
    title: "Backend API",
    sub: "Endpoints REST + SSE streaming",
    techs: [
      "FastAPI",
      "Python 3.11",
      "Pydantic v2",
      "Motor (async)",
      "JWT Auth",
    ],
    color: "#C46830",
    bg: "#261a12",
    border: "#4a3020",
    height: 72,
  },
  {
    icon: Cpu,
    title: "Services IA / NLP",
    sub: "Traitement intelligent du langage",
    techs: [
      "MiniLM 384d",
      "FAISS IndexFlatIP",
      "spaCy",
      "CamemBERT",
      "Groq API",
    ],
    color: "#8B5CF6",
    bg: "#22183a",
    border: "#3a2560",
    height: 72,
  },
  {
    icon: Database,
    title: "Données",
    sub: "Persistance et recherche vectorielle",
    techs: ["MongoDB 7", "FAISS Index (fichier)", "Volumes Docker"],
    color: "#22C55E",
    bg: "#12261e",
    border: "#1e4030",
    height: 68,
  },
  {
    icon: Container,
    title: "Infrastructure",
    sub: "Déploiement et orchestration",
    techs: [
      "Docker Compose",
      "Portainer",
      "Health checks",
      "Réseau Docker interne",
    ],
    color: "#F59E0B",
    bg: "#26200e",
    border: "#4a3a10",
    height: 68,
  },
];

export default function Slide11() {
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

      {/* Left — header */}
      <motion.div
        variants={container}
        initial="hidden"
        animate="show"
        className="w-72 flex flex-col justify-center px-10 py-16 border-r border-edu-border flex-shrink-0"
      >
        <motion.span
          variants={item}
          className="font-body text-xs tracking-widest uppercase text-edu-muted mb-4"
        >
          Architecture
        </motion.span>

        <motion.h2
          variants={item}
          className="font-display font-bold"
          style={{
            fontSize: "clamp(1.7rem, 2.8vw, 2.6rem)",
            color: "#F2EDE7",
            lineHeight: 1.2,
          }}
        >
          Architecture <span style={{ color: "#C46830" }}>Full-Stack</span>
        </motion.h2>

        <motion.p
          variants={item}
          className="mt-5 font-body text-edu-secondary leading-relaxed"
          style={{ fontSize: "clamp(0.8rem, 1.2vw, 0.92rem)" }}
        >
          Conception modulaire, déployable et maintenable — chaque couche est
          isolée et remplaçable.
        </motion.p>

        <motion.div variants={item} className="mt-8 space-y-2">
          {["Modulaire", "Déployable", "Maintenable", "Évolutif"].map(
            (t, i) => (
              <div key={i} className="flex items-center gap-2">
                <div
                  className="w-1.5 h-1.5 rounded-full flex-shrink-0"
                  style={{ background: "#C46830" }}
                />
                <span
                  className="font-body text-edu-secondary"
                  style={{ fontSize: "0.85rem" }}
                >
                  {t}
                </span>
              </div>
            ),
          )}
        </motion.div>
      </motion.div>

      {/* Right — layer stack */}
      <motion.div
        variants={container}
        initial="hidden"
        animate="show"
        className="flex-1 flex flex-col justify-center px-10 py-10 gap-2"
      >
        {layers.map((l, idx) => {
          const Icon = l.icon;
          return (
            <motion.div
              key={idx}
              variants={item}
              className="flex items-center gap-5 px-5 rounded-xl w-full"
              style={{
                background: l.bg,
                border: `1px solid ${l.border}`,
                borderLeft: `3px solid ${l.color}`,
                height: l.height,
              }}
            >
              <div
                className="flex-shrink-0 w-9 h-9 rounded-lg flex items-center justify-center"
                style={{
                  background: `rgba(${l.color === "#3B82F6" ? "59,130,246" : l.color === "#C46830" ? "196,104,48" : l.color === "#8B5CF6" ? "139,92,246" : l.color === "#22C55E" ? "34,197,94" : l.color === "#F59E0B" ? "245,158,11" : "168,160,154"},0.15)`,
                }}
              >
                <Icon className="w-4 h-4" style={{ color: l.color }} />
              </div>

              <div className="flex-1 min-w-0">
                <div
                  className="font-body font-semibold text-edu-text"
                  style={{ fontSize: "0.88rem" }}
                >
                  {l.title}
                </div>
                <div
                  className="font-body text-edu-muted"
                  style={{ fontSize: "0.72rem" }}
                >
                  {l.sub}
                </div>
              </div>

              {l.techs.length > 0 && (
                <div className="flex flex-wrap gap-1.5 justify-end max-w-xs">
                  {l.techs.map((t, ti) => (
                    <span
                      key={ti}
                      className="px-2 py-0.5 rounded font-mono border"
                      style={{
                        fontSize: "0.65rem",
                        background: "#0D0B09",
                        borderColor: l.border,
                        color: l.color,
                      }}
                    >
                      {t}
                    </span>
                  ))}
                </div>
              )}
            </motion.div>
          );
        })}
      </motion.div>
    </div>
  );
}
