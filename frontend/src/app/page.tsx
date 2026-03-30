"use client";

import React from "react";
import Link from "next/link";
import { Shield, Brain, Zap, Clock, Lock, Globe, Server, Activity, ChevronRight } from "lucide-react";

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-black text-white font-sans selection:bg-red-500/30 overflow-x-hidden">
      {/* 🌌 CINEMATIC BACKGROUND */}
      <div className="fixed inset-0 z-0">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,#1a1a1a_0%,#000_100%)]"></div>
        <div className="absolute top-0 left-0 w-full h-[1px] bg-gradient-to-r from-transparent via-red-500/20 to-transparent"></div>
        <div className="absolute bottom-0 left-0 w-full h-[1px] bg-gradient-to-r from-transparent via-blue-500/20 to-transparent"></div>
      </div>

      {/* 🧭 NAVIGATION */}
      <nav className="relative z-50 flex items-center justify-between px-6 py-4 border-b border-white/5 backdrop-blur-md bg-black/20">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-red-600 rounded flex items-center justify-center shadow-[0_0_15px_rgba(220,38,38,0.5)]">
            <Shield className="w-5 h-5 text-white" />
          </div>
          <span className="text-xl font-black tracking-tighter uppercase italic">StealthVault</span>
        </div>
        <div className="flex gap-4">
          <Link href="/login" className="px-5 py-2 hover:text-red-500 transition-colors text-sm font-bold uppercase tracking-widest">Login</Link>
          <Link href="/register" className="px-5 py-2 bg-white text-black text-sm font-bold uppercase tracking-widest hover:bg-neutral-200 transition-all rounded">Join Beta</Link>
        </div>
      </nav>

      {/* 🚀 HERO SECTION */}
      <section className="relative z-10 pt-32 pb-20 px-6 text-center max-w-5xl mx-auto">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-red-500/10 border border-red-500/20 mb-8 animate-in fade-in slide-in-from-bottom-2 duration-700">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-red-500"></span>
          </span>
          <span className="text-[10px] font-black tracking-widest uppercase text-red-500">System Active — v1.0.4 Online</span>
        </div>
        
        <h1 className="text-6xl md:text-8xl font-black tracking-tighter mb-6 leading-tight animate-in fade-in slide-in-from-bottom-4 duration-700 delay-100 italic">
          THE <span className="text-transparent bg-clip-text bg-gradient-to-r from-red-600 to-red-400 underline decoration-red-600/30 underline-offset-8">BRAIN</span> OF <br />
          CYBER DEFENSE.
        </h1>
        
        <p className="text-lg md:text-xl text-neutral-400 max-w-2xl mx-auto mb-10 leading-relaxed font-light animate-in fade-in slide-in-from-bottom-6 duration-700 delay-200">
          Autonomous. Real-time. Self-learning. StealthVault AI is an enterprise-grade SOC 
          platform that detects, explains, and neutralizes threats as they happen.
        </p>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-4 animate-in fade-in slide-in-from-bottom-8 duration-700 delay-300">
          <Link href="/register" className="w-full sm:w-auto px-10 py-5 bg-red-600 hover:bg-red-700 text-white font-black text-sm uppercase tracking-[0.2em] transition-all rounded shadow-[0_0_20px_rgba(220,38,38,0.3)] hover:shadow-[0_0_35px_rgba(220,38,38,0.5)] group">
            Start Securing <ChevronRight className="inline-block ml-1 group-hover:translate-x-1 transition-transform" />
          </Link>
          <button className="w-full sm:w-auto px-10 py-5 bg-neutral-900 hover:bg-neutral-800 text-white font-bold text-sm uppercase tracking-widest transition-all rounded border border-white/5">
            View Live Demo
          </button>
        </div>
      </section>

      {/* 🧠 FEATURES GRID */}
      <section className="relative z-10 py-20 px-6 max-w-7xl mx-auto border-t border-white/5 bg-black/40">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-12">
          <div className="space-y-4 group">
            <div className="w-12 h-12 bg-white/5 border border-white/10 rounded-xl flex items-center justify-center group-hover:border-red-500/50 transition-colors">
              <Activity className="w-6 h-6 text-red-500" />
            </div>
            <h3 className="text-2xl font-black italic tracking-tight">Real-Time Inspection</h3>
            <p className="text-neutral-500 leading-relaxed text-sm">
              Deep packet analysis across your infrastructure. High-throughput scanning with sub-millisecond 
              latency for mission-critical apps.
            </p>
          </div>

          <div className="space-y-4 group">
            <div className="w-12 h-12 bg-white/5 border border-white/10 rounded-xl flex items-center justify-center group-hover:border-red-500/50 transition-colors">
              <Brain className="w-6 h-6 text-red-500" />
            </div>
            <h3 className="text-2xl font-black italic tracking-tight">Explainable AI (XAI)</h3>
            <p className="text-neutral-500 leading-relaxed text-sm">
              No more black boxes. Our AI Brain explains exactly <span className="text-white">why</span> it flagged a threat, 
              providing technical reasoning and mitigation steps instantly.
            </p>
          </div>

          <div className="space-y-4 group">
            <div className="w-12 h-12 bg-white/5 border border-white/10 rounded-xl flex items-center justify-center group-hover:border-red-500/50 transition-colors">
              <Zap className="w-6 h-6 text-red-500" />
            </div>
            <h3 className="text-2xl font-black italic tracking-tight">Autonomous Defense</h3>
            <p className="text-neutral-500 leading-relaxed text-sm">
              Defender Agents automatically quarantine threats, unblock safe IPs, and adapt 
              security posturing based on global reputation updates.
            </p>
          </div>
        </div>
      </section>

      {/* 📊 PLATFORM PREVIEW BACKGROUND SCROLL */}
      <section className="relative z-10 py-40 overflow-hidden">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[120%] h-[120%] opacity-20 pointer-events-none">
          <div className="absolute inset-0 bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-[size:24px_24px]"></div>
        </div>
        
        <div className="relative z-10 px-6 text-center max-w-4xl mx-auto">
          <h2 className="text-4xl md:text-5xl font-black italic tracking-tight mb-8">BUILT FOR THE MODERN WEB.</h2>
          <div className="flex flex-wrap justify-center gap-10 opacity-30">
            <span className="text-2xl font-black uppercase tracking-widest tracking-[0.5em]">WebSocket</span>
            <span className="text-2xl font-black uppercase tracking-widest tracking-[0.5em]">Next.js</span>
            <span className="text-2xl font-black uppercase tracking-widest tracking-[0.5em]">PostgreSQL</span>
            <span className="text-2xl font-black uppercase tracking-widest tracking-[0.5em]">FastAPI</span>
            <span className="text-2xl font-black uppercase tracking-widest tracking-[0.5em]">AI Core</span>
          </div>
        </div>
      </section>

      {/* 🛡️ TRUST SECTION */}
      <section className="relative z-10 py-20 bg-neutral-950 border-y border-white/5 px-6">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center gap-20">
          <div className="flex-1 space-y-6">
            <h2 className="text-5xl font-black italic tracking-tighter leading-none">ZERO-TRUST. <br />ZERO-FRICTION.</h2>
            <p className="text-neutral-400 text-lg font-light leading-relaxed">
              StealthVault AI operates silently in the shadows. We provide high-fidelity alerts 
              without disrupting your legitimate traffic, ensuring business continuity while 
              maintaining a hardened posture against DDOS, Brute Force, and XSS attacks.
            </p>
            <div className="grid grid-cols-2 gap-4">
              <div className="p-4 bg-black rounded-lg border border-white/5">
                <p className="text-3xl font-black text-red-500">99.9%</p>
                <p className="text-[10px] text-neutral-500 uppercase font-black uppercase tracking-widest">Uptime Record</p>
              </div>
              <div className="p-4 bg-black rounded-lg border border-white/5">
                <p className="text-3xl font-black text-red-500">1ms</p>
                <p className="text-[10px] text-neutral-500 uppercase font-black uppercase tracking-widest">Analysis Latency</p>
              </div>
            </div>
          </div>
          <div className="flex-1 w-full aspect-square relative group">
            <div className="absolute inset-0 bg-red-600/10 blur-[100px] rounded-full group-hover:bg-red-600/20 transition-all"></div>
            <div className="relative h-full w-full bg-black border border-white/10 rounded-3xl overflow-hidden shadow-2xl flex items-center justify-center group-hover:border-red-500/50 transition-all">
                <Shield className="w-40 h-40 text-red-500 opacity-20 animate-pulse" />
                <div className="absolute top-8 left-8 flex items-center gap-2">
                    <div className="h-2 w-2 bg-red-500 rounded-full animate-ping"></div>
                    <span className="text-[10px] tracking-[0.3em] font-black uppercase opacity-50">Monitoring Instance: Live</span>
                </div>
            </div>
          </div>
        </div>
      </section>

      {/* 🚀 FOOTER */}
      <footer className="relative z-10 py-20 px-6 border-t border-white/5">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center gap-10">
          <div className="flex items-center gap-2 opacity-50">
            <div className="w-5 h-5 bg-white text-black rounded flex items-center justify-center">
              <Shield className="w-3 h-3" />
            </div>
            <span className="text-xs font-black uppercase tracking-widest tracking-tighter">StealthVault AI</span>
          </div>
          <p className="text-[10px] text-neutral-600 uppercase tracking-widest font-bold">
            &copy; 2026 StealthVault Security Group. All rights reserved.
          </p>
          <div className="flex gap-6 opacity-30">
            <Lock className="w-5 h-5" />
            <Globe className="w-5 h-5" />
            <Server className="w-5 h-5" />
          </div>
        </div>
      </footer>
    </div>
  );
}
