import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronLeft, ChevronRight } from "lucide-react";
import type { SlideInfo } from "../App";

interface NavProps {
  current: number;
  total: number;
  slides: SlideInfo[];
  onNavigate: (index: number) => void;
}

export default function Navigation({
  current,
  total,
  slides,
  onNavigate,
}: NavProps) {
  const [showHint, setShowHint] = useState(true);

  useEffect(() => {
    const id = setTimeout(() => setShowHint(false), 5000);
    return () => clearTimeout(id);
  }, []);

  return (
    <>
      {/* Top bar */}
      <div className="fixed top-0 left-0 right-0 z-50 flex items-center justify-between px-6 py-3 pointer-events-none">
        {/* Slide title */}
        <AnimatePresence mode="wait">
          <motion.div
            key={current}
            initial={{ opacity: 0, y: -6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 6 }}
            transition={{ duration: 0.3 }}
            className="font-body text-xs tracking-widest uppercase text-edu-muted"
          >
            {slides[current].title}
          </motion.div>
        </AnimatePresence>

        {/* Counter + timer */}
        <div className="flex items-center gap-5 font-mono text-xs text-edu-muted">
          <span className="flex items-center gap-1.5">
            <span>
              <span className="text-edu-secondary font-semibold">
                {current + 1}
              </span>
              <span className="text-edu-muted"> / {total}</span>
            </span>
          </span>
        </div>
      </div>

      {/* Left arrow */}
      <AnimatePresence>
        {current > 0 && (
          <motion.button
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -10 }}
            onClick={() => onNavigate(current - 1)}
            className="fixed left-3 top-1/2 -translate-y-1/2 z-50 p-2.5 rounded-full
                       text-edu-muted hover:text-edu-text hover:bg-edu-card
                       transition-all duration-200 pointer-events-auto"
            aria-label="Slide précédente"
          >
            <ChevronLeft className="w-5 h-5" />
          </motion.button>
        )}
      </AnimatePresence>

      {/* Right arrow */}
      <AnimatePresence>
        {current < total - 1 && (
          <motion.button
            initial={{ opacity: 0, x: 10 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 10 }}
            onClick={() => onNavigate(current + 1)}
            className="fixed right-3 top-1/2 -translate-y-1/2 z-50 p-2.5 rounded-full
                       text-edu-muted hover:text-edu-text hover:bg-edu-card
                       transition-all duration-200 pointer-events-auto"
            aria-label="Slide suivante"
          >
            <ChevronRight className="w-5 h-5" />
          </motion.button>
        )}
      </AnimatePresence>

      {/* Bottom progress dots */}
      <div className="fixed bottom-5 left-1/2 -translate-x-1/2 z-50 flex items-center gap-1.5 pointer-events-auto">
        {Array.from({ length: total }, (_, i) => (
          <button
            key={i}
            onClick={() => onNavigate(i)}
            aria-label={`Aller au slide ${i + 1}`}
          >
            <motion.div
              animate={{
                width: i === current ? 24 : 6,
                height: 6,
                opacity: i === current ? 1 : i < current ? 0.5 : 0.2,
              }}
              transition={{ duration: 0.3 }}
              className="rounded-full"
              style={{ background: i === current ? "#C46830" : "#6B6359" }}
            />
          </button>
        ))}
      </div>

      {/* ESTE Logo — persistent bottom-right branding on every slide */}
      <div className="fixed bottom-4 right-6 z-50 pointer-events-none">
        <img
          src="./logo_este.png"
          alt="ESTE Essaouira"
          style={{
            height: "44px",
            width: "auto",
            objectFit: "contain",
            opacity: 0.75,
          }}
        />
      </div>

      {/* Keyboard hint */}
      <AnimatePresence>
        {showHint && current === 0 && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            transition={{ delay: 2 }}
            className="fixed bottom-16 left-1/2 -translate-x-1/2 z-50 pointer-events-none
                       flex items-center gap-2 text-edu-muted text-xs font-body"
          >
            <kbd className="px-1.5 py-0.5 rounded border border-edu-border font-mono text-xs">
              ←
            </kbd>
            <span>Flèches ou Espace pour naviguer</span>
            <kbd className="px-1.5 py-0.5 rounded border border-edu-border font-mono text-xs">
              →
            </kbd>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
