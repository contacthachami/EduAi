"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import ReactFlow, {
  Node,
  Edge,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
} from "reactflow";
import "reactflow/dist/style.css";
import { api } from "@/lib/auth";
import { RefreshCw, ArrowLeft } from "lucide-react";

const NODE_COLORS: Record<string, string> = {
  chapter: "#B85B2A",
  concept: "#5B7BA8",
  detail: "#6B8F71",
};

export default function MindMapPage() {
  const params = useParams();
  const courseId = params.id as string;
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadMap = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const res = await api.get(`/api/mindmap/${courseId}`);
      const { nodes: apiNodes, edges: apiEdges } = res.data;

      // Layout: simple radial-ish by type
      const flowNodes: Node[] = apiNodes.map((n: any, i: number) => {
        const angle = (i / apiNodes.length) * 2 * Math.PI;
        const radius =
          n.type === "chapter" ? 150 : n.type === "concept" ? 300 : 420;
        return {
          id: n.id,
          position: {
            x: 500 + radius * Math.cos(angle),
            y: 400 + radius * Math.sin(angle),
          },
          data: { label: n.label },
          style: {
            background: NODE_COLORS[n.type] || "#DED8D1",
            color: "#fff",
            border: "none",
            borderRadius: 8,
            padding: "8px 14px",
            fontSize: n.type === "chapter" ? 14 : 12,
            fontWeight: n.type === "chapter" ? 700 : 500,
          },
        };
      });

      const flowEdges: Edge[] = apiEdges.map((e: any, i: number) => ({
        id: `e-${i}`,
        source: e.source,
        target: e.target,
        label: e.label || "",
        style: { stroke: "#8D837A" },
        labelStyle: { fontSize: 10, fill: "#5F5750" },
      }));

      setNodes(flowNodes);
      setEdges(flowEdges);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Erreur lors du chargement.");
    } finally {
      setLoading(false);
    }
  }, [courseId]);

  useEffect(() => {
    loadMap();
  }, [loadMap]);

  const regenerate = async () => {
    try {
      await api.delete(`/api/mindmap/${courseId}`);
      await loadMap();
    } catch {}
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#F6F3EF] flex flex-col items-center justify-center relative">
        <Link
          href={`/course/${courseId}`}
          className="absolute top-6 left-6 inline-flex items-center gap-1.5 text-sm text-[#5F5750] hover:text-[#B85B2A] transition"
        >
          <ArrowLeft className="w-4 h-4" /> Retour au cours
        </Link>
        <div className="animate-pulse text-[#5F5750]">
          Génération de la carte mentale...
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-[#F6F3EF] flex flex-col items-center justify-center relative">
        <Link
          href={`/course/${courseId}`}
          className="absolute top-6 left-6 inline-flex items-center gap-1.5 text-sm text-[#5F5750] hover:text-[#B85B2A] transition"
        >
          <ArrowLeft className="w-4 h-4" /> Retour au cours
        </Link>
        <p className="text-red-600">{error}</p>
      </div>
    );
  }

  return (
    <div className="h-screen w-full relative">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        fitView
        attributionPosition="bottom-left"
      >
        <Background color="#DED8D1" gap={20} />
        <Controls />
        <MiniMap
          nodeColor={(n) => (n.style?.background as string) || "#DED8D1"}
          maskColor="rgba(246, 243, 239, 0.7)"
        />
      </ReactFlow>

      {/* Back button */}
      <Link
        href={`/course/${courseId}`}
        className="absolute top-4 left-4 flex items-center gap-1.5 px-3 py-2 rounded-md bg-white border border-[#DED8D1] text-sm text-[#5F5750] hover:border-[#B85B2A] transition z-10"
      >
        <ArrowLeft className="w-4 h-4" /> Retour au cours
      </Link>

      {/* Regenerate button */}
      <button
        onClick={regenerate}
        className="absolute top-4 right-4 flex items-center gap-2 px-3 py-2 rounded-md bg-white border border-[#DED8D1] text-sm text-[#5F5750] hover:border-[#B85B2A] transition"
      >
        <RefreshCw className="w-4 h-4" /> Régénérer
      </button>

      {/* Legend */}
      <div className="absolute bottom-4 right-4 bg-white/90 rounded-md border border-[#DED8D1] p-3 text-xs space-y-1">
        {Object.entries(NODE_COLORS).map(([type, color]) => (
          <div key={type} className="flex items-center gap-2">
            <div className="w-3 h-3 rounded" style={{ background: color }} />
            <span className="capitalize text-[#5F5750]">{type}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
