"use client";

import React, { useEffect, useState } from "react";
import { ShieldX, Clock, MapPin, AlertCircle, RefreshCcw } from "lucide-react";
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
      <div className="h-64 bg-gray-950/20 border border-gray-900 rounded-2xl flex items-center justify-center">
        <RefreshCcw className="w-5 h-5 text-gray-700 animate-spin" />
      </div>
    );
  }

  return (
    <div className="bg-gray-950 border border-gray-900 rounded-2xl overflow-hidden flex flex-col h-full ring-1 ring-white/5">
      <div className="px-6 py-5 border-b border-gray-900 bg-black/40 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-red-600/10 border border-red-500/20">
            <ShieldX className="w-4 h-4 text-red-500" />
          </div>
          <h3 className="text-sm font-black tracking-tighter uppercase italic">Active IP Quarantine</h3>
        </div>
        <span className="text-[10px] bg-red-600/10 text-red-500 px-2 py-0.5 rounded-full font-black uppercase tracking-widest border border-red-500/20 shadow-sm animate-pulse">
           Live Neural Blockade
        </span>
      </div>

      <div className="flex-1 overflow-auto custom-scrollbar">
        {blocks.length === 0 ? (
          <div className="h-48 flex flex-col items-center justify-center text-center p-6 space-y-4">
             <div className="w-12 h-12 rounded-full border border-gray-800 flex items-center justify-center opacity-30">
                <AlertCircle className="w-6 h-6 text-gray-400" />
             </div>
             <p className="text-[10px] font-black uppercase tracking-widest text-gray-600">Zero active threats quarantined.</p>
          </div>
        ) : (
          <table className="w-full text-left border-collapse">
            <thead className="sticky top-0 bg-gray-950/90 backdrop-blur-md z-10 border-b border-gray-900">
              <tr className="bg-black/20">
                <th className="px-6 py-4 text-[10px] font-black uppercase tracking-widest text-gray-500 italic">Target IP</th>
                <th className="px-6 py-4 text-[10px] font-black uppercase tracking-widest text-gray-500 italic">Attack Pattern</th>
                <th className="px-6 py-4 text-[10px] font-black uppercase tracking-widest text-gray-500 italic text-center">Threat Score</th>
                <th className="px-6 py-4 text-[10px] font-black uppercase tracking-widest text-gray-500 italic text-right">TTL Remaining</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-900">
              {blocks.map((b) => (
                <tr key={b.ip} className="hover:bg-red-500/[0.02] transition-colors group">
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-3">
                      <div className="w-1.5 h-1.5 bg-red-500 rounded-full shadow-[0_0_8px_rgba(239,68,68,0.5)]"></div>
                      <span className="text-[11px] font-bold text-gray-300 group-hover:text-red-400 transition-colors">{b.ip}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex flex-col">
                      <span className="text-[10px] font-black uppercase tracking-tighter text-white">{b.attack_type || "UNKNOWN"}</span>
                      <span className="text-[9px] text-gray-600 uppercase font-bold truncate max-w-[120px]">{b.reason}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center justify-center gap-2">
                       <div className="flex-1 w-12 bg-gray-900 h-1 rounded-full overflow-hidden">
                          <div 
                             className="h-full bg-red-600 shadow-[0_0_10px_rgba(220,38,38,0.4)]"
                             style={{ width: `${(b.risk || 0) * 100}%` }}
                          ></div>
                       </div>
                       <span className="text-[10px] font-black text-red-500">{(b.risk * 100).toFixed(0)}%</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-right">
                    <div className="flex items-center justify-end gap-2 text-gray-500">
                      <Clock className="w-3 h-3" />
                      <span className="text-[10px] font-bold">
                        {b.expires_at ? new Date(b.expires_at).toLocaleTimeString() : "Permanent"}
                      </span>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};
