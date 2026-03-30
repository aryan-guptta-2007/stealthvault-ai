"use client";

import { useEffect, useState } from "react";
import { API } from "@/lib/api";
import { StatsCharts } from "@/components/dashboard/StatsCharts";
import { BrainPanel } from "@/components/dashboard/BrainPanel";
import { Activity, Shield, AlertTriangle, Cpu, Terminal } from "lucide-react";

interface BrainAnalysis {
  attack_name: string;
  description: string;
  danger_level: string;
  what_is_happening: string;
  how_to_stop: string;
  technical_details: string;
  recommended_actions: string[];
}

interface AlertData {
  id: string;
  timestamp: string;
  packet: any;
  anomaly: any;
  classification: any;
  risk: any;
}

export default function Dashboard() {
  const [status, setStatus] = useState("Loading...");
  const [events, setEvents] = useState<string[]>([]);
  const [rawAlerts, setRawAlerts] = useState<AlertData[]>([]);
  const [stats, setStats] = useState<any>(null);
  
  // AI Brain State
  const [selectedAnalysis, setSelectedAnalysis] = useState<BrainAnalysis | null>(null);
  const [isBrainOpen, setIsBrainOpen] = useState(false);
  const [brainLoading, setBrainLoading] = useState(false);

  useEffect(() => {
    // 🔐 PROTECT DASHBOARD
    const token = localStorage.getItem("token");
    if (!token) {
      window.location.href = "/login";
      return;
    }

    // Initial Stats Fetch
    const fetchStats = async () => {
      try {
        const res = await API.get("/api/v1/dashboard/");
        setStats(res.data);
        setStatus(res.data.system_status.toLowerCase());
      } catch (err) {
        console.error("Dashboard Stats Fetch Failed:", err);
      }
    };

    fetchStats();

    // 🔥 WebSocket connection
    const ws = new WebSocket("wss://stealthvault-ai.onrender.com/ws");

    ws.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        
        if (payload.type === "ALERT") {
          const alert = payload.data;
          const msg = `🚨 [${alert.risk.severity.toUpperCase()}] ${alert.classification.attack_type} intercepted from ${alert.packet.src_ip}`;
          
          setEvents((prev) => [msg, ...prev.slice(0, 19)]);
          setRawAlerts((prev) => [alert, ...prev.slice(0, 19)]);
        } else if (payload.type === "STATS_UPDATE") {
           setStats(payload.data);
        }
      } catch (e) {
        console.error("WS Parse Error:", e);
      }
    };

    return () => ws.close();
  }, []);

  const handleAlertClick = async (alertId: string) => {
    setBrainLoading(true);
    setIsBrainOpen(true);
    try {
      const res = await API.post("/api/v1/brain/analyze", { alert_id: alertId });
      setSelectedAnalysis(res.data);
    } catch (err) {
      console.error("Brain Analysis Failed:", err);
    } finally {
      setBrainLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("token");
    window.location.href = "/"; // Back to landing page
  };

  if (!stats) return (
    <div className="min-h-screen bg-black flex flex-col items-center justify-center space-y-4">
        <div className="w-10 h-10 border-2 border-red-500 border-t-transparent rounded-full animate-spin"></div>
        <p className="text-[10px] font-black tracking-widest uppercase text-red-500 animate-pulse">Initializing Neural Link...</p>
    </div>
  );

  return (
    <div className="flex min-h-screen bg-black text-white font-mono selection:bg-red-500/30">
      <BrainPanel 
        isOpen={isBrainOpen} 
        onCloseAction={() => setIsBrainOpen(false)} 
        analysis={selectedAnalysis} 
        loading={brainLoading}
      />

      {/* SIDEBAR */}
      <div className="w-72 bg-gray-950 border-r border-gray-800 flex flex-col p-6 sticky top-0 h-screen z-40">
        <div className="flex items-center gap-3 mb-12 group cursor-default">
          <div className="bg-red-600 w-8 h-8 rounded flex items-center justify-center shadow-[0_0_15px_rgba(220,38,38,0.5)] group-hover:scale-110 transition-transform">
            <Shield className="w-5 h-5 text-white" />
          </div>
          <h2 className="text-xl font-black tracking-tighter uppercase italic text-transparent bg-clip-text bg-gradient-to-r from-white to-gray-500">
            STEALTHVAULT
          </h2>
        </div>

        <nav className="flex-1">
          <ul className="space-y-2">
            <li className="flex items-center gap-3 p-3 bg-red-600/10 text-red-500 rounded-xl border border-red-600/20 cursor-default">
              <Activity className="w-4 h-4" /> Dashboard
            </li>
            <li className="flex items-center gap-3 p-3 text-gray-500 hover:text-gray-300 hover:bg-gray-900 rounded-xl cursor-not-allowed transition-all group">
              <AlertTriangle className="w-4 h-4" /> Threats <span className="text-[10px] bg-gray-800 px-1.5 rounded ml-auto">PRO</span>
            </li>
            <li className="flex items-center gap-3 p-3 text-gray-500 hover:text-gray-300 hover:bg-gray-900 rounded-xl cursor-not-allowed transition-all group">
              <Cpu className="w-4 h-4" /> Agents <span className="text-[10px] bg-gray-800 px-1.5 rounded ml-auto">PRO</span>
            </li>
          </ul>
        </nav>

        <div className="pt-6 border-t border-gray-900">
          <button
            onClick={handleLogout}
            className="w-full flex items-center justify-center gap-2 bg-gray-900 hover:bg-red-950/30 text-gray-400 hover:text-red-500 p-3 rounded-xl border border-gray-800 hover:border-red-500/30 transition-all duration-300"
          >
            <span>🔌</span> Logout
          </button>
        </div>
      </div>

      {/* MAIN CONTENT */}
      <div className="flex-1 flex flex-col">
        <header className="h-20 border-b border-gray-900 flex items-center justify-between px-8 bg-black/50 backdrop-blur-xl z-30 sticky top-0">
          <div>
            <h1 className="text-lg font-black tracking-tighter uppercase italic">Security Operations Center</h1>
            <p className="text-[10px] text-gray-500 uppercase tracking-widest">Instance: ALPHA-NODE-01</p>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 bg-gray-900 border border-gray-800 px-4 py-1.5 rounded-full">
              <span className={`h-2 w-2 rounded-full ${status === 'active' || status === 'ok' ? 'bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.5)]' : 'bg-yellow-500 animate-pulse'}`}></span>
              <span className="text-[10px] font-black text-gray-400 uppercase tracking-widest">{status}</span>
            </div>
          </div>
        </header>

        <main className="flex-1 p-8 overflow-y-auto custom-scrollbar">
          {/* STATS INFOCARDS */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-10">
             {[
               { label: "Alerts Total", val: stats.total_alerts, col: "text-white" },
               { label: "Critical", val: stats.critical_alerts, col: "text-red-500" },
               { label: "Analyze Rate", val: stats.packets_per_minute, col: "text-blue-400", unit: "PPM" },
               { label: "Risk Avg", val: (stats.avg_risk_score * 100).toFixed(0), col: "text-yellow-500", unit: "%" }
             ].map((card, i) => (
                <div key={i} className="bg-gray-900/40 p-6 rounded-3xl border border-gray-800 shadow-xl overflow-hidden relative">
                    <p className="text-[10px] text-gray-500 uppercase tracking-widest mb-3">{card.label}</p>
                    <div className="flex items-baseline gap-1">
                        <span className={`text-4xl font-black italic tracking-tighter ${card.col}`}>{card.val}</span>
                        {card.unit && <span className="text-[10px] text-gray-700 font-bold uppercase">{card.unit}</span>}
                    </div>
                    <div className="absolute top-0 right-0 p-2 opacity-5">
                        <Terminal className="w-12 h-12" />
                    </div>
                </div>
             ))}
          </div>

          <StatsCharts distribution={stats.attack_distribution} />

          <div className="bg-gray-900/40 rounded-3xl border border-gray-800 shadow-2xl overflow-hidden transition-all duration-700">
            <div className="p-6 border-b border-gray-800 flex items-center justify-between">
              <h2 className="text-lg font-black tracking-tighter uppercase italic flex items-center gap-2">
                <span className="text-red-500 animate-pulse">!</span> Intercepted Threats
              </h2>
              <div className="flex items-center gap-2">
                <span className="relative flex h-2 w-2">
                   <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
                   <span className="relative inline-flex rounded-full h-2 w-2 bg-red-500"></span>
                </span>
                <span className="text-[10px] text-red-600 font-black tracking-widest uppercase">Streaming Real-Time</span>
              </div>
            </div>

            <div className="p-6">
              <div className="space-y-2">
                {rawAlerts.length === 0 ? (
                  <div className="py-20 flex flex-col items-center justify-center border-2 border-dashed border-gray-800 rounded-3xl group">
                    <Activity className="w-10 h-10 text-gray-800 mb-4 animate-pulse group-hover:text-red-900/30 transition-colors" />
                    <p className="text-[10px] text-gray-600 font-black uppercase tracking-[0.3em] italic">Quiet on the frontier. No threats detected.</p>
                  </div>
                ) : (
                  rawAlerts.map((alert, i) => (
                    <div
                      key={i}
                      onClick={() => handleAlertClick(alert.id)}
                      className="group flex items-center gap-4 p-4 bg-red-600/5 hover:bg-red-600/10 border border-red-500/10 hover:border-red-500/50 rounded-2xl cursor-pointer transition-all animate-in slide-in-from-right-4 fade-in shadow-[0_0_15px_rgba(220,38,38,0.02)]"
                    >
                      <div className="w-10 h-10 rounded-xl bg-red-600/10 flex items-center justify-center font-black text-red-500 group-hover:bg-red-500 group-hover:text-white transition-all shadow-inner">!</div>
                      <div className="flex-1">
                        <p className="font-black italic text-sm tracking-tight text-red-400 uppercase">
                          {alert.classification.attack_type} Detections: {alert.packet.src_ip}
                        </p>
                        <p className="text-[10px] text-gray-600 font-bold uppercase tracking-widest mt-1">
                          Severity: <span className="text-red-700">{alert.risk.severity}</span> • Score: {(alert.risk.score * 100).toFixed(0)}%
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="text-[10px] text-gray-700 font-mono italic">{new Date(alert.timestamp).toLocaleTimeString()}</p>
                        <div className="mt-1 opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-1 text-[10px] text-red-500 font-black uppercase tracking-tighter">
                          Engage <ChevronRight className="w-3 h-3" />
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        </main>
      </div>

      <style jsx global>{`
        .custom-scrollbar::-webkit-scrollbar { width: 6px; }
        .custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
        .custom-scrollbar::-webkit-scrollbar-thumb { background: #1f2937; border-radius: 10px; }
        .custom-scrollbar-thin::-webkit-scrollbar { width: 4px; }
        .custom-scrollbar-thin::-webkit-scrollbar-track { background: transparent; }
        .custom-scrollbar-thin::-webkit-scrollbar-thumb { background: #374151; border-radius: 10px; }
      `}</style>
    </div>
  );
}

const ChevronRight = ({ className }: { className?: string }) => (
    <svg className={className} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><path d="m9 18 6-6-6-6"/></svg>
);
