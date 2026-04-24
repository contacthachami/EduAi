/**
 * AnimatedTitle — Anime le titre de l'onglet du navigateur en marquee horizontal.
 *
 * Effet : « EduAI — Assistant Pédagogique Intelligent • » défile en boucle
 * caractère par caractère pour donner une touche vivante et professionnelle.
 *
 * Optimisations :
 *  - 200ms par frame → fluide sans surcharger le RAF.
 *  - Pause sur l'onglet inactif (économie batterie).
 *  - Restaure le titre original au démontage.
 */
"use client";

import { useEffect } from "react";

const FULL_TITLE = "EduAI — Assistant Pédagogique Intelligent  •  ";
const FRAME_MS = 220;
const VISIBLE_LENGTH = 30;

export default function AnimatedTitle() {
  useEffect(() => {
    const original = document.title;
    let offset = 0;
    let intervalId: ReturnType<typeof setInterval> | null = null;

    const tick = () => {
      // Crée une fenêtre glissante sur le texte doublé pour un défilement infini
      const doubled = FULL_TITLE + FULL_TITLE;
      const slice = doubled.slice(offset, offset + VISIBLE_LENGTH);
      document.title = slice;
      offset = (offset + 1) % FULL_TITLE.length;
    };

    const start = () => {
      if (intervalId !== null) return;
      tick();
      intervalId = setInterval(tick, FRAME_MS);
    };

    const stop = () => {
      if (intervalId !== null) {
        clearInterval(intervalId);
        intervalId = null;
      }
    };

    const handleVisibility = () => {
      if (document.hidden) {
        stop();
        document.title = "EduAI — Reviens apprendre !";
      } else {
        start();
      }
    };

    start();
    document.addEventListener("visibilitychange", handleVisibility);

    return () => {
      stop();
      document.removeEventListener("visibilitychange", handleVisibility);
      document.title = original;
    };
  }, []);

  return null;
}
