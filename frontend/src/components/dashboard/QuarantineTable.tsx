"use client";

import React, { useEffect, useState } from "react";
import { ShieldX, Clock, MapPin, AlertCircle, RefreshCcw, Activity, ShieldCheck } from "lucide-react";
import { API } from "@/lib/api";

interface BlockedIP {
  ip: string;
  timestamp: string;
  reason: string;
  expires_at: string | null;
  risk: number;
  confidence: number;
  attack_type: string;
  auto: boolean;
}

export const QuarantineTable: React.FC = () => {
  const [blocks, setBlocks] = useState<BlockedIP[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchBlocks = async () => {
    try {
      const res = await API.get("/api/v1/defender/blocks/active");
      setBlocks(res.data);
    } catch (err) {
      console.error("Failed to fetch quarantine list:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBlocks();
    const interval = setInterval(fetchBlocks, 10000); // 🕙 Refresh every 10s
    return () => clearInterval(interval);
  }, []);

  if (loading && blocks.length === 0) {
    return (
      <div className="h-64 glass-card border-white/5 flex items-center justify-center">
        <RefreshCcw className="w-6 h-6 text-cyber-red animate-spin" />
      </div>
    );
  }

  return (
    <div className="glass-card overflow-hidden flex flex-col h-full border-white/5 bg-black/40">
      <div className="px-8 py-6 border-b border-white/5 bg-white/[0.02] flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="p-3 rounded-2xl bg-cyber-red/10 border border-cyber-red/20 shadow-[0_0_15px_rgba(239,68,68,0.1)]">
            <ShieldX className="w-5 h-5 text-cyber-red animate-pulse" />
          </div>
          <div>
            <h3 className="text-sm font-black tracking-tighter uppercase italic text-glow-red">IP QUARANTINE.</h3>
            <p className="text-[8px] text-gray-500 uppercase tracking-[0.4em] font-black mt-1">TOTAL ISOLATED: {blocks.length}</p>
          </div>
        </div>
        <div className="flex items-center gap-2 px-3 py-1 bg-cyber-red/10 border border-cyber-red/20 rounded-full">
            <div className="w-1.5 h-1.5 bg-cyber-red rounded-full animate-ping"></div>
            <span className="text-[8px] text-cyber-red font-black uppercase tracking-widest">Live Blockade</span>
        </div>
      </div>

      <div className="flex-1 overflow-auto custom-scrollbar relative">
        {/* Decorative Grid */}
        <div className="absolute inset-0 opacity-[0.01] pointer-events-none cyber-grid-small"></div>
        
        {blocks.length === 0 ? (
          <div className="h-64 flex flex-col items-center justify-center text-center p-10 space-y-6 relative z-10">
             <div className="w-20 h-20 rounded-[2rem] bg-white/5 border border-white/10 flex items-center justify-center group hover:border-green-500/30 transition-all duration-500">
                <ShieldCheck className="w-10 h-10 text-gray-700 group-hover:text-green-500 transition-colors" />
             </div>
             <div>
                <h4 className="text-xs font-black uppercase tracking-[0.3em] text-gray-500 mb-2">Perimeter Secured.</h4>
                <p className="text-[10px] font-black uppercase tracking-widest text-gray-700">No active threats detected in quarantine.</p>
             </div>
          </div>
        ) : (
          <table className="w-full text-left border-collapse relative z-10">
            <thead className="sticky top-0 bg-cyber-black/95 backdrop-blur-xl z-20 border-b border-white/5">
              <tr className="bg-white/[0.02]">
                <th className="px-8 py-5 text-[10px] font-black uppercase tracking-[0.2em] text-gray-500 italic">Target IP</th>
                <th className="px-8 py-5 text-[10px] font-black uppercase tracking-[0.2em] text-gray-500 italic">Attack Vector</th>
                <th className="px-8 py-5 text-[10px] font-black uppercase tracking-[0.2em] text-gray-500 italic">Severity</th>
                <th className="px-8 py-5 text-[10px] font-black uppercase tracking-[0.2em] text-gray-500 italic text-right">TTL Exit</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5 font-mono">
              {blocks.map((b) => (
                <tr key={b.ip} className="hover:bg-white/[0.02] transition-all group">
                  <td className="px-8 py-6">
                    <div className="flex items-center gap-4">
                      <div className="w-2 h-2 bg-cyber-red rounded-full shadow-[0_0_10px_rgba(239,68,68,0.6)] group-hover:scale-150 transition-transform"></div>
                      <div>
                        <span className="text-xs font-black text-gray-300 group-hover:text-white transition-colors tracking-tighter">{b.ip}</span>
                        <div className="text-[8px] text-gray-600 font-bold uppercase tracking-[0.3em] mt-1">NODE: {b.auto ? "AUTO-DEFENSE" : "MANUAL"}</div>
                      </div>
                    </div>
                  </td>
                  <td className="px-8 py-6">
                    <div className="flex flex-col">
                      <span className="text-[10px] font-black uppercase tracking-widest text-white group-hover:text-cyber-red transition-colors italic">{b.attack_type || "ANOMALY"}</span>
                      <span className="text-[9px] text-gray-600 uppercase font-black tracking-tighter truncate max-w-[150px] mt-1">{b.reason}</span>
                    </div>
                  </td>
                  <td className="px-8 py-6">
                    <div className="flex items-center gap-3">
                       <div className="flex-1 w-16 bg-white/5 h-1.5 rounded-full overflow-hidden border border-white/5 shadow-inner">
                          <div 
                             className="h-full bg-cyber-red shadow-[0_0_15px_rgba(239,68,68,0.4)]"
                             style={{ width: `${(b.risk || 0) * 100}%` }}
                          ></div>
                       </div>
                       <span className="text-[10px] font-black text-cyber-red font-mono">{(b.risk * 100).toFixed(0)}</span>
                    </div>
                  </td>
                  <td className="px-8 py-6 text-right">
                    <div className="flex items-center justify-end gap-2 text-gray-500 group-hover:text-white transition-colors">
                      <Clock className="w-3 h-3" />
                      <span className="text-[10px] font-black uppercase tracking-tighter">
                        {b.expires_at ? new Date(b.expires_at).toLocaleTimeString() : "PERMANENT"}
                      </span>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Footer Decoration */}
      <div className="px-8 py-4 border-t border-white/5 bg-white/[0.01] flex justify-between items-center opacity-30 select-none">
        <span className="text-[8px] font-black uppercase tracking-[0.5em] text-gray-600">STEALTHVAULT QUARANTINE MODULE v4.2</span>
        <Activity className="w-3 h-3 text-gray-600" />
      </div>
    </div>
  );
};
