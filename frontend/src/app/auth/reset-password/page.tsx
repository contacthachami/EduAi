"use client";

import { useState, Suspense } from "react";
import Image from "next/image";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { motion } from "framer-motion";
import { Lock, CheckCircle, ArrowLeft } from "lucide-react";
import axios from "axios";

function ResetPasswordForm() {
  const searchParams = useSearchParams();
  const token = searchParams.get("token") ?? "";

  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (newPassword !== confirmPassword) {
      setError("Les mots de passe ne correspondent pas.");
      return;
    }
    if (!token) {
      setError("Token manquant. Veuillez utiliser le lien complet.");
      return;
    }

    setLoading(true);
    try {
      await axios.post("/api/auth/reset-password", {
        token,
        new_password: newPassword,
      });
      setSuccess(true);
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
          <div className="inline-flex items-center gap-2.5 mb-2">
            <Image
              src="/favicon.svg"
              alt="EduAI"
              width={36}
              height={36}
              className="rounded-lg"
            />
            <span className="font-serif text-2xl font-bold text-[#171412]">
              EduAI
            </span>
          </div>
          <p className="text-[#5F5750] text-sm">Nouveau mot de passe</p>
        </div>

        <div className="bg-white rounded-lg border border-[#DED8D1] shadow-sm p-8">
          {!success ? (
            <>
              <h1 className="text-lg font-semibold text-[#171412] mb-1">
                Choisir un nouveau mot de passe
              </h1>
              <p className="text-sm text-[#5F5750] mb-6">
                Votre nouveau mot de passe doit comporter au moins 6 caractères.
              </p>

              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-[#171412] mb-1">
                    Nouveau mot de passe
                  </label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#8D837A]" />
                    <input
                      type="password"
                      value={newPassword}
                      onChange={(e) => setNewPassword(e.target.value)}
                      className="w-full pl-10 pr-4 py-2.5 rounded-md border border-[#DED8D1] bg-[#F6F3EF] text-[#171412] placeholder:text-[#8D837A] focus:outline-none focus:ring-2 focus:ring-[#B85B2A]/30 focus:border-[#B85B2A]"
                      placeholder="••••••••"
                      required
                      minLength={6}
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-[#171412] mb-1">
                    Confirmer le mot de passe
                  </label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#8D837A]" />
                    <input
                      type="password"
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
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
                    ? "Réinitialisation…"
                    : "Réinitialiser le mot de passe"}
                </button>
              </form>
            </>
          ) : (
            <motion.div
              initial={{ opacity: 0, scale: 0.96 }}
              animate={{ opacity: 1, scale: 1 }}
              className="text-center py-4"
            >
              <div className="flex justify-center mb-4">
                <div className="w-14 h-14 rounded-full bg-[#E5F2EA] flex items-center justify-center">
                  <CheckCircle className="w-7 h-7 text-[#2F6A4E]" />
                </div>
              </div>
              <h2 className="text-lg font-semibold text-[#171412] mb-2">
                Mot de passe réinitialisé !
              </h2>
              <p className="text-sm text-[#5F5750] mb-6">
                Votre mot de passe a été modifié avec succès.
              </p>
              <Link
                href="/auth"
                className="block w-full py-2.5 rounded-md bg-[#B85B2A] text-white font-medium hover:bg-[#9A4B22] transition-colors text-center text-sm"
              >
                Se connecter
              </Link>
            </motion.div>
          )}
        </div>

        {!success && (
          <div className="mt-4 text-center">
            <Link
              href="/auth"
              className="inline-flex items-center gap-1.5 text-sm text-[#5F5750] hover:text-[#B85B2A] transition-colors"
            >
              <ArrowLeft className="w-4 h-4" />
              Retour à la connexion
            </Link>
          </div>
        )}
      </motion.div>
    </div>
  );
}

export default function ResetPasswordPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-[#F6F3EF]" />}>
      <ResetPasswordForm />
    </Suspense>
  );
}
