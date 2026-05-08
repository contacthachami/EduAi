"use client";

import { useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import { Mail, ArrowLeft, CheckCircle, Copy } from "lucide-react";
import axios from "axios";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [resetLink, setResetLink] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const { data } = await axios.post("/api/auth/forgot-password", { email });
      setResetLink(data.reset_link);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Une erreur est survenue.");
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = () => {
    if (resetLink) {
      navigator.clipboard.writeText(window.location.origin + resetLink);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
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
          <p className="text-[#5F5750] text-sm">
            Réinitialisation du mot de passe
          </p>
        </div>

        <div className="bg-white rounded-lg border border-[#DED8D1] shadow-sm p-8">
          <AnimatePresence mode="wait">
            {!resetLink ? (
              <motion.div
                key="form"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
              >
                <h1 className="text-lg font-semibold text-[#171412] mb-1">
                  Mot de passe oublié ?
                </h1>
                <p className="text-sm text-[#5F5750] mb-6">
                  Entrez votre adresse email et nous générerons un lien de
                  réinitialisation.
                </p>

                <form onSubmit={handleSubmit} className="space-y-4">
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
                      ? "Génération en cours…"
                      : "Générer le lien de réinitialisation"}
                  </button>
                </form>
              </motion.div>
            ) : (
              <motion.div
                key="success"
                initial={{ opacity: 0, scale: 0.96 }}
                animate={{ opacity: 1, scale: 1 }}
                className="text-center"
              >
                <div className="flex justify-center mb-4">
                  <div className="w-14 h-14 rounded-full bg-[#E5F2EA] flex items-center justify-center">
                    <CheckCircle className="w-7 h-7 text-[#2F6A4E]" />
                  </div>
                </div>
                <h2 className="text-lg font-semibold text-[#171412] mb-2">
                  Lien généré avec succès
                </h2>
                <p className="text-sm text-[#5F5750] mb-5">
                  En production, ce lien serait envoyé par email. Pour cette
                  démonstration, copiez-le ci-dessous :
                </p>

                <div className="flex items-center gap-2 bg-[#F6F3EF] border border-[#DED8D1] rounded-md px-3 py-2.5 mb-5 text-left">
                  <span className="flex-1 text-xs text-[#5F5750] break-all font-mono">
                    {typeof window !== "undefined"
                      ? window.location.origin + resetLink
                      : resetLink}
                  </span>
                  <button
                    onClick={handleCopy}
                    className="flex-shrink-0 p-1 rounded hover:bg-[#E0D5CB] transition-colors"
                    title="Copier le lien"
                  >
                    <Copy className="w-4 h-4 text-[#8D837A]" />
                  </button>
                </div>

                {copied && (
                  <p className="text-xs text-[#2F6A4E] mb-3">
                    Lien copié dans le presse-papiers !
                  </p>
                )}

                <Link
                  href={resetLink}
                  className="block w-full py-2.5 rounded-md bg-[#B85B2A] text-white font-medium hover:bg-[#9A4B22] transition-colors text-center text-sm"
                >
                  Réinitialiser maintenant
                </Link>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        <div className="mt-4 text-center">
          <Link
            href="/auth"
            className="inline-flex items-center gap-1.5 text-sm text-[#5F5750] hover:text-[#B85B2A] transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            Retour à la connexion
          </Link>
        </div>
      </motion.div>
    </div>
  );
}
