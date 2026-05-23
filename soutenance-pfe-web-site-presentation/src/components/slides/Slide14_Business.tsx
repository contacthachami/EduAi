import { motion } from "framer-motion";
import { TrendingUp, Building2 } from "lucide-react";

const container = {
  hidden: {},
  show: { transition: { staggerChildren: 0.12 } },
};
const item = {
  hidden: { opacity: 0, y: 22 },
  show: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.55, ease: [0.25, 0.46, 0.45, 0.94] as const },
  },
};

const plans = [
  {
    tier: "Free",
    price: "0 MAD",
    sub: "Gratuit pour toujours",
    features: [
      "3 cours maximum",
      "Résumé · Q&A · Quiz · Flashcards",
      "Support communauté",
    ],
    color: "#A8A09A",
    bg: "#1E1A16",
    border: "#3D3530",
    badge: false,
  },
  {
    tier: "Pro",
    price: "49 MAD",
    sub: "par mois",
    features: [
      "Cours illimités",
      "Mode Examen & Carte Mentale",
      "Export PDF · Q&A illimité",
      "Support prioritaire",
    ],
    color: "#C46830",
    bg: "#261a12",
    border: "#4a3020",
    badge: true,
  },
];

const revenue = [
  {
    label: "Année 1",
    amount: "147K MAD",
    value: 147,
    height: "30%",
    color: "#3B82F6",
  },
  {
    label: "Année 2",
    amount: "940K MAD",
    value: 940,
    height: "62%",
    color: "#C46830",
  },
  {
    label: "Année 3",
    amount: "4.2M MAD",
    value: 4200,
    height: "100%",
    color: "#22C55E",
  },
];

export default function Slide14() {
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

      {/* Left — pricing */}
      <motion.div
        variants={container}
        initial="hidden"
        animate="show"
        className="flex-1 flex flex-col justify-center px-12 py-16 border-r border-edu-border"
      >
        <motion.span
          variants={item}
          className="font-body text-xs tracking-widest uppercase text-edu-muted mb-4"
        >
          Modèle d&apos;affaires
        </motion.span>

        <motion.h2
          variants={item}
          className="font-display font-bold"
          style={{
            fontSize: "clamp(1.8rem, 3vw, 2.8rem)",
            color: "#F2EDE7",
            lineHeight: 1.15,
          }}
        >
          SaaS <span style={{ color: "#C46830" }}>Freemium</span>
        </motion.h2>

        <motion.p
          variants={item}
          className="mt-3 font-body text-edu-secondary"
          style={{ fontSize: "0.92rem", maxWidth: 340 }}
        >
          Accès libre pour convaincre, abonnement Pro pour fidéliser.
        </motion.p>

        <div className="mt-8 space-y-4">
          {plans.map((p, idx) => (
            <motion.div
              key={idx}
              variants={item}
              className="p-5 rounded-2xl relative"
              style={{ background: p.bg, border: `1px solid ${p.border}` }}
            >
              {p.badge && (
                <span
                  className="absolute top-3 right-3 px-2.5 py-0.5 rounded-full font-mono text-xs"
                  style={{
                    background: "rgba(196,104,48,0.15)",
                    color: "#C46830",
                  }}
                >
                  Recommandé
                </span>
              )}
              <div className="flex items-baseline gap-2 mb-1">
                <span
                  className="font-display font-bold"
                  style={{ color: p.color, fontSize: "1.6rem" }}
                >
                  {p.price}
                </span>
                <span
                  className="font-body text-edu-muted"
                  style={{ fontSize: "0.8rem" }}
                >
                  {p.sub}
                </span>
              </div>
              <div
                className="font-body font-semibold text-edu-text mb-3"
                style={{ fontSize: "0.88rem" }}
              >
                {p.tier}
              </div>
              <ul className="space-y-1.5">
                {p.features.map((f, fi) => (
                  <li key={fi} className="flex items-center gap-2">
                    <div
                      className="w-1.5 h-1.5 rounded-full flex-shrink-0"
                      style={{ background: p.color }}
                    />
                    <span
                      className="font-body text-edu-secondary"
                      style={{ fontSize: "0.8rem" }}
                    >
                      {f}
                    </span>
                  </li>
                ))}
              </ul>
            </motion.div>
          ))}
        </div>
      </motion.div>

      {/* Right — revenue chart */}
      <motion.div
        variants={container}
        initial="hidden"
        animate="show"
        className="flex-1 flex flex-col justify-center items-center px-12 py-16"
      >
        <motion.div
          variants={item}
          className="flex items-center gap-2 mb-6 self-start"
        >
          <TrendingUp className="w-5 h-5" style={{ color: "#22C55E" }} />
          <span
            className="font-body font-semibold text-edu-text"
            style={{ fontSize: "0.95rem" }}
          >
            Projection de revenus (3 ans)
          </span>
        </motion.div>

        {/* Bar chart */}
        <div className="flex items-end gap-8 h-52 w-full max-w-xs">
          {revenue.map((r, idx) => (
            <div key={idx} className="flex flex-col items-center flex-1 gap-2">
              {/* Amount label */}
              <motion.span
                variants={item}
                className="font-display font-bold"
                style={{ color: r.color, fontSize: "0.82rem" }}
              >
                {r.amount}
              </motion.span>
              {/* Bar */}
              <div
                className="w-full flex flex-col justify-end"
                style={{ height: "10rem" }}
              >
                <motion.div
                  className="w-full rounded-t-lg"
                  style={{ background: r.color, opacity: 0.85 }}
                  initial={{ height: 0 }}
                  animate={{ height: r.height }}
                  transition={{
                    duration: 1,
                    delay: idx * 0.18 + 0.3,
                    ease: "easeOut",
                  }}
                />
              </div>
              {/* Year label */}
              <span
                className="font-body text-edu-muted"
                style={{ fontSize: "0.78rem" }}
              >
                {r.label}
              </span>
            </div>
          ))}
        </div>

        {/* Footer info */}
        <motion.div
          variants={item}
          className="mt-8 p-4 rounded-xl border w-full max-w-xs"
          style={{ background: "#161210", borderColor: "#2A2420" }}
        >
          <div className="flex items-center gap-2 mb-3">
            <Building2 className="w-4 h-4" style={{ color: "#C46830" }} />
            <span
              className="font-body font-semibold text-edu-text"
              style={{ fontSize: "0.85rem" }}
            >
              Perspectives B2B
            </span>
          </div>
          <ul className="space-y-1.5">
            {[
              "Licences établissements scolaires",
              "API pour plateformes e-learning",
              "Coût infra estimé : 1 300 MAD / mois",
            ].map((f, fi) => (
              <li key={fi} className="flex items-start gap-2">
                <div
                  className="mt-1.5 w-1.5 h-1.5 rounded-full flex-shrink-0"
                  style={{ background: "#C46830" }}
                />
                <span
                  className="font-body text-edu-secondary"
                  style={{ fontSize: "0.78rem" }}
                >
                  {f}
                </span>
              </li>
            ))}
          </ul>
        </motion.div>
      </motion.div>
    </div>
  );
}
