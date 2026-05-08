"use client";

import { useEffect, useState, useCallback } from "react";
import Image from "next/image";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import {
  Users,
  Plus,
  Pencil,
  Trash2,
  X,
  Search,
  Shield,
  BookOpen,
  ChevronDown,
  Eye,
  EyeOff,
  AlertTriangle,
  CheckCircle,
  Loader2,
} from "lucide-react";
import { useAuth, api } from "@/lib/auth";

// ── Types ─────────────────────────────────────────────────────────────────────

interface UserRow {
  id: string;
  name: string;
  email: string;
  role: string;
  plan: string;
  created_at: string;
  courses_count: number;
}

interface Stats {
  total_users: number;
  total_courses: number;
  total_chunks: number;
  admin_count: number;
}

// ── Composants utilitaires ────────────────────────────────────────────────────

function RoleBadge({ role }: { role: string }) {
  return role === "admin" ? (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold bg-[#F0E3DA] text-[#B85B2A]">
      <Shield className="w-3 h-3" />
      Admin
    </span>
  ) : (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-[#ECE7E1] text-[#5F5750]">
      Utilisateur
    </span>
  );
}

function PlanBadge({ plan }: { plan: string }) {
  return plan === "pro" ? (
    <span className="px-2 py-0.5 rounded-full text-xs font-semibold bg-[#E5F2EA] text-[#2F6A4E]">
      Pro
    </span>
  ) : (
    <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-[#F6F3EF] text-[#8D837A] border border-[#DED8D1]">
      Free
    </span>
  );
}

// ── Modal: Ajouter / Modifier ─────────────────────────────────────────────────

interface UserFormProps {
  user?: UserRow | null;
  onClose: () => void;
  onSaved: () => void;
}

function UserFormModal({ user, onClose, onSaved }: UserFormProps) {
  const isEdit = !!user;
  const [name, setName] = useState(user?.name ?? "");
  const [email, setEmail] = useState(user?.email ?? "");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState(user?.role ?? "user");
  const [plan, setPlan] = useState(user?.plan ?? "free");
  const [showPw, setShowPw] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // Admin accounts are always Pro — enforce automatically
  useEffect(() => {
    if (role === "admin") setPlan("pro");
  }, [role]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      if (isEdit) {
        const payload: Record<string, string> = { name, email, role, plan };
        if (password) payload.password = password;
        await api.put(`/api/admin/users/${user!.id}`, payload);
      } else {
        await api.post("/api/admin/users", {
          name,
          email,
          password,
          role,
          plan,
        });
      }
      onSaved();
      onClose();
    } catch (err: any) {
      setError(err.response?.data?.detail || "Une erreur est survenue.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm px-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="bg-white rounded-xl border border-[#DED8D1] shadow-xl w-full max-w-md"
      >
        <div className="flex items-center justify-between p-5 border-b border-[#DED8D1]">
          <h2 className="font-semibold text-[#171412] text-base">
            {isEdit ? "Modifier le compte" : "Ajouter un compte"}
          </h2>
          <button
            onClick={onClose}
            aria-label="Fermer"
            className="p-1.5 rounded-md hover:bg-[#F6F3EF] transition-colors"
          >
            <X className="w-5 h-5 text-[#8D837A]" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-5 space-y-4">
          {/* Nom */}
          <div>
            <label className="block text-sm font-medium text-[#171412] mb-1">
              Nom
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              minLength={2}
              className="w-full px-3 py-2.5 rounded-md border border-[#DED8D1] bg-[#F6F3EF] text-[#171412] placeholder:text-[#8D837A] focus:outline-none focus:ring-2 focus:ring-[#B85B2A]/30 focus:border-[#B85B2A] text-sm"
              placeholder="Nom complet"
            />
          </div>

          {/* Email */}
          <div>
            <label className="block text-sm font-medium text-[#171412] mb-1">
              Email
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="w-full px-3 py-2.5 rounded-md border border-[#DED8D1] bg-[#F6F3EF] text-[#171412] placeholder:text-[#8D837A] focus:outline-none focus:ring-2 focus:ring-[#B85B2A]/30 focus:border-[#B85B2A] text-sm"
              placeholder="email@exemple.com"
            />
          </div>

          {/* Mot de passe */}
          <div>
            <label className="block text-sm font-medium text-[#171412] mb-1">
              Mot de passe{" "}
              {isEdit && (
                <span className="text-[#8D837A] font-normal">
                  (laisser vide pour ne pas changer)
                </span>
              )}
            </label>
            <div className="relative">
              <input
                type={showPw ? "text" : "password"}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required={!isEdit}
                minLength={isEdit && !password ? undefined : 6}
                className="w-full pr-10 px-3 py-2.5 rounded-md border border-[#DED8D1] bg-[#F6F3EF] text-[#171412] placeholder:text-[#8D837A] focus:outline-none focus:ring-2 focus:ring-[#B85B2A]/30 focus:border-[#B85B2A] text-sm"
                placeholder={
                  isEdit
                    ? "Nouveau mot de passe…"
                    : "Mot de passe (min. 6 car.)"
                }
              />
              <button
                type="button"
                onClick={() => setShowPw((v) => !v)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-[#8D837A] hover:text-[#5F5750]"
              >
                {showPw ? (
                  <EyeOff className="w-4 h-4" />
                ) : (
                  <Eye className="w-4 h-4" />
                )}
              </button>
            </div>
          </div>

          {/* Rôle + Plan */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-medium text-[#171412] mb-1">
                Rôle
              </label>
              <div className="relative">
                <select
                  aria-label="Rôle du compte"
                  value={role}
                  onChange={(e) => setRole(e.target.value)}
                  className="w-full appearance-none px-3 py-2.5 rounded-md border border-[#DED8D1] bg-[#F6F3EF] text-[#171412] focus:outline-none focus:ring-2 focus:ring-[#B85B2A]/30 focus:border-[#B85B2A] text-sm"
                >
                  <option value="user">Utilisateur</option>
                  <option value="admin">Admin</option>
                </select>
                <ChevronDown className="pointer-events-none absolute right-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-[#8D837A]" />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-[#171412] mb-1">
                Plan
              </label>
              <div className="relative">
                <select
                  aria-label="Plan du compte"
                  value={plan}
                  onChange={(e) => setPlan(e.target.value)}
                  disabled={role === "admin"}
                  className={`w-full appearance-none px-3 py-2.5 rounded-md border border-[#DED8D1] bg-[#F6F3EF] text-[#171412] focus:outline-none focus:ring-2 focus:ring-[#B85B2A]/30 focus:border-[#B85B2A] text-sm ${
                    role === "admin" ? "opacity-60 cursor-not-allowed" : ""
                  }`}
                >
                  {role === "admin" ? (
                    <option value="pro">Pro</option>
                  ) : (
                    <>
                      <option value="free">Free</option>
                      <option value="pro">Pro</option>
                    </>
                  )}
                </select>
                <ChevronDown className="pointer-events-none absolute right-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-[#8D837A]" />
              </div>
              {role === "admin" && (
                <p className="mt-1 text-xs text-[#8D837A]">
                  Les admins ont toujours le plan Pro.
                </p>
              )}
            </div>
          </div>

          {error && (
            <p className="text-sm text-red-600 bg-red-50 p-2.5 rounded-md">
              {error}
            </p>
          )}

          <div className="flex gap-3 pt-1">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 py-2.5 rounded-md border border-[#DED8D1] text-[#5F5750] text-sm font-medium hover:bg-[#F6F3EF] transition-colors"
            >
              Annuler
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex-1 py-2.5 rounded-md bg-[#B85B2A] text-white text-sm font-semibold hover:bg-[#9A4B22] transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {loading && <Loader2 className="w-4 h-4 animate-spin" />}
              {isEdit ? "Enregistrer" : "Créer le compte"}
            </button>
          </div>
        </form>
      </motion.div>
    </div>
  );
}

// ── Modal: Confirmation de suppression ────────────────────────────────────────

interface DeleteConfirmProps {
  user: UserRow;
  onClose: () => void;
  onDeleted: () => void;
}

function DeleteConfirmModal({ user, onClose, onDeleted }: DeleteConfirmProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleDelete = async () => {
    setLoading(true);
    setError("");
    try {
      await api.delete(`/api/admin/users/${user.id}`);
      onDeleted();
      onClose();
    } catch (err: any) {
      setError(
        err.response?.data?.detail || "Impossible de supprimer ce compte.",
      );
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm px-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="bg-white rounded-xl border border-[#DED8D1] shadow-xl w-full max-w-sm p-6"
      >
        <div className="flex justify-center mb-4">
          <div className="w-12 h-12 rounded-full bg-red-50 flex items-center justify-center">
            <AlertTriangle className="w-6 h-6 text-red-500" />
          </div>
        </div>
        <h2 className="text-center font-semibold text-[#171412] mb-2">
          Supprimer ce compte ?
        </h2>
        <p className="text-center text-sm text-[#5F5750] mb-1">
          <span className="font-medium text-[#171412]">{user.name}</span> —{" "}
          {user.email}
        </p>
        <p className="text-center text-xs text-[#8D837A] mb-5">
          Tous les cours ({user.courses_count}) et données associés seront
          définitivement supprimés.
        </p>

        {error && (
          <p className="text-sm text-red-600 bg-red-50 p-2 rounded mb-4">
            {error}
          </p>
        )}

        <div className="flex gap-3">
          <button
            onClick={onClose}
            className="flex-1 py-2.5 rounded-md border border-[#DED8D1] text-[#5F5750] text-sm font-medium hover:bg-[#F6F3EF] transition-colors"
          >
            Annuler
          </button>
          <button
            onClick={handleDelete}
            disabled={loading}
            className="flex-1 py-2.5 rounded-md bg-red-500 text-white text-sm font-semibold hover:bg-red-600 transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {loading && <Loader2 className="w-4 h-4 animate-spin" />}
            Supprimer
          </button>
        </div>
      </motion.div>
    </div>
  );
}

// ── Page principale ───────────────────────────────────────────────────────────

export default function AdminPage() {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();

  const [users, setUsers] = useState<UserRow[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [loadingData, setLoadingData] = useState(true);
  const [search, setSearch] = useState("");
  const [filterRole, setFilterRole] = useState<"all" | "admin" | "user">("all");

  const [showAddModal, setShowAddModal] = useState(false);
  const [editUser, setEditUser] = useState<UserRow | null>(null);
  const [deleteUser, setDeleteUser] = useState<UserRow | null>(null);
  const [toast, setToast] = useState<string | null>(null);

  // ── Auth guard ──────────────────────────────────────────────────────────────
  useEffect(() => {
    if (authLoading) return;
    if (!user) {
      router.replace("/auth"); // Not logged in → login page
    } else if (user.role !== "admin") {
      router.replace("/courses"); // Logged in but not admin → courses
    }
  }, [user, authLoading, router]);

  // ── Chargement des données ──────────────────────────────────────────────────
  const loadData = useCallback(async () => {
    try {
      const [usersRes, statsRes] = await Promise.all([
        api.get<UserRow[]>("/api/admin/users"),
        api.get<Stats>("/api/admin/stats"),
      ]);
      setUsers(usersRes.data);
      setStats(statsRes.data);
    } catch {
      // Géré via auth guard
    } finally {
      setLoadingData(false);
    }
  }, []);

  useEffect(() => {
    if (user?.role === "admin") loadData();
  }, [user, loadData]);

  // ── Toast ───────────────────────────────────────────────────────────────────
  const showToast = (msg: string) => {
    setToast(msg);
    setTimeout(() => setToast(null), 3000);
  };

  // ── Filtre ──────────────────────────────────────────────────────────────────
  const filtered = users.filter((u) => {
    const q = search.toLowerCase();
    const matchSearch =
      u.name.toLowerCase().includes(q) || u.email.toLowerCase().includes(q);
    const matchRole = filterRole === "all" || u.role === filterRole;
    return matchSearch && matchRole;
  });

  if (authLoading || loadingData) {
    return (
      <div className="min-h-screen bg-[#F6F3EF] flex items-center justify-center">
        <Loader2 className="w-7 h-7 animate-spin text-[#B85B2A]" />
      </div>
    );
  }

  // Still waiting for redirect to complete
  if (!user || user.role !== "admin") {
    return (
      <div className="min-h-screen bg-[#F6F3EF] flex items-center justify-center">
        <Loader2 className="w-7 h-7 animate-spin text-[#B85B2A]" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#F6F3EF]">
      {/* ── Header admin ─────────────────────────────────────────────────── */}
      <div className="bg-white border-b border-[#DED8D1]">
        <div className="max-w-6xl mx-auto px-5 sm:px-8 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Image
              src="/favicon.svg"
              alt="EduAI"
              width={32}
              height={32}
              className="rounded-lg"
            />
            <div>
              <div className="flex items-center gap-2">
                <span className="font-display text-lg font-bold text-[#171412]">
                  EduAI
                </span>
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold bg-[#F0E3DA] text-[#B85B2A]">
                  <Shield className="w-3 h-3" />
                  Admin
                </span>
              </div>
              <p className="text-xs text-[#8D837A]">
                Panneau d&apos;administration
              </p>
            </div>
          </div>
          <Link
            href="/courses"
            className="text-sm text-[#5F5750] hover:text-[#B85B2A] transition-colors"
          >
            ← Retour à l&apos;application
          </Link>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-5 sm:px-8 py-8">
        {/* ── Statistiques ───────────────────────────────────────────────── */}
        {stats && (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-8">
            {[
              {
                label: "Utilisateurs",
                value: stats.total_users,
                icon: Users,
                color: "text-[#B85B2A]",
                bg: "bg-[#F0E3DA]",
              },
              {
                label: "Cours",
                value: stats.total_courses,
                icon: BookOpen,
                color: "text-[#2F6A4E]",
                bg: "bg-[#E5F2EA]",
              },
              {
                label: "Passages indexés",
                value: stats.total_chunks.toLocaleString(),
                icon: null,
                color: "text-[#5F5750]",
                bg: "bg-[#ECE7E1]",
              },
              {
                label: "Admins",
                value: stats.admin_count,
                icon: Shield,
                color: "text-[#B85B2A]",
                bg: "bg-[#F0E3DA]",
              },
            ].map((s) => (
              <div
                key={s.label}
                className="bg-white rounded-xl border border-[#DED8D1] p-4"
              >
                <div
                  className={`w-9 h-9 rounded-lg ${s.bg} flex items-center justify-center mb-3`}
                >
                  {s.icon ? (
                    <s.icon className={`w-5 h-5 ${s.color}`} />
                  ) : (
                    <span className="text-xs font-mono font-bold text-[#5F5750]">
                      #
                    </span>
                  )}
                </div>
                <div className="text-2xl font-bold text-[#171412]">
                  {s.value}
                </div>
                <div className="text-xs text-[#8D837A] mt-0.5">{s.label}</div>
              </div>
            ))}
          </div>
        )}

        {/* ── Tableau des utilisateurs ────────────────────────────────────── */}
        <div className="bg-white rounded-xl border border-[#DED8D1] shadow-sm">
          {/* Toolbar */}
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 p-5 border-b border-[#DED8D1]">
            <div className="flex items-center gap-2">
              <Users className="w-5 h-5 text-[#B85B2A]" />
              <h2 className="font-semibold text-[#171412]">
                Comptes ({filtered.length})
              </h2>
            </div>

            <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2 w-full sm:w-auto">
              {/* Recherche */}
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#8D837A]" />
                <input
                  type="text"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="Rechercher…"
                  className="pl-9 pr-4 py-2 rounded-md border border-[#DED8D1] bg-[#F6F3EF] text-sm text-[#171412] placeholder:text-[#8D837A] focus:outline-none focus:ring-2 focus:ring-[#B85B2A]/30 focus:border-[#B85B2A] w-full sm:w-52"
                />
              </div>

              {/* Filtre rôle */}
              <div className="relative">
                <select
                  aria-label="Filtrer par rôle"
                  value={filterRole}
                  onChange={(e) => setFilterRole(e.target.value as any)}
                  className="appearance-none pl-3 pr-8 py-2 rounded-md border border-[#DED8D1] bg-[#F6F3EF] text-sm text-[#171412] focus:outline-none focus:ring-2 focus:ring-[#B85B2A]/30 focus:border-[#B85B2A] w-full sm:w-auto"
                >
                  <option value="all">Tous les rôles</option>
                  <option value="user">Utilisateurs</option>
                  <option value="admin">Admins</option>
                </select>
                <ChevronDown className="pointer-events-none absolute right-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-[#8D837A]" />
              </div>

              {/* Bouton Ajouter */}
              <button
                onClick={() => setShowAddModal(true)}
                className="flex items-center gap-2 px-4 py-2 rounded-md bg-[#B85B2A] text-white text-sm font-semibold hover:bg-[#9A4B22] transition-colors"
              >
                <Plus className="w-4 h-4" />
                Ajouter
              </button>
            </div>
          </div>

          {/* Table */}
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-[#DED8D1] bg-[#FAF8F5]">
                  <th className="text-left px-5 py-3 text-xs font-semibold text-[#8D837A] uppercase tracking-wider">
                    Utilisateur
                  </th>
                  <th className="text-left px-4 py-3 text-xs font-semibold text-[#8D837A] uppercase tracking-wider hidden sm:table-cell">
                    Rôle
                  </th>
                  <th className="text-left px-4 py-3 text-xs font-semibold text-[#8D837A] uppercase tracking-wider hidden md:table-cell">
                    Plan
                  </th>
                  <th className="text-left px-4 py-3 text-xs font-semibold text-[#8D837A] uppercase tracking-wider hidden lg:table-cell">
                    Cours
                  </th>
                  <th className="text-left px-4 py-3 text-xs font-semibold text-[#8D837A] uppercase tracking-wider hidden lg:table-cell">
                    Inscrit le
                  </th>
                  <th className="px-4 py-3"></th>
                </tr>
              </thead>
              <tbody>
                <AnimatePresence>
                  {filtered.length === 0 ? (
                    <tr>
                      <td
                        colSpan={6}
                        className="text-center py-12 text-[#8D837A] text-sm"
                      >
                        Aucun utilisateur trouvé
                      </td>
                    </tr>
                  ) : (
                    filtered.map((u, i) => (
                      <motion.tr
                        key={u.id}
                        initial={{ opacity: 0, y: 4 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: i * 0.03 }}
                        className="border-b border-[#F0EBE5] hover:bg-[#FAF8F5] transition-colors"
                      >
                        <td className="px-5 py-3.5">
                          <div>
                            <div className="font-medium text-[#171412]">
                              {u.name}
                            </div>
                            <div className="text-xs text-[#8D837A]">
                              {u.email}
                            </div>
                          </div>
                        </td>
                        <td className="px-4 py-3.5 hidden sm:table-cell">
                          <RoleBadge role={u.role} />
                        </td>
                        <td className="px-4 py-3.5 hidden md:table-cell">
                          <PlanBadge plan={u.plan} />
                        </td>
                        <td className="px-4 py-3.5 hidden lg:table-cell">
                          <span className="text-[#5F5750]">
                            {u.courses_count}
                          </span>
                        </td>
                        <td className="px-4 py-3.5 hidden lg:table-cell">
                          <span className="text-[#8D837A] text-xs">
                            {new Date(u.created_at).toLocaleDateString(
                              "fr-FR",
                              {
                                day: "2-digit",
                                month: "short",
                                year: "numeric",
                              },
                            )}
                          </span>
                        </td>
                        <td className="px-4 py-3.5">
                          <div className="flex items-center justify-end gap-1">
                            <button
                              onClick={() => setEditUser(u)}
                              className="p-1.5 rounded-md hover:bg-[#F0E3DA] text-[#8D837A] hover:text-[#B85B2A] transition-colors"
                              title="Modifier"
                            >
                              <Pencil className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() => setDeleteUser(u)}
                              className="p-1.5 rounded-md hover:bg-red-50 text-[#8D837A] hover:text-red-500 transition-colors"
                              title="Supprimer"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </div>
                        </td>
                      </motion.tr>
                    ))
                  )}
                </AnimatePresence>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* ── Modals ─────────────────────────────────────────────────────────── */}
      <AnimatePresence>
        {showAddModal && (
          <UserFormModal
            onClose={() => setShowAddModal(false)}
            onSaved={() => {
              loadData();
              showToast("Compte créé avec succès.");
            }}
          />
        )}
        {editUser && (
          <UserFormModal
            user={editUser}
            onClose={() => setEditUser(null)}
            onSaved={() => {
              loadData();
              showToast("Compte modifié avec succès.");
            }}
          />
        )}
        {deleteUser && (
          <DeleteConfirmModal
            user={deleteUser}
            onClose={() => setDeleteUser(null)}
            onDeleted={() => {
              loadData();
              showToast("Compte supprimé.");
            }}
          />
        )}
      </AnimatePresence>

      {/* ── Toast notification ──────────────────────────────────────────────── */}
      <AnimatePresence>
        {toast && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 20 }}
            className="fixed bottom-6 left-1/2 -translate-x-1/2 flex items-center gap-2 bg-[#171412] text-white text-sm px-4 py-2.5 rounded-lg shadow-lg"
          >
            <CheckCircle className="w-4 h-4 text-[#6EE7A8]" />
            {toast}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
