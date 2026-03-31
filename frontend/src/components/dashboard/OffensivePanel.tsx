"use client";

import React, { useState } from "react";
import { Zap, ShieldAlert, Wifi, Globe, Target, Terminal, Play } from "lucide-react";
import { API } from "@/lib/api";

interface OffensivePanelProps {
  onAttackLaunched?: () => void;
}

export const OffensivePanel: React.FC<OffensivePanelProps> = ({ onAttackLaunched }) => {
  const [loading, setLoading] = useState(false);
  const [intensity, setIntensity] = useState<"medium" | "high">("medium");
  const [status, setStatus] = useState<string | null>(null);

  const launchAttack = async (type: string) => {
    setLoading(true);
    setStatus(`Initializing ${type.toUpperCase()} scenario...`);
    try {
      const res = await API.post("/api/v1/traffic/simulate", {
        attack_type: type,
        intensity: intensity,
      });
      setStatus(`Success: Launched ${res.data.packets_scheduled} packets.`);
      if (onAttackLaunched) onAttackLaunched();
      
      // Clear status after 3 seconds
      setTimeout(() => setStatus(null), 3000);
    } catch (err) {
      console.error(err);
      setStatus("Error: Neural Link Interrupted.");
    } finally {
      setLoading(false);
    }
  };

  const scenarios = [
    { id: "ddos", name: "DDoS Flood", icon: Wifi, color: "text-red-500", border: "border-red-500/20", bg: "bg-red-500/5" },
    { id: "brute_force", name: "Brute Force", icon: ShieldAlert, color: "text-orange-500", border: "border-orange-500/20", bg: "bg-orange-500/5" },
    { id: "port_scan", name: "Port Scan", icon: Target, color: "text-blue-500", border: "border-blue-500/20", bg: "bg-blue-500/5" },
  ];

  return (
    <div className="bg-gray-950 border border-gray-900 rounded-2xl p-6 relative overflow-hidden group">
      {/* Background Grid Decoration */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#1f2937_1px,transparent_1px),linear-gradient(to_bottom,#1f2937_1px,transparent_1px)] bg-[size:14px_14px] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_0%,#000_70%,transparent_100%)] opacity-[0.03]"></div>

      <div className="flex items-center justify-between mb-8 relative z-10">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-red-600/10 border border-red-500/20 flex items-center justify-center">
            <Zap className="w-5 h-5 text-red-500" />
          </div>
          <div>
            <h2 className="text-sm font-black tracking-tighter uppercase italic">Combat Simulator</h2>
            <p className="text-[10px] text-gray-500 uppercase tracking-widest font-bold">Node: ALPHA-NODE-01</p>
          </div>
        </div>

        <div className="flex items-center gap-2 p-1 bg-black/40 border border-gray-900 rounded-lg">
          <button 
            onClick={() => setIntensity("medium")}
            className={`px-3 py-1 text-[10px] font-black uppercase rounded-md transition-all ${intensity === "medium" ? "bg-gray-800 text-white shadow-lg" : "text-gray-600 hover:text-gray-400"}`}
          >
            Medium
          </button>
          <button 
            onClick={() => setIntensity("high")}
            className={`px-3 py-1 text-[10px] font-black uppercase rounded-md transition-all ${intensity === "high" ? "bg-red-600 text-white shadow-[0_0_15px_rgba(220,38,38,0.3)]" : "text-gray-600 hover:text-red-900"}`}
          >
            High
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 relative z-10">
        {scenarios.map((s) => (
          <button
            key={s.id}
            disabled={loading}
            onClick={() => launchAttack(s.id)}
            className={`group relative flex flex-col items-center justify-center gap-4 p-6 rounded-2xl border ${s.border} ${s.bg} hover:scale-[1.02] active:scale-95 transition-all duration-300 disabled:opacity-50 disabled:pointer-events-none overflow-hidden`}
          >
            <div className={`p-4 rounded-xl bg-black/40 border ${s.border} shadow-lg transition-transform group-hover:rotate-12`}>
              <s.icon className={`w-8 h-8 ${s.color}`} />
            </div>
            <span className={`text-[11px] font-black uppercase tracking-widest ${s.color}`}>
              {s.name}
            </span>
            
            {/* Hover Glitch Effect */}
            <div className="absolute inset-0 bg-white/5 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none"></div>
          </button>
        ))}
      </div>

      {status && (
        <div className="mt-6 p-3 bg-black/60 border border-gray-900 rounded-xl flex items-center gap-3 animate-in fade-in slide-in-from-bottom-2 duration-300 relative z-10">
          <Terminal className="w-4 h-4 text-gray-400" />
          <p className="text-[10px] font-mono text-gray-400 whitespace-nowrap overflow-hidden">
            <span className="text-red-500 font-bold">$ </span>{status}
          </p>
        </div>
      )}
    </div>
  );
};
