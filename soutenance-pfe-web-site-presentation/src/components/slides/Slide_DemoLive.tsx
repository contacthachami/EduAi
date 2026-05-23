import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Play,
  ExternalLink,
  MonitorPlay,
  CheckCircle2,
  ArrowRight,
  Wifi,
} from "lucide-react";
import EduAILogo from "../EduAILogo";

const DEMO_URL = "http://158.158.17.96:3000/";

export default function SlideDemoLive() {
  const [launched, setLaunched] = useState(false);
  // Ref to the "Lancer la Démo" <a> element.
  // Calling .click() on a real <a target="_blank"> is anchor navigation —
  // browsers NEVER block it with the popup blocker (only window.open() is
  // subject to popup blocking). This is the guaranteed way to open a new tab.
  const demoLinkRef = useRef<HTMLAnchorElement>(null);

  // When the user opens the demo tab, Chrome steals focus.
  // This handler reclaims focus for the presentation tab after a short delay
  // so the next → key press advances the slide instead of going to the demo tab.
  const handleOpen = () => {
    setLaunched(true);
    setTimeout(() => window.focus(), 150);
  };

  // Intercept "next" key events — ONLY when demo not yet launched.
  // Capture phase runs before App.tsx's bubble-phase listener.
  useEffect(() => {
    if (launched) return;
    const onKey = (e: KeyboardEvent) => {
      if (["ArrowRight", "ArrowDown", " ", "PageDown"].includes(e.key)) {
        e.preventDefault();
        e.stopPropagation();
        // Click the actual <a> element — anchor navigation is NEVER blocked
        // by the popup blocker, unlike window.open() which can be blocked.
        demoLinkRef.current?.click();
      }
    };
    window.addEventListener("keydown", onKey, true);
    return () => window.removeEventListener("keydown", onKey, true);
  }, [launched]);

  return (
    <div className="relative w-full h-full flex flex-col items-center justify-center bg-edu-bg overflow-hidden">
      {/* Top + bottom amber accents */}
      <div
        className="absolute top-0 left-0 right-0 h-[2px]"
        style={{
          background:
            "linear-gradient(90deg, transparent, #F59E0B 30%, #F59E0B 70%, transparent)",
        }}
      />
      <div
        className="absolute bottom-0 left-0 right-0 h-[2px]"
        style={{
          background:
            "linear-gradient(90deg, transparent, #F59E0B 30%, #F59E0B 70%, transparent)",
        }}
      />

      {/* Radial glow */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background:
            "radial-gradient(ellipse 65% 60% at 50% 50%, rgba(245,158,11,0.07) 0%, transparent 70%)",
        }}
      />

      {/* Grid background */}
      <div className="absolute inset-0 grid-bg opacity-20 pointer-events-none" />

      <motion.div
        initial={{ opacity: 0, y: 32 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.7, ease: [0.25, 0.46, 0.45, 0.94] }}
        className="relative z-10 flex flex-col items-center text-center px-12 max-w-2xl"
      >
        {/* Live badge */}
        <motion.div
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.2, duration: 0.5 }}
          className="flex items-center gap-2 px-4 py-2 rounded-full border mb-8"
          style={{
            borderColor: "rgba(245,158,11,0.4)",
            background: "rgba(245,158,11,0.08)",
          }}
        >
          <Wifi className="w-3.5 h-3.5" style={{ color: "#F59E0B" }} />
          <span
            className="font-mono text-xs tracking-widest uppercase"
            style={{ color: "#F59E0B" }}
          >
            Démonstration Live
          </span>
          {/* Pulse dot */}
          <span
            className="w-2 h-2 rounded-full animate-pulse"
            style={{ background: "#22C55E" }}
          />
        </motion.div>

        {/* EduAI Logo */}
        <motion.div
          initial={{ opacity: 0, y: 18 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3, duration: 0.6 }}
          className="mb-5"
        >
          <EduAILogo size={72} showText={false} />
        </motion.div>

        {/* Title */}
        <motion.h2
          initial={{ opacity: 0, y: 18 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4, duration: 0.6 }}
          className="font-display font-bold"
          style={{
            fontSize: "clamp(2rem, 4vw, 3.4rem)",
            color: "#F2EDE7",
            lineHeight: 1.1,
          }}
        >
          EduAI <span style={{ color: "#F59E0B" }}>en production</span>
        </motion.h2>

        {/* Subtitle */}
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.52, duration: 0.5 }}
          className="mt-4 font-body text-edu-secondary"
          style={{ fontSize: "clamp(0.88rem, 1.4vw, 1.05rem)", maxWidth: 440 }}
        >
          Explorons ensemble les 6 modules — Q&amp;A, Résumé, Quiz, Flashcards,
          Carte Mentale &amp; Examen.
        </motion.p>

        {/* URL chip — direct link, clicking always works */}
        <motion.a
          href={DEMO_URL}
          target="_blank"
          rel="noopener noreferrer"
          onClick={handleOpen}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.62, duration: 0.5 }}
          className="mt-7 flex items-center gap-2.5 px-5 py-3 rounded-xl border border-edu-border cursor-pointer hover:border-amber-500/40 transition-colors"
          style={{ background: "#161210", textDecoration: "none" }}
        >
          <MonitorPlay className="w-4 h-4" style={{ color: "#F59E0B" }} />
          <span
            className="font-mono text-edu-secondary"
            style={{ fontSize: "0.85rem" }}
          >
            {DEMO_URL}
          </span>
          <ExternalLink className="w-3.5 h-3.5 text-edu-muted" />
        </motion.a>

        {/* CTA Button / Success state */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.75, duration: 0.6 }}
          className="mt-8"
        >
          <AnimatePresence mode="wait">
            {!launched ? (
              <motion.a
                ref={demoLinkRef}
                key="launch-btn"
                href={DEMO_URL}
                target="_blank"
                rel="noopener noreferrer"
                exit={{
                  opacity: 0,
                  scale: 0.88,
                  transition: { duration: 0.25 },
                }}
                onClick={handleOpen}
                whileHover={{ scale: 1.04 }}
                whileTap={{ scale: 0.96 }}
                className="flex items-center gap-3 px-9 py-4 rounded-2xl font-body font-semibold text-white cursor-pointer"
                style={{
                  background:
                    "linear-gradient(135deg, #F59E0B 0%, #D97706 100%)",
                  fontSize: "1.08rem",
                  boxShadow:
                    "0 0 40px rgba(245,158,11,0.28), 0 4px 20px rgba(0,0,0,0.4)",
                  textDecoration: "none",
                }}
              >
                <Play className="w-5 h-5 fill-white" />
                Lancer la Démo
              </motion.a>
            ) : (
              <motion.div
                key="launched-state"
                initial={{ opacity: 0, scale: 0.85 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.4 }}
                className="flex flex-col items-center gap-4"
              >
                {/* Success chip */}
                <div
                  className="flex items-center gap-2.5 px-6 py-3 rounded-2xl"
                  style={{
                    background: "rgba(34,197,94,0.1)",
                    border: "1px solid rgba(34,197,94,0.3)",
                  }}
                >
                  <CheckCircle2
                    className="w-5 h-5"
                    style={{ color: "#22C55E" }}
                  />
                  <span
                    className="font-body font-semibold"
                    style={{ color: "#22C55E", fontSize: "1rem" }}
                  >
                    Démo ouverte dans un nouvel onglet
                  </span>
                </div>
                {/* Next hint */}
                <div
                  className="flex items-center gap-1.5 font-body text-edu-muted"
                  style={{ fontSize: "0.82rem" }}
                >
                  <ArrowRight className="w-3.5 h-3.5" />
                  Appuyez sur{" "}
                  <kbd className="px-1.5 py-0.5 rounded border border-edu-border font-mono text-xs mx-0.5">
                    →
                  </kbd>{" "}
                  pour continuer vers la Conclusion
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>

        {/* Keyboard hint — shown before launch */}
        <AnimatePresence>
          {!launched && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ delay: 1.2, duration: 0.5 }}
              className="mt-6 flex items-center gap-1.5 font-body text-edu-muted"
              style={{ fontSize: "0.78rem" }}
            >
              ou appuyez sur{" "}
              <kbd className="px-1.5 py-0.5 rounded border border-edu-border font-mono text-xs mx-0.5">
                →
              </kbd>
              <kbd className="px-1.5 py-0.5 rounded border border-edu-border font-mono text-xs mx-0.5">
                Espace
              </kbd>{" "}
              pour lancer
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>
    </div>
  );
}
