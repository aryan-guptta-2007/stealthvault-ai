"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { API } from "@/lib/api";
import { StatsCharts } from "@/components/dashboard/StatsCharts";
import { BrainPanel } from "@/components/dashboard/BrainPanel";
import AttackMap from "@/components/dashboard/AttackMap";
import { OffensivePanel } from "@/components/dashboard/OffensivePanel";
import { QuarantineTable } from "@/components/dashboard/QuarantineTable";
import { TerminalLogs } from "@/components/dashboard/TerminalLogs";
import { Activity, Shield, AlertTriangle, Cpu, Terminal, LogOut, Server, ChevronRight, Zap, Radio, Target, Bell, Brain } from "lucide-react";
import { Logo } from "@/components/Logo";
import Link from "next/link";
import { OnboardingModal } from "@/components/dashboard/OnboardingModal";

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
  const router = useRouter();
  const [status, setStatus] = useState("Loading...");
  const [events, setEvents] = useState<string[]>([]);
  const [rawAlerts, setRawAlerts] = useState<AlertData[]>([]);
  const [stats, setStats] = useState<any>(null);
  
  // AI Brain State
  const [selectedAnalysis, setSelectedAnalysis] = useState<BrainAnalysis | null>(null);
  const [isBrainOpen, setIsBrainOpen] = useState(false);
  const [brainLoading, setBrainLoading] = useState(false);

  // Onboarding & Demo State
  const [showOnboarding, setShowOnboarding] = useState(false);
  const [isDemoMode, setIsDemoMode] = useState(false);
  const [demoIntervalId, setDemoIntervalId] = useState<NodeJS.Timeout | null>(null);

  useEffect(() => {
    const token = localStorage.getItem("access_token") || localStorage.getItem("token");

    if (!token) {
      router.push("/login");
      return;
    }

    const fetchDashboardData = async () => {
      try {
        const statsRes = await API.get("/api/v1/dashboard/");
        setStats(statsRes.data);
        setStatus(statsRes.data.system_status.toLowerCase());

        const alertsRes = await API.get("/api/v1/alerts/", { params: { limit: 20 } });
        setRawAlerts(alertsRes.data);
      } catch (err) {
        console.error("Dashboard Data Fetch Failed:", err);
      }
    };

    fetchDashboardData();
    const interval = setInterval(fetchDashboardData, 5000);

    // Initial Onboarding Check
    const hasVisited = localStorage.getItem("sv_onboarded");
    if (!hasVisited) {
      setShowOnboarding(true);
    }

    const ws_url = process.env.NEXT_PUBLIC_WS_URL || "wss://stealthvault-ai.onrender.com/ws";
    const ws = new WebSocket(ws_url);

    ws.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        
        if (payload.type === "ALERT") {
          // If we receive a real alert, disable demo mode
          setIsDemoMode(false);
          if (demoIntervalId) clearInterval(demoIntervalId);

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

    return () => {
      clearInterval(interval);
      ws.close();
      if (demoIntervalId) clearInterval(demoIntervalId);
    };
  }, [router, demoIntervalId]);

  // Demo Mode Simulation Logic
  useEffect(() => {
    if (rawAlerts.length === 0 && !isDemoMode) {
      const timer = setTimeout(() => {
        setIsDemoMode(true);
        startSimulation();
      }, 3000); // Wait 3s before starting demo
      return () => clearTimeout(timer);
    }
  }, [rawAlerts]);

  const startSimulation = () => {
    const mockAlerts = [
      {
        id: "sim-1",
        timestamp: new Date().toISOString(),
        packet: { src_ip: "185.220.101.44", dst_port: 80 },
        classification: { attack_type: "SQL Injection" },
        risk: { score: 0.92, severity: "critical" },
        geo_location: { country: "Russia" },
        anomaly: { confidence: 0.98 }
      },
      {
        id: "sim-2",
        timestamp: new Date().toISOString(),
        packet: { src_ip: "45.146.165.37", dst_port: 443 },
        classification: { attack_type: "DDoS Flood" },
        risk: { score: 0.85, severity: "high" },
        geo_location: { country: "Ukraine" },
        anomaly: { confidence: 0.91 }
      },
      {
        id: "sim-3",
        timestamp: new Date().toISOString(),
        packet: { src_ip: "103.255.44.12", dst_port: 22 },
        classification: { attack_type: "SSH Brute-Force" },
        risk: { score: 0.78, severity: "high" },
        geo_location: { country: "China" },
        anomaly: { confidence: 0.88 }
      }
    ];

    let i = 0;
    const id = setInterval(() => {
      const alert = mockAlerts[i % mockAlerts.length];
      const newAlert = { ...alert, timestamp: new Date().toISOString(), id: `sim-${Date.now()}` };
      
      const msg = `🚀 [DEMO-ACTIVE] [${newAlert.risk.severity.toUpperCase()}] ${newAlert.classification.attack_type} intercepted (Simulation)`;
      
      setEvents((prev) => [msg, ...prev.slice(0, 19)]);
      setRawAlerts((prev) => [newAlert, ...prev.slice(0, 19)]);
      i++;
    }, 4000);

    setDemoIntervalId(id);
  };

  const handleOnboardingComplete = () => {
    localStorage.setItem("sv_onboarded", "true");
    setShowOnboarding(false);
  };

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
    localStorage.clear();
    router.push("/login");
  };

  if (!stats) return (
    <div className="min-h-screen bg-cyber-black flex flex-col items-center justify-center space-y-6 cyber-grid">
        <div className="relative">
            <div className="w-16 h-16 border-2 border-cyber-red border-t-transparent rounded-full animate-spin"></div>
            <div className="absolute inset-0 border-2 border-cyber-blue border-b-transparent rounded-full animate-spin-reverse opacity-50"></div>
        </div>
        <p className="text-[10px] font-black tracking-[0.5em] uppercase text-cyber-red animate-pulse italic">Connecting to SOC Node Alpha-1...</p>
    </div>
  );

  return (
    <div className="flex min-h-screen bg-cyber-black text-white font-sans selection:bg-cyber-red/30 cyber-grid">
      <div className="fixed inset-0 pointer-events-none opacity-20">
          <div className="absolute top-0 left-0 w-full h-[2px] bg-cyber-red animate-scanline"></div>
      </div>

      <BrainPanel 
        isOpen={isBrainOpen} 
        onCloseAction={() => setIsBrainOpen(false)} 
        analysis={selectedAnalysis} 
        loading={brainLoading}
      />

      {showOnboarding && <OnboardingModal onCloseAction={handleOnboardingComplete} />}

      {/* SIDEBAR */}
      <div className="w-80 bg-black/80 border-r border-white/5 flex flex-col p-8 sticky top-0 h-screen z-40 backdrop-blur-3xl">
        <div className="mb-16">
            <Logo />
        </div>

        <nav className="flex-1 space-y-12">
          <div className="space-y-4">
              <h3 className="text-[10px] font-black text-gray-600 uppercase tracking-[0.5em] mb-6">Operations</h3>
              <ul className="space-y-3">
                <li className="flex items-center gap-3 p-4 bg-cyber-red text-white rounded-xl shadow-[0_0_20px_rgba(239,68,68,0.2)] font-black uppercase italic tracking-widest text-[10px]">
                  <Activity className="w-4 h-4" /> Global Dashboard
                </li>
                <li className="flex items-center gap-3 p-4 text-gray-500 hover:text-white transition-all group cursor-pointer border border-transparent hover:border-white/5 rounded-xl">
                  <Target className="w-4 h-4 group-hover:text-cyber-red" /> 
                  <span className="text-[10px] font-black uppercase tracking-widest italic group-hover:italic group-hover:translate-x-1 transition-transform">Target Intel</span>
                  <span className="ml-auto text-[8px] bg-white/5 px-2 py-0.5 rounded text-gray-600 font-bold uppercase italic group-hover:bg-cyber-red group-hover:text-white">PRO</span>
                </li>
                <li className="flex items-center gap-3 p-4 text-gray-500 hover:text-white transition-all group cursor-pointer border border-transparent hover:border-white/5 rounded-xl">
                  <Radio className="w-4 h-4 group-hover:text-cyber-blue" />
                  <span className="text-[10px] font-black uppercase tracking-widest italic group-hover:translate-x-1 transition-transform">Nodes</span>
                  <span className="ml-auto text-[8px] bg-white/5 px-2 py-0.5 rounded text-gray-600 font-bold uppercase italic group-hover:border-cyber-blue group-hover:text-white">PRO</span>
                </li>
              </ul>
          </div>

          <div className="space-y-4">
              <h3 className="text-[10px] font-black text-gray-600 uppercase tracking-[0.5em] mb-6">Active Channels</h3>
              <div className="space-y-3">
                  <div className="flex items-center gap-4 p-4 glass-card border-white/5 group">
                      <div className="w-2 h-2 rounded-full bg-cyber-blue shadow-[0_0_10px_rgba(59,130,246,0.5)] animate-pulse"></div>
                      <span className="text-[10px] font-black text-gray-400 group-hover:text-white uppercase tracking-widest">Telegram SOC</span>
                      <Shield className="w-3 h-3 ml-auto text-gray-700 group-hover:text-cyber-blue transition-colors" />
                  </div>
                  <div className="flex items-center gap-4 p-4 glass-card border-white/5 group opacity-50 grayscale hover:grayscale-0 hover:opacity-100 transition-all">
                      <div className="w-2 h-2 rounded-full bg-cyber-red shadow-[0_0_10px_rgba(239,68,68,0.5)] animate-pulse"></div>
                      <span className="text-[10px] font-black text-gray-400 group-hover:text-white uppercase tracking-widest">SIEM Stream</span>
                      <Terminal className="w-3 h-3 ml-auto text-gray-700 group-hover:text-cyber-red transition-colors" />
                  </div>
              </div>
          </div>
        </nav>

        <div className="mt-auto pt-8 border-t border-white/5 space-y-6">
           <div className="p-4 glass-card border-cyber-red/20 bg-cyber-red/5">
                <p className="text-[8px] font-black uppercase text-cyber-red tracking-[0.3em] mb-1">Account Standing</p>
                <div className="flex justify-between items-end">
                    <p className="text-xs font-black italic tracking-tighter uppercase">Free Beta</p>
                    <Link href="/pricing" className="text-[8px] text-white bg-cyber-red px-2 py-0.5 rounded uppercase font-black tracking-widest hover:bg-white hover:text-cyber-red transition-colors">Upgrade</Link>
                </div>
           </div>
          <button
            onClick={handleLogout}
            className="w-full flex items-center justify-center gap-4 text-xs font-black uppercase tracking-[0.3em] text-gray-600 hover:text-cyber-red hover:bg-cyber-red/5 p-4 rounded-xl transition-all duration-300"
          >
            <LogOut className="w-4 h-4" /> Sign-Off
          </button>
        </div>
      </div>

      {/* MAIN CONTENT */}
      <div className="flex-1 flex flex-col">
        <header className="h-24 border-b border-white/5 flex items-center justify-between px-10 bg-cyber-black/60 backdrop-blur-2xl z-30 sticky top-0 overflow-hidden">
          <div className="flex items-center gap-4">
              <div className="w-1.5 h-8 bg-cyber-red rounded-full"></div>
              <div>
                <h1 className="text-xl font-black tracking-tighter uppercase italic text-glow-red">War Room Alpha-1</h1>
                <p className="text-[10px] text-gray-600 uppercase tracking-widest font-bold">Node Identity: SV-SOC-773</p>
              </div>
          </div>
          <div className="flex items-center gap-10">
            <div className="hidden sm:flex items-center gap-3 px-6 py-2 bg-cyber-red/10 border border-cyber-red/20 rounded-full group cursor-help">
                <Bell className="w-3 h-3 text-cyber-red group-hover:animate-bounce" />
                <span className="text-[10px] font-black text-cyber-red uppercase tracking-[0.2em] italic">Real-Time Threat Feed Active</span>
            </div>
            <div className="flex items-center gap-3 bg-white/5 border border-white/10 px-6 py-2 rounded-full">
              <span className={`h-2 w-2 rounded-full ${status === 'active' || status === 'ok' ? 'bg-green-500 shadow-[0_0_12px_rgba(34,197,94,0.8)]' : 'bg-yellow-500 animate-pulse'}`}></span>
              <span className="text-[10px] font-black text-gray-400 uppercase tracking-widest">{status} Status</span>
            </div>
          </div>
        </header>

        <main className="flex-1 p-10 overflow-y-auto custom-scrollbar space-y-12">
          {/* STATS INFOCARDS */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
             {[
               { 
                 label: "System Status", 
                 val: status.toUpperCase(), 
                 col: status === "active" || status === "ok" ? "text-green-500" : "text-cyber-red",
                 icon: <Activity className="w-4 h-4" />,
                 glow: status === "active" || status === "ok" ? "group-hover:text-green-400" : "group-hover:text-cyber-red"
               },
               { 
                 label: "Analyzed (Cumulative)", 
                 val: stats.total_packets_analyzed, 
                 col: "text-white",
                 icon: <Server className="w-4 h-4" />,
                 glow: "group-hover:text-cyber-blue"
               },
               { 
                 label: "Intercepted Threats", 
                 val: stats.total_alerts, 
                 col: "text-cyber-red",
                 icon: <Shield className="w-4 h-4" />,
                 glow: "group-hover:text-cyber-red"
               },
               { 
                 label: "Avg Explanatory Index", 
                 val: (stats.avg_risk_score * 100).toFixed(1), 
                 col: "text-cyber-blue", 
                 unit: "%",
                 icon: <Brain className="w-4 h-4" />,
                 glow: "group-hover:text-cyber-blue"
               }
             ].map((card, i) => (
                <div key={i} className="glass-card group p-8 overflow-hidden relative transition-all duration-700 hover:scale-[1.02] cursor-default border-white/5 hover:border-white/10 shadow-2xl">
                    <div className="absolute top-0 left-0 w-full h-[1px] bg-gradient-to-r from-transparent via-white/10 to-transparent"></div>
                    <p className="text-[10px] text-gray-600 uppercase tracking-[0.3em] mb-4 font-black">{card.label}</p>
                    <div className="flex items-baseline gap-2 relative z-10">
                        <span className={`text-4xl font-black italic tracking-tighter ${card.col} group-hover:scale-105 transition-transform duration-500`}>{card.val}</span>
                        {card.unit && <span className="text-[10px] text-gray-700 font-bold uppercase">{card.unit}</span>}
                    </div>
                    <div className={`absolute top-6 right-8 opacity-5 group-hover:opacity-30 group-hover:-translate-y-1 transition-all duration-700 ${card.glow}`}>
                        {card.icon}
                    </div>
                </div>
             ))}
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* 🌍 GLOBAL THREAT MAP */}
            <div className="lg:col-span-2 glass-card h-[500px] relative overflow-hidden group">
                 <div className="absolute top-0 left-0 px-6 py-4 z-20 flex items-center gap-3">
                    <div className="w-2 h-2 bg-cyber-red rounded-full animate-ping"></div>
                    <span className="text-[10px] font-black uppercase tracking-widest text-cyber-red italic text-glow-red">Live Global Radar</span>
                 </div>
                 <AttackMap alerts={rawAlerts} />
            </div>

            {/* ⚡ SYSTEM LOGS */}
            <TerminalLogs />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
             <OffensivePanel />
             <QuarantineTable />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            <div className="lg:col-span-2">
                <StatsCharts distribution={stats.attack_distribution} />
            </div>
            
            <div className="glass-card p-10 flex flex-col justify-center gap-8 bg-black/40 border-white/5 relative group overflow-hidden">
                <div className="absolute -top-10 -right-10 w-40 h-40 bg-cyber-red/5 blur-[80px] rounded-full group-hover:bg-cyber-red/10 transition-all"></div>
                
                <h2 className="text-xl font-black tracking-tighter uppercase italic flex items-center gap-4 text-glow-red">
                    <AlertTriangle className="w-6 h-6 text-cyber-red animate-pulse" /> 
                    Threat Distribution
                </h2>
                
                <div className="space-y-6">
                    {[
                        { label: "Critical Risk", val: stats.critical_alerts, color: "bg-red-600", text: "text-cyber-red", sub: "Immediate Neutralization" },
                        { label: "High Risk", val: stats.high_alerts, color: "bg-orange-500", text: "text-orange-500", sub: "Active Observation" },
                        { label: "Normal Flow", val: stats.low_alerts + stats.medium_alerts, color: "bg-cyber-blue", text: "text-cyber-blue", sub: "Routine Filtration" },
                    ].map((item, i) => (
                        <div key={i} className="group/row cursor-default">
                            <div className="flex justify-between items-end mb-3">
                                <div>
                                    <span className={`text-[10px] font-black uppercase tracking-widest ${item.text}`}>{item.label}</span>
                                    <p className="text-[8px] text-gray-500 font-bold uppercase tracking-widest group-hover/row:text-gray-300 transition-colors">{item.sub}</p>
                                </div>
                                <span className="text-2xl font-black italic tracking-tighter">{item.val}</span>
                            </div>
                            <div className="h-1.5 w-full bg-white/5 rounded-full overflow-hidden border border-white/5 p-[1px]">
                                <div 
                                    className={`h-full ${item.color} transition-all duration-1500 ease-in-out relative`} 
                                    style={{ width: `${stats.total_alerts > 0 ? (item.val / stats.total_alerts * 100) : 0}%` }}
                                >
                                    <div className="absolute inset-0 bg-white/20 animate-pulse"></div>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
          </div>

          {/* 📡 LIVE ATTACK FEED (UPGRADED) */}
          <div className="glass-card bg-black/60 border-white/5 overflow-hidden transition-all duration-700 shadow-3xl group">
            <div className="p-8 border-b border-white/5 flex items-center justify-between bg-white/[0.02]">
              <h2 className="text-xl font-black tracking-tighter uppercase italic flex items-center gap-4">
                <Radio className="w-6 h-6 text-cyber-red animate-pulse" />
                Interception History
              </h2>
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-3 px-4 py-1.5 bg-black/40 border border-white/5 rounded-lg">
                    <span className="text-[10px] text-gray-600 font-black tracking-widest uppercase">Node: <span className="text-white">India-Center</span></span>
                </div>
                <div className="flex items-center gap-3 px-4 py-1.5 bg-green-500/10 border border-green-500/20 rounded-lg">
                    <span className="text-[10px] text-green-500 font-black tracking-widest uppercase italic">Streaming Packets</span>
                </div>
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-white/5 bg-white/5">
                    <th className="p-6 text-[10px] font-black uppercase tracking-[0.2em] text-gray-500">Trace/Timestamp</th>
                    <th className="p-6 text-[10px] font-black uppercase tracking-[0.2em] text-gray-500">Attacker Source</th>
                    <th className="p-6 text-[10px] font-black uppercase tracking-[0.2em] text-gray-500">Threat Vector</th>
                    <th className="p-6 text-[10px] font-black uppercase tracking-[0.2em] text-gray-500">Risk Intensity</th>
                    <th className="p-6 text-[10px] font-black uppercase tracking-[0.2em] text-gray-500 text-right">SOC Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  {rawAlerts.length === 0 ? (
                    <tr>
                      <td colSpan={5} className="py-24 text-center">
                        <Activity className="w-16 h-16 text-white/5 mx-auto mb-8 animate-pulse" />
                        <p className="text-[10px] text-gray-700 font-black uppercase tracking-[0.4em] italic leading-loose">
                            Analyzing Incoming Buffer... <br /> Network Posture Status: <span className="text-green-500">Fortified</span>
                        </p>
                      </td>
                    </tr>
                  ) : (
                    rawAlerts.map((alert, i) => (
                      <tr 
                        key={i} 
                        onClick={() => handleAlertClick(alert.id)}
                        className="group/row hover:bg-cyber-red/[0.03] cursor-pointer transition-all duration-300"
                      >
                        <td className="p-6">
                          <div className="space-y-1">
                              <span className="text-[10px] font-mono text-gray-500 group-hover/row:text-white transition-colors">
                                {new Date(alert.timestamp).toLocaleTimeString()}
                              </span>
                              <p className="text-[8px] text-gray-700 font-black uppercase tracking-[0.2em]">Alpha-Node Link</p>
                          </div>
                        </td>
                        <td className="p-6">
                          <div className="flex items-center gap-4">
                             <div className={`w-2 h-2 rounded-full ${alert.risk.severity === 'critical' ? 'bg-cyber-red shadow-[0_0_12px_rgba(239,68,68,1)]' : 'bg-orange-500 shadow-[0_0_8px_rgba(249,115,22,0.5)]'}`}></div>
                             <div className="space-y-1">
                                <span className="text-lg font-black italic tracking-tighter group-hover/row:text-cyber-red transition-colors">{alert.packet.src_ip}</span>
                                <p className="text-[8px] text-gray-600 font-bold uppercase tracking-widest">{alert.geo_location?.country || "Earth-Orbit"}</p>
                             </div>
                          </div>
                        </td>
                        <td className="p-6">
                          <span className={`text-[10px] font-black uppercase tracking-widest px-4 py-1.5 rounded-lg bg-black border ${alert.risk.severity === 'critical' ? 'text-cyber-red border-cyber-red/20 text-glow-red' : 'text-orange-400 border-orange-900/30'}`}>
                            {alert.classification.attack_type}
                          </span>
                        </td>
                        <td className="p-6">
                          <div className="flex items-center gap-4">
                            <div className="w-16 h-1 bg-white/5 rounded-full overflow-hidden border border-white/5">
                              <div className={`${alert.risk.severity === 'critical' ? 'bg-cyber-red' : 'bg-orange-500'} h-full transition-all duration-1000`} style={{ width: `${alert.risk.score * 100}%` }}></div>
                            </div>
                            <span className={`text-[10px] font-black italic ${alert.risk.severity === 'critical' ? 'text-cyber-red' : 'text-gray-500'}`}>{(alert.risk.score * 100).toFixed(0)}</span>
                          </div>
                        </td>
                        <td className="p-6 text-right">
                           <button className="text-[10px] font-black uppercase tracking-widest bg-white/5 group-hover/row:bg-cyber-red group-hover/row:text-white px-6 py-2 rounded-xl border border-white/5 transition-all flex items-center gap-2 ml-auto shadow-lg">
                             Deep Analysis <ChevronRight className="w-3 h-3 group-hover/row:translate-x-1 transition-transform" />
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
        .custom-scrollbar::-webkit-scrollbar { width: 8px; }
        .custom-scrollbar::-webkit-scrollbar-track { background: #050505; }
        .custom-scrollbar::-webkit-scrollbar-thumb { background: #1a1a1a; border-radius: 20px; border: 2px solid #050505; }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover { background: #ef4444; }
        
        .custom-scrollbar-thin::-webkit-scrollbar { width: 4px; }
        .custom-scrollbar-thin::-webkit-scrollbar-track { background: transparent; }
        .custom-scrollbar-thin::-webkit-scrollbar-thumb { background: #1a1a1a; border-radius: 10px; }
        
        @keyframes scanline {
            0% { transform: translateY(-100%); opacity: 0; }
            50% { opacity: 0.5; }
            100% { transform: translateY(100vh); opacity: 0; }
        }

        .animate-scanline {
            animation: scanline 4s linear infinite;
        }

        @keyframes spin-reverse {
            from { transform: rotate(0deg); }
            to { transform: rotate(-360deg); }
        }
        .animate-spin-reverse {
            animation: spin-reverse 2s linear infinite;
        }
      `}</style>
    </div>
  );
}
