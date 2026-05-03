"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { useAuth } from "@/lib/auth";
import { BookOpen, Mail, Lock, User } from "lucide-react";

export default function AuthPage() {
  const [mode, setMode] = useState<"login" | "register">("login");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { login, register } = useAuth();
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      if (mode === "login") {
        await login(email, password);
      } else {
        await register(name, email, password);
      }
      router.push("/courses");
    } catch (err: any) {
      setError(err.response?.data?.detail || "Une erreur est survenue.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#F6F3EF] flex items-center justify-center px-4">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-md"
      >
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-2 mb-2">
            <BookOpen className="w-8 h-8 text-[#B85B2A]" />
            <span className="font-serif text-2xl font-bold text-[#171412]">
              EduAI
            </span>
          </div>
          <p className="text-[#5F5750] text-sm">
            {mode === "login"
              ? "Connectez-vous à votre espace"
              : "Créez votre compte gratuit"}
          </p>
        </div>

        {/* Card */}
        <div className="bg-white rounded-lg border border-[#DED8D1] shadow-sm p-8">
          <form onSubmit={handleSubmit} className="space-y-4">
            {mode === "register" && (
              <div>
                <label className="block text-sm font-medium text-[#171412] mb-1">
                  Nom
                </label>
                <div className="relative">
                  <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#8D837A]" />
                  <input
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    className="w-full pl-10 pr-4 py-2.5 rounded-md border border-[#DED8D1] bg-[#F6F3EF] text-[#171412] placeholder:text-[#8D837A] focus:outline-none focus:ring-2 focus:ring-[#B85B2A]/30 focus:border-[#B85B2A]"
                    placeholder="Votre nom"
                    required
                  />
                </div>
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-[#171412] mb-1">
                Email
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#8D837A]" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full pl-10 pr-4 py-2.5 rounded-md border border-[#DED8D1] bg-[#F6F3EF] text-[#171412] placeholder:text-[#8D837A] focus:outline-none focus:ring-2 focus:ring-[#B85B2A]/30 focus:border-[#B85B2A]"
                  placeholder="vous@email.com"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-[#171412] mb-1">
                Mot de passe
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#8D837A]" />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full pl-10 pr-4 py-2.5 rounded-md border border-[#DED8D1] bg-[#F6F3EF] text-[#171412] placeholder:text-[#8D837A] focus:outline-none focus:ring-2 focus:ring-[#B85B2A]/30 focus:border-[#B85B2A]"
                  placeholder="••••••••"
                  required
                  minLength={6}
                />
              </div>
            </div>

            {error && (
              <p className="text-red-600 text-sm bg-red-50 p-2 rounded">
                {error}
              </p>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 rounded-md bg-[#B85B2A] text-white font-medium hover:bg-[#9A4B22] transition-colors disabled:opacity-50"
            >
              {loading
                ? "..."
                : mode === "login"
                  ? "Se connecter"
                  : "Créer mon compte"}
            </button>
          </form>

          <div className="mt-6 text-center text-sm text-[#5F5750]">
            {mode === "login" ? (
              <>
                Pas encore de compte ?{" "}
                <button
                  onClick={() => {
                    setMode("register");
                    setError("");
                  }}
                  className="text-[#B85B2A] font-medium hover:underline"
                >
                  S&apos;inscrire
                </button>
              </>
            ) : (
              <>
                Déjà un compte ?{" "}
                <button
                  onClick={() => {
                    setMode("login");
                    setError("");
                  }}
                  className="text-[#B85B2A] font-medium hover:underline"
                >
                  Se connecter
                </button>
              </>
            )}
          </div>
        </div>
      </motion.div>
    </div>
  );
}
