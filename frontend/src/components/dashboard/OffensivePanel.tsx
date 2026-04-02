"use client";

import React, { useState } from "react";
import { Zap, ShieldAlert, Wifi, Globe, Target, Terminal, Play, Radio, Activity, Cpu } from "lucide-react";
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
    { id: "ddos", name: "DDoS Flood", icon: Radio, color: "text-cyber-red", border: "border-cyber-red/20", bg: "bg-cyber-red/5" },
    { id: "brute_force", name: "Brute Force", icon: ShieldAlert, color: "text-orange-500", border: "border-orange-500/20", bg: "bg-orange-500/5" },
    { id: "port_scan", name: "Port Scan", icon: Target, color: "text-cyber-blue", border: "border-cyber-blue/20", bg: "bg-cyber-blue/5" },
  ];

  return (
    <div className="glass-card p-10 relative overflow-hidden group border-white/5 bg-black/40">
      {/* Background Decorative Element */}
      <div className="absolute top-0 right-0 p-10 opacity-[0.02] pointer-events-none group-hover:opacity-[0.05] transition-opacity">
        <Target className="w-40 h-40 text-cyber-red rotate-12" />
      </div>

      <div className="flex flex-col md:flex-row items-start md:items-center justify-between mb-10 relative z-10 gap-6">
        <div className="flex items-center gap-5">
          <div className="w-14 h-14 rounded-2xl bg-cyber-red/10 border border-cyber-red/20 flex items-center justify-center shadow-[0_0_20px_rgba(239,68,68,0.1)] group-hover:scale-110 transition-transform">
            <Zap className="w-6 h-6 text-cyber-red animate-pulse" />
          </div>
          <div>
            <h2 className="text-xl font-black tracking-tighter uppercase italic text-glow-red">COMBAT SIMULATOR.</h2>
            <p className="text-[10px] text-gray-500 uppercase tracking-[0.4em] font-black mt-1">OFFENSIVE NODE: ALPHA-IX</p>
          </div>
        </div>

        <div className="flex items-center gap-3 p-1.5 bg-black/60 border border-white/5 rounded-2xl">
          <button 
            onClick={() => setIntensity("medium")}
            className={`px-5 py-2 text-[10px] font-black uppercase rounded-xl transition-all ${intensity === "medium" ? "bg-white/10 text-white shadow-xl" : "text-gray-600 hover:text-gray-400"}`}
          >
            Medium
          </button>
          <button 
            onClick={() => setIntensity("high")}
            className={`px-5 py-2 text-[10px] font-black uppercase rounded-xl transition-all ${intensity === "high" ? "bg-cyber-red text-white shadow-[0_0_25px_rgba(239,68,68,0.4)]" : "text-gray-600 hover:text-cyber-red"}`}
          >
            High Power
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 relative z-10">
        {scenarios.map((s) => (
          <button
            key={s.id}
            disabled={loading}
            onClick={() => launchAttack(s.id)}
            className={`group/btn relative flex flex-col items-center justify-center gap-5 p-8 rounded-[2rem] border ${s.border} ${s.bg} hover:border-white/20 transition-all duration-500 disabled:opacity-50 disabled:pointer-events-none overflow-hidden hover:shadow-[0_0_40px_rgba(0,0,0,0.4)]`}
          >
            {/* Scanline Effect */}
            <div className="absolute inset-0 bg-cyber-red/5 opacity-0 group-hover/btn:opacity-100 transition-opacity cyber-scanline pointer-events-none"></div>
            
            <div className={`p-5 rounded-2xl bg-black/60 border ${s.border} shadow-2xl transition-all duration-500 group-hover/btn:scale-110 group-hover/btn:-rotate-6`}>
              <s.icon className={`w-8 h-8 ${s.color}`} />
            </div>
            <div className="text-center">
                <span className={`text-xs font-black uppercase tracking-[0.3em] ${s.color}`}>
                {s.name}
                </span>
                <p className="text-[8px] text-gray-600 font-bold uppercase tracking-[0.5em] mt-2 group-hover/btn:text-white transition-colors">Initialize Sequence</p>
            </div>
            
            {/* Action Bar */}
            <div className="absolute bottom-4 opacity-0 group-hover/btn:opacity-100 transition-all translate-y-2 group-hover/btn:translate-y-0 text-[8px] font-mono font-black text-white/40">
                READY // EXECUTE
            </div>
          </button>
        ))}
      </div>

      {status && (
        <div className="mt-8 p-4 bg-black/80 border border-white/5 rounded-2xl flex items-center gap-4 animate-in slide-in-from-bottom-5 duration-500 relative z-10">
          <div className="w-8 h-8 rounded-lg bg-cyber-red/10 flex items-center justify-center">
            <Terminal className="w-4 h-4 text-cyber-red" />
          </div>
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-1">
                <div className="w-1 h-1 bg-cyber-red rounded-full animate-ping"></div>
                <span className="text-[8px] font-black text-cyber-red uppercase tracking-widest">Live Execution Terminal</span>
            </div>
            <p className="text-[10px] font-mono text-gray-400">
                <span className="text-cyber-red font-black">$ </span>{status}
            </p>
          </div>
        </div>
      )}
    </div>
  );
};
