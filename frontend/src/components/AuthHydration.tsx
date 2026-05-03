"use client";

import { useEffect } from "react";
import { useAuth } from "@/lib/auth";

export default function AuthHydration() {
  const { loadFromStorage } = useAuth();
  useEffect(() => {
    loadFromStorage();
  }, []);
  return null;
}
