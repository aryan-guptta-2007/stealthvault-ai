"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { API } from "@/lib/api";
import { StatsCharts } from "@/components/dashboard/StatsCharts";
import { BrainPanel } from "@/components/dashboard/BrainPanel";
import AttackMap from "@/components/dashboard/AttackMap";
import { Activity, Shield, AlertTriangle, Cpu, Terminal, LogOut, Server } from "lucide-react";

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
  geo_location: any;
}

export default function Dashboard() {
  const router = useRouter(); // 🚀 Next.js Navigation
  const [status, setStatus] = useState("Loading...");
  const [events, setEvents] = useState<string[]>([]);
  const [rawAlerts, setRawAlerts] = useState<AlertData[]>([]);
  const [stats, setStats] = useState<any>(null);
  
  // AI Brain State
  const [selectedAnalysis, setSelectedAnalysis] = useState<BrainAnalysis | null>(null);
  const [isBrainOpen, setIsBrainOpen] = useState(false);
  const [brainLoading, setBrainLoading] = useState(false);

  useEffect(() => {
    // 🔐 PROTECT DASHBOARD: Guard unauthorized access
    const token = localStorage.getItem("access_token") || localStorage.getItem("token");

    if (!token) {
      console.log("No authorization token detected. Redirecting to login...");
      router.push("/login");
      return;
    }

    // Initial Stats Fetch
    const fetchDashboardData = async () => {
      try {
        const statsRes = await API.get("/api/v1/dashboard/");
        setStats(statsRes.data);
        setStatus(statsRes.data.system_status.toLowerCase());

        // 🔥 HISTORICAL SYNC: Get previous alerts for SOC feed
        const alertsRes = await API.get("/api/v1/alerts/", { params: { limit: 20 } });
        setRawAlerts(alertsRes.data);
      } catch (err) {
        console.error("Dashboard Data Fetch Failed:", err);
      }
    };

    fetchDashboardData();

    // 🔥 AUTO-REFRESH: Polling fallback every 5 seconds for stats
    const interval = setInterval(fetchDashboardData, 5000);

    // 🔥 WEBSOCKET: Real-time event stream
    const ws = new WebSocket("wss://stealthvault-ai.onrender.com/ws");

    ws.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        
        if (payload.type === "ALERT") {
          const alert = payload.data;
          const msg = `🚨 [${alert.risk.severity.toUpperCase()}] ${alert.classification.attack_type} intercepted from ${alert.packet.src_ip}`;
          
          setEvents((prev) => [msg, ...prev.slice(0, 19)]);
          setRawAlerts((prev) => [alert, ...prev.slice(0, 19)]); // Prepend new alerts
        } else if (payload.type === "STATS_UPDATE") {
           setStats(payload.data);
        }
      } catch (e) {
        console.error("WS Parse Error:", e);
      }
    };

    return () => {
      clearInterval(interval);
      ws.close();
    };
  }, [router]);

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
    console.log("Logging out of StealthVault...");
    localStorage.clear(); // 🧹 FULL SESSION WIPE
    router.push("/login");
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
          <div className="flex items-center gap-6">
            <div className="hidden sm:flex items-center gap-2 px-3 py-1 bg-red-500/5 border border-red-500/10 rounded-full">
                <span className="relative flex h-1.5 w-1.5">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-red-500"></span>
                </span>
                <span className="text-[9px] font-black text-red-500 uppercase tracking-[0.2em]">Live Monitoring Active</span>
            </div>
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
               { 
                 label: "System Status", 
                 val: status.toUpperCase(), 
                 col: status === "active" || status === "ok" ? "text-green-500" : "text-red-500",
                 icon: <Activity className="w-4 h-4 opacity-20" />
               },
               { 
                 label: "Total Packets", 
                 val: stats.total_packets_analyzed, 
                 col: "text-blue-400",
                 icon: <Server className="w-4 h-4 opacity-20" />
               },
               { 
                 label: "Total Alerts", 
                 val: stats.total_alerts, 
                 col: "text-white",
                 icon: <AlertTriangle className="w-4 h-4 opacity-20" />
               },
               { 
                 label: "Avg Risk Score", 
                 val: (stats.avg_risk_score * 100).toFixed(1), 
                 col: "text-yellow-500", 
                 unit: "%",
                 icon: <Activity className="w-4 h-4 opacity-20" />
               }
             ].map((card, i) => (
                <div key={i} className="bg-gray-900/40 p-6 rounded-3xl border border-gray-800 shadow-xl overflow-hidden relative group hover:border-gray-700 transition-all duration-300">
                    <p className="text-[10px] text-gray-500 uppercase tracking-widest mb-3 font-black">{card.label}</p>
                    <div className="flex items-baseline gap-1">
                        <span className={`text-3xl font-black italic tracking-tighter ${card.col}`}>{card.val}</span>
                        {card.unit && <span className="text-[10px] text-gray-700 font-bold uppercase">{card.unit}</span>}
                    </div>
                    <div className="absolute top-4 right-4 group-hover:scale-125 transition-transform duration-500">
                        {card.icon}
                    </div>
                </div>
             ))}
          </div>

          {/* 🌍 GLOBAL THREAT MAP (FULL WIDTH) */}
          <div className="mb-10">
             <AttackMap alerts={rawAlerts} />
          </div>

          {/* ALERT BREAKDOWN & CHARTS */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-10">
            <div className="lg:col-span-2">
                <StatsCharts distribution={stats.attack_distribution} />
            </div>
            
            <div className="bg-gray-900/40 p-8 rounded-3xl border border-gray-800 shadow-xl">
                <h2 className="text-lg font-black tracking-tighter uppercase italic flex items-center gap-2 mb-8">
                    <span className="text-red-500">🚨</span> Alert Breakdown
                </h2>
                <div className="space-y-6">
                    {[
                        { label: "Critical", val: stats.critical_alerts, color: "bg-red-600", text: "text-red-500" },
                        { label: "High", val: stats.high_alerts, color: "bg-orange-600", text: "text-orange-500" },
                        { label: "Medium", val: stats.medium_alerts, color: "bg-yellow-600", text: "text-yellow-500" },
                        { label: "Low", val: stats.low_alerts, color: "bg-blue-600", text: "text-blue-500" },
                    ].map((item, i) => (
                        <div key={i} className="group cursor-default">
                            <div className="flex justify-between items-end mb-2">
                                <span className={`text-[10px] font-black uppercase tracking-widest ${item.text}`}>{item.label}</span>
                                <span className="text-xl font-black italic tracking-tighter">{item.val}</span>
                            </div>
                            <div className="h-1.5 w-full bg-gray-800 rounded-full overflow-hidden">
                                <div 
                                    className={`h-full ${item.color} transition-all duration-1000 ease-out`} 
                                    style={{ width: `${stats.total_alerts > 0 ? (item.val / stats.total_alerts * 100) : 0}%` }}
                                ></div>
                            </div>
                        </div>
                    ))}
                </div>
                <div className="mt-10 p-4 bg-black/40 rounded-2xl border border-gray-800/50">
                    <p className="text-[10px] text-gray-600 uppercase font-bold tracking-[0.2em] leading-relaxed">
                        Statistical model calibrated for <span className="text-white">Active Detection</span>.
                        Confidence rating: <span className="text-green-500">98.4%</span>
                    </p>
                </div>
            </div>
          </div>

          <div className="bg-gray-900/40 rounded-3xl border border-gray-800 shadow-2xl overflow-hidden transition-all duration-700 mt-10">
            <div className="p-6 border-b border-gray-800 flex items-center justify-between">
              <h2 className="text-lg font-black tracking-tighter uppercase italic flex items-center gap-2">
                <span className="text-red-500 animate-pulse">📡</span> Live Attack Feed
              </h2>
              <div className="flex items-center gap-2">
                <span className="relative flex h-2 w-2">
                   <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
                   <span className="relative inline-flex rounded-full h-2 w-2 bg-red-500"></span>
                </span>
                <span className="text-[10px] text-red-600 font-black tracking-widest uppercase">Streaming Real-Time Alerts</span>
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-gray-800/50 bg-black/20">
                    <th className="p-4 text-[10px] font-black uppercase tracking-widest text-gray-500">Timestamp</th>
                    <th className="p-4 text-[10px] font-black uppercase tracking-widest text-gray-500">Source Node</th>
                    <th className="p-4 text-[10px] font-black uppercase tracking-widest text-gray-500">Threat Vector</th>
                    <th className="p-4 text-[10px] font-black uppercase tracking-widest text-gray-500">Risk Index</th>
                    <th className="p-4 text-[10px] font-black uppercase tracking-widest text-gray-500 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-800/30">
                  {rawAlerts.length === 0 ? (
                    <tr>
                      <td colSpan={5} className="py-20 text-center">
                        <Activity className="w-10 h-10 text-gray-800 mx-auto mb-4 animate-pulse" />
                        <p className="text-[10px] text-gray-600 font-black uppercase tracking-[0.3em] italic">Scanning network packets... All clear.</p>
                      </td>
                    </tr>
                  ) : (
                    rawAlerts.map((alert, i) => (
                      <tr 
                        key={i} 
                        onClick={() => handleAlertClick(alert.id)}
                        className="group hover:bg-red-500/5 cursor-pointer transition-colors"
                      >
                        <td className="p-4">
                          <span className="text-[10px] font-mono text-gray-500 group-hover:text-gray-300 transition-colors">
                            {new Date(alert.timestamp).toLocaleTimeString()}
                          </span>
                        </td>
                        <td className="p-4">
                          <div className="flex items-center gap-2">
                             <div className={`w-1.5 h-1.5 rounded-full ${alert.risk.severity === 'critical' ? 'bg-red-500 shadow-[0_0_8px_red]' : 'bg-orange-500'}`}></div>
                             <span className="text-sm font-black italic tracking-tighter group-hover:text-red-400 transition-colors">{alert.packet.src_ip}</span>
                          </div>
                        </td>
                        <td className="p-4">
                          <span className={`text-[10px] font-black uppercase tracking-widest px-2 py-1 rounded bg-black/40 border ${alert.risk.severity === 'critical' ? 'text-red-500 border-red-900/50' : 'text-orange-400 border-orange-900/50'}`}>
                            {alert.classification.attack_type}
                          </span>
                        </td>
                        <td className="p-4">
                          <div className="flex items-center gap-2">
                            <div className="w-12 h-1 bg-gray-800 rounded-full overflow-hidden">
                              <div className="h-full bg-red-500" style={{ width: `${alert.risk.score * 100}%` }}></div>
                            </div>
                            <span className="text-[10px] font-black text-gray-400 italic">{(alert.risk.score * 100).toFixed(0)}%</span>
                          </div>
                        </td>
                        <td className="p-4 text-right">
                           <button className="text-[10px] font-black uppercase tracking-widest bg-gray-900 group-hover:bg-red-600/20 text-gray-600 group-hover:text-red-500 px-3 py-1 rounded-lg border border-gray-800 group-hover:border-red-500/30 transition-all flex items-center gap-1 ml-auto">
                             Deep Dive <ChevronRight className="w-3 h-3" />
                           </button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
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
