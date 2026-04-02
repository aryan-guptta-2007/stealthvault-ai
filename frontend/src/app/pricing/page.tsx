"use client";

import React from "react";
import Link from "next/link";
import { CheckCircle2, ChevronLeft, Shield, Zap, Globe, Lock, Server, Activity } from "lucide-react";
import { Logo } from "@/components/Logo";

export default function PricingPage() {
  return (
    <div className="min-h-screen bg-cyber-black text-white font-sans selection:bg-cyber-red/30 cyber-grid">
      {/* 🧭 NAVIGATION */}
      <nav className="relative z-50 flex items-center justify-between px-6 py-5 border-b border-white/5 backdrop-blur-xl bg-black/40 sticky top-0">
        <div className="flex items-center gap-6">
            <Link href="/" className="p-2 hover:bg-white/5 rounded-full transition-colors group">
                <ChevronLeft className="w-5 h-5 text-gray-500 group-hover:text-white" />
            </Link>
            <Logo />
        </div>
        <div className="flex gap-4">
          <Link href="/login" className="px-6 py-2.5 bg-white/5 text-white text-xs font-black uppercase tracking-widest hover:bg-white/10 transition-all rounded-lg border border-white/10">Dashboard</Link>
        </div>
      </nav>

      <main className="relative z-10 py-24 px-6 max-w-7xl mx-auto">
        <div className="text-center mb-24 space-y-6">
            <h1 className="text-5xl md:text-7xl font-black tracking-tighter italic text-glow-red">PRICING TIERS.</h1>
            <p className="text-gray-500 uppercase tracking-[0.5em] font-black text-xs">Choose your level of protection</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-12">
            {/* FREE TIER */}
            <div className="glass-card p-12 flex flex-col group border-white/5 relative overflow-hidden h-full">
                <div className="absolute -top-10 -right-10 w-40 h-40 bg-white/5 blur-[100px] rounded-full group-hover:bg-white/10 transition-all"></div>
                <div className="mb-10 text-gray-500">
                    <h2 className="text-2xl font-black uppercase tracking-widest mb-2">COMMUNITY</h2>
                    <p className="text-xs font-bold uppercase tracking-widest italic leading-relaxed">For security researchers & hobbyists.</p>
                </div>
                <div className="mb-12">
                    <span className="text-6xl font-black italic tracking-tighter">₹0</span>
                    <span className="text-[10px] text-gray-700 font-black uppercase tracking-widest ml-2">/ Forever</span>
                </div>
                <ul className="space-y-6 mb-16 flex-1">
                    {[
                        "100,000 Packets / Month",
                        "Basic AI Interception",
                        "Community Threat Feed",
                        "Standard SOC View",
                        "Shared API Rate Limits"
                    ].map((feature, i) => (
                        <li key={i} className="flex items-start gap-4 group/item">
                            <CheckCircle2 className="w-5 h-5 text-gray-700 group-hover/item:text-green-500 transition-colors shrink-0" />
                            <span className="text-sm font-medium text-gray-400 group-hover/item:text-white transition-colors">{feature}</span>
                        </li>
                    ))}
                </ul>
                <Link href="/register" className="w-full py-5 text-center border border-white/10 hover:bg-white/5 rounded-xl text-xs font-black uppercase tracking-widest transition-all hover:text-cyber-red hover:border-cyber-red/30">Get Started Free</Link>
            </div>

            {/* PRO SOC - RECOMMENDED */}
            <div className="glass-card p-12 flex flex-col relative border-cyber-red/30 bg-cyber-red/[0.02] shadow-[0_0_80px_rgba(239,68,68,0.1)] group overflow-hidden h-full scale-[1.05] z-10 transition-all hover:scale-[1.07]">
                <div className="absolute top-0 right-0 bg-cyber-red text-white px-12 py-2 text-[10px] font-black uppercase tracking-[0.4em] origin-bottom-left rotate-45 translate-x-[20%] translate-y-[80%] shadow-lg">Popular</div>
                <div className="mb-10">
                    <div className="flex items-center gap-2 mb-2">
                        <Zap className="w-4 h-4 text-cyber-red" />
                        <h2 className="text-2xl font-black uppercase tracking-widest text-cyber-red">PRO SOC</h2>
                    </div>
                    <p className="text-gray-500 text-xs font-bold uppercase tracking-widest italic leading-relaxed">For production apps & startups.</p>
                </div>
                <div className="mb-12">
                    <span className="text-7xl font-black italic tracking-tighter text-glow-red">₹499</span>
                    <span className="text-[10px] text-gray-500 font-black uppercase tracking-widest ml-2">/ Month</span>
                </div>
                <ul className="space-y-6 mb-16 flex-1">
                    {[
                        "Unlimited Network Packets",
                        "XAI Reasoning Engine (Why/How)",
                        "Predictive Attack Story Generator",
                        "Automated Defensive Blockades",
                        "Priority Forensic Data Retention",
                        "Global Reputation Reputation Sync",
                        "Slack/Telegram SOC Alerts"
                    ].map((feature, i) => (
                        <li key={i} className="flex items-start gap-4">
                            <CheckCircle2 className="w-5 h-5 text-cyber-red shrink-0" />
                            <span className="text-sm font-bold text-white uppercase tracking-tight">{feature}</span>
                        </li>
                    ))}
                </ul>
                <Link href="/register" className="w-full py-6 text-center bg-cyber-red hover:bg-red-700 rounded-xl text-sm font-black uppercase tracking-[0.2em] transition-all shadow-[0_0_30px_rgba(239,68,68,0.4)] hover:shadow-[0_0_50px_rgba(239,68,68,0.6)] text-white">Upgrade to Pro</Link>
            </div>

            {/* ENTERPRISE */}
            <div className="glass-card p-12 flex flex-col group border-white/5 relative overflow-hidden h-full">
                <div className="absolute -top-10 -right-10 w-40 h-40 bg-cyber-blue/5 blur-[100px] rounded-full group-hover:bg-cyber-blue/10 transition-all"></div>
                <div className="mb-10 text-gray-500">
                    <h2 className="text-2xl font-black uppercase tracking-widest mb-2">ULTIMATE</h2>
                    <p className="text-xs font-bold uppercase tracking-widest italic leading-relaxed">Custom hardened infrastructure.</p>
                </div>
                <div className="mb-12">
                    <span className="text-5xl font-black italic tracking-tighter">CUSTOM</span>
                    <span className="text-[10px] text-gray-700 font-black uppercase tracking-widest ml-2">/ Yearly</span>
                </div>
                <ul className="space-y-6 mb-16 flex-1">
                    {[
                        "On-Premise Node Clusters",
                        "Dedicated Offensive Agents",
                        "ZKP Guard Logic Integration",
                        "SOC-2 Audit Package",
                        "1hr Critical Reaction SLA"
                    ].map((feature, i) => (
                        <li key={i} className="flex items-start gap-4 group/item">
                            <CheckCircle2 className="w-5 h-5 text-cyber-blue shrink-0" />
                            <span className="text-sm font-medium text-gray-400 group-hover/item:text-white transition-colors">{feature}</span>
                        </li>
                    ))}
                </ul>
                <Link href="/contact" className="w-full py-5 text-center border border-white/5 bg-white/[0.02] hover:bg-white/10 rounded-xl text-xs font-black uppercase tracking-widest transition-all">Consult Engineers</Link>
            </div>
        </div>

        {/* COMPARISON TABLE */}
        <div className="mt-32 glass-card border-white/5 overflow-hidden">
            <div className="p-10 border-b border-white/5 h-20 flex items-center bg-white/[0.01]">
                <h3 className="text-lg font-black uppercase tracking-[0.3em] italic">FEATURE MATRIX.</h3>
            </div>
            <div className="overflow-x-auto">
                <table className="w-full text-left">
                    <thead>
                        <tr className="border-b border-white/5 bg-white/5">
                            <th className="p-8 text-[10px] font-black uppercase tracking-widest text-gray-400">Functionality</th>
                            <th className="p-8 text-[10px] font-black uppercase tracking-widest text-gray-400">Community</th>
                            <th className="p-8 text-[10px] font-black uppercase tracking-widest text-gray-400">Pro SOC</th>
                            <th className="p-8 text-[10px] font-black uppercase tracking-widest text-gray-400">Ultimate</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-white/5 font-mono text-[10px]">
                        {[
                            { name: "Max Throughput", free: "100k Packets", pro: "Unlimited", ent: "Custom Cluster" },
                            { name: "AI Explanations", free: "Basic", pro: "Advanced (XAI)", ent: "Custom Models" },
                            { name: "Alert Latency", free: "10s Fallback", pro: "<100ms Live", ent: "Dedicated Lane" },
                            { name: "Global Reputation", free: "Daily Update", pro: "Real-time Sync", ent: "Private Oracle" },
                            { name: "Integrations", free: "None", pro: "Webhook/Slack", ent: "SIEM Support" },
                            { name: "Isolation", free: "Multi-tenant", pro: "Isolated Workspace", ent: "Single Instance" },
                        ].map((row, i) => (
                            <tr key={i} className="hover:bg-white/[0.02] transition-colors">
                                <td className="p-8 font-sans font-black uppercase tracking-widest text-gray-300">{row.name}</td>
                                <td className="p-8 text-gray-500 uppercase">{row.free}</td>
                                <td className="p-8 text-cyber-red uppercase font-bold">{row.pro}</td>
                                <td className="p-8 text-cyber-blue uppercase font-bold">{row.ent}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
      </main>

      {/* 🚀 FOOTER */}
      <footer className="relative z-10 py-20 px-6 border-t border-white/5 bg-black mt-24">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center gap-10">
          <Logo />
          <p className="text-[10px] text-gray-600 uppercase tracking-widest font-bold">
            &copy; 2026 StealthVault Security Group. Built by Aryan Gupta.
          </p>
          <div className="flex gap-8 opacity-20">
            <Lock className="w-5 h-5" />
            <Globe className="w-5 h-5" />
            <Server className="w-5 h-5" />
          </div>
        </div>
      </footer>
    </div>
  );
}
