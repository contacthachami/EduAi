import { useState, useEffect, useCallback } from "react";
import { AnimatePresence, motion } from "framer-motion";
import Navigation from "./components/Navigation";
import Slide01 from "./components/slides/Slide01_Cover";
import Slide02 from "./components/slides/Slide02_Problem";
import Slide03 from "./components/slides/Slide03_Context";
import Slide04 from "./components/slides/Slide04_Vision";
import Slide05 from "./components/slides/Slide05_Journey";
import Slide06 from "./components/slides/Slide06_QA";
import Slide07 from "./components/slides/Slide07_Summary";
import Slide08 from "./components/slides/Slide08_Revision";
import Slide09 from "./components/slides/Slide09_Exam";
import Slide10 from "./components/slides/Slide10_Pipeline";
import Slide11 from "./components/slides/Slide11_Architecture";
import Slide12 from "./components/slides/Slide12_Validation";
import Slide13 from "./components/slides/Slide13_Diff";
import Slide14 from "./components/slides/Slide14_Business";
import Slide15 from "./components/slides/Slide15_Conclusion";
import SlideSommaire from "./components/slides/Slide_Sommaire";
import SlideDemoLive from "./components/slides/Slide_DemoLive";

export interface SlideInfo {
  title: string;
  duration: number;
}

const SLIDES = [
  { component: Slide01, title: "Couverture", duration: 45 },
  { component: SlideSommaire, title: "Sommaire", duration: 30 },
  { component: Slide02, title: "Le Problème", duration: 50 },
  { component: Slide03, title: "Contexte Maroc", duration: 55 },
  { component: Slide04, title: "La Vision EduAI", duration: 55 },
  { component: Slide05, title: "Parcours Utilisateur", duration: 50 },
  { component: Slide06, title: "Q&A RAG", duration: 60 },
  { component: Slide07, title: "Résumé Pédagogique", duration: 55 },
  { component: Slide08, title: "Révision Active", duration: 60 },
  { component: Slide09, title: "Mode Examen", duration: 55 },
  { component: Slide10, title: "Pipeline IA", duration: 75 },
  { component: Slide11, title: "Architecture", duration: 65 },
  { component: Slide12, title: "Validation", duration: 60 },
  { component: Slide13, title: "Différenciation", duration: 60 },
  { component: Slide14, title: "Business Model", duration: 70 },
  { component: SlideDemoLive, title: "Démo Live", duration: 120 },
  { component: Slide15, title: "Conclusion", duration: 60 },
];

const variants = {
  enter: (dir: number) => ({ x: dir > 0 ? 60 : -60, opacity: 0, scale: 0.985 }),
  center: { x: 0, opacity: 1, scale: 1 },
  exit: (dir: number) => ({ x: dir > 0 ? -60 : 60, opacity: 0, scale: 0.985 }),
};

const transition = {
  duration: 0.45,
  ease: [0.25, 0.46, 0.45, 0.94] as [number, number, number, number],
};

export default function App() {
  const [current, setCurrent] = useState(0);
  const [direction, setDirection] = useState(1);

  const goTo = useCallback(
    (index: number) => {
      if (index < 0 || index >= SLIDES.length) return;
      setDirection(index > current ? 1 : -1);
      setCurrent(index);
    },
    [current],
  );

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      switch (e.key) {
        case "ArrowRight":
        case "ArrowDown":
        case " ":
        case "PageDown":
          e.preventDefault();
          goTo(current + 1);
          break;
        case "ArrowLeft":
        case "ArrowUp":
        case "PageUp":
          e.preventDefault();
          goTo(current - 1);
          break;
        case "Home":
          goTo(0);
          break;
        case "End":
          goTo(SLIDES.length - 1);
          break;
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [current, goTo]);

  const SlideComponent = SLIDES[current].component;

  return (
    <div className="relative w-full h-full overflow-hidden bg-edu-bg select-none">
      <AnimatePresence mode="wait" custom={direction}>
        <motion.div
          key={current}
          custom={direction}
          variants={variants}
          initial="enter"
          animate="center"
          exit="exit"
          transition={transition}
          className="absolute inset-0"
        >
          <SlideComponent />
        </motion.div>
      </AnimatePresence>

      <Navigation
        current={current}
        total={SLIDES.length}
        slides={SLIDES.map((s) => ({ title: s.title, duration: s.duration }))}
        onNavigate={goTo}
      />
    </div>
  );
}
