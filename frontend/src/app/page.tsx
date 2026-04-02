"use client";

import React from "react";
import Link from "next/link";
import { Shield, Brain, Zap, Clock, Lock, Globe, Server, Activity, ChevronRight, CheckCircle2, User, ArrowRight, ShieldCheck, Terminal, AlertCircle } from "lucide-react";
import { Logo } from "@/components/Logo";

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-cyber-black text-white font-sans selection:bg-cyber-red/30 overflow-x-hidden cyber-grid">
      {/* 🌌 CINEMATIC BACKGROUND ELEMENTS */}
      <div className="fixed inset-0 z-0 pointer-events-none">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,#0a0a0a_0%,#000_100%)]"></div>
        <div className="absolute top-0 left-0 w-full h-[1px] bg-gradient-to-r from-transparent via-cyber-red/30 to-transparent"></div>
        <div className="absolute top-[20%] left-[-10%] w-[40%] h-[40%] bg-cyber-red/5 blur-[120px] rounded-full"></div>
        <div className="absolute bottom-[20%] right-[-10%] w-[40%] h-[40%] bg-cyber-blue/5 blur-[120px] rounded-full"></div>
      </div>

      {/* 🧭 NAVIGATION */}
      <nav className="relative z-50 flex items-center justify-between px-6 py-5 border-b border-white/5 backdrop-blur-xl bg-black/40 sticky top-0">
        <Logo />
        <div className="hidden md:flex items-center gap-8">
          <Link href="#how-it-works" className="text-xs font-bold uppercase tracking-widest text-gray-400 hover:text-white transition-colors">How it Works</Link>
          <Link href="#pricing" className="text-xs font-bold uppercase tracking-widest text-gray-400 hover:text-white transition-colors">Pricing</Link>
          <Link href="#about" className="text-xs font-bold uppercase tracking-widest text-gray-400 hover:text-white transition-colors">About</Link>
        </div>
        <div className="flex gap-4">
          <Link href="/login" className="px-5 py-2 text-gray-400 hover:text-white transition-colors text-xs font-bold uppercase tracking-widest">Login</Link>
          <Link href="/register" className="px-6 py-2.5 bg-white text-black text-xs font-black uppercase tracking-widest hover:bg-cyber-red hover:text-white transition-all rounded-lg shadow-lg">Start Securing</Link>
        </div>
      </nav>

      {/* 🚀 HERO SECTION */}
      <section className="relative z-10 pt-32 pb-24 px-6 text-center max-w-6xl mx-auto">
        <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-cyber-red/10 border border-cyber-red/20 mb-10 animate-in fade-in slide-in-from-bottom-2 duration-700">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyber-red opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-cyber-red"></span>
          </span>
          <span className="text-[10px] font-black tracking-[0.2em] uppercase text-cyber-red">Global Threat Coverage Active — v1.2.0</span>
        </div>
        
        <h1 className="text-5xl md:text-8xl font-black tracking-tighter mb-8 leading-[0.9] animate-in fade-in slide-in-from-bottom-4 duration-700 delay-100">
          🚨 STOP CYBER ATTACKS <br />
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyber-red to-red-400">IN REAL-TIME</span> USING AI.
        </h1>
        
        <p className="text-lg md:text-xl text-gray-400 max-w-3xl mx-auto mb-12 leading-relaxed font-medium animate-in fade-in slide-in-from-bottom-6 duration-700 delay-200">
          Most apps look "low trust" until they're breached. StealthVault AI is an 
          <span className="text-white"> enterprise-grade autonomous SOC</span> that detects, explains, and 
          neutralizes threats before they touch your data.
        </p>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-6 mb-20 animate-in fade-in slide-in-from-bottom-8 duration-700 delay-300">
          <Link href="/register" className="w-full sm:w-auto px-12 py-5 bg-cyber-red hover:bg-red-700 text-white font-black text-sm uppercase tracking-[0.2em] transition-all rounded-xl shadow-[0_0_30px_rgba(239,68,68,0.4)] hover:shadow-[0_0_50px_rgba(239,68,68,0.6)] group">
            Join the Secured Beta <ChevronRight className="inline-block ml-1 group-hover:translate-x-1 transition-transform" />
          </Link>
          <Link href="/login" className="w-full sm:w-auto px-12 py-5 bg-white/5 hover:bg-white/10 text-white font-black text-sm uppercase tracking-widest transition-all rounded-xl border border-white/10 backdrop-blur-sm">
            Access Command Center
          </Link>
        </div>

        {/* SOCIAL PROOF RIBBON */}
        <div className="pt-16 border-t border-white/5 mb-24 animate-in fade-in duration-1000 delay-500">
            <p className="text-[10px] font-black uppercase tracking-[0.5em] text-gray-600 mb-10 italic">Hardened Infrastructure for:</p>
            <div className="flex flex-wrap justify-center gap-12 opacity-30 grayscale hover:grayscale-0 hover:opacity-100 transition-all duration-700 border-b border-white/5 pb-16">
                {["Next.js 15", "FastAPI", "React 19", "ReCharts", "PostgreSQL", "Quantum-AI"].map((tech) => (
                    <div key={tech} className="flex items-center gap-3 group">
                        <span className="text-sm font-black italic tracking-tighter text-white group-hover:text-cyber-red transition-colors">{tech}</span>
                    </div>
                ))}
            </div>
            <div className="mt-12 flex justify-center">
                <div className="flex items-center gap-4 px-8 py-3 bg-white/[0.02] border border-white/5 rounded-full">
                    <div className="flex -space-x-3">
                        {[1,2,3,4,5].map(i => (
                            <div key={i} className="w-8 h-8 rounded-full border-2 border-cyber-black bg-gray-900 flex items-center justify-center relative">
                                <div className="w-6 h-6 rounded-full bg-cyber-red/20 flex items-center justify-center">
                                    <User className="w-3 h-3 text-cyber-red/40" />
                                </div>
                            </div>
                        ))}
                    </div>
                    <span className="text-[10px] font-black uppercase text-gray-500 tracking-widest leading-none">
                        Deploying for <span className="text-white">124+ Cybersecurity Engineers</span> in Beta
                    </span>
                </div>
            </div>
        </div>

        {/* TRUST BADGES */}
        <div className="mt-24 grid grid-cols-2 md:grid-cols-4 gap-8 opacity-40 grayscale hover:grayscale-0 transition-all duration-700">
            <div className="flex items-center justify-center gap-2">
                <ShieldCheck className="w-5 h-5 text-cyber-blue" />
                <span className="text-[10px] font-black uppercase tracking-widest">SOC-2 READY</span>
            </div>
            <div className="flex items-center justify-center gap-2">
                <Lock className="w-5 h-5 text-green-500" />
                <span className="text-[10px] font-black uppercase tracking-widest">AES-256 ENCRYPTION</span>
            </div>
            <div className="flex items-center justify-center gap-2">
                <Globe className="w-5 h-5 text-cyber-red" />
                <span className="text-[10px] font-black uppercase tracking-widest">GLOBAL REPUTATION</span>
            </div>
            <div className="flex items-center justify-center gap-2">
                <Brain className="w-5 h-5 text-purple-500" />
                <span className="text-[10px] font-black uppercase tracking-widest">EXPLAINABLE AI</span>
            </div>
        </div>
      </section>

      {/* 🛠️ HOW IT WORKS SECTION */}
      <section id="how-it-works" className="relative z-10 py-32 px-6 border-t border-white/5 bg-black/20">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-20">
            <h2 className="text-sm font-black text-cyber-red uppercase tracking-[0.5em] mb-4">Precision Defense</h2>
            <h3 className="text-4xl md:text-6xl font-black tracking-tighter italic">HOW IT WORKS.</h3>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {[
              {
                step: "01",
                title: "Deep Inspection",
                desc: "We analyze every packet hitting your endpoint using our proprietary neural engine, identifying anomalies in sub-milliseconds.",
                icon: <Activity className="w-8 h-8 text-cyber-red" />
              },
              {
                step: "02",
                title: "Agent Analysis",
                desc: "Our AI 'Analyst' explain exactly why a request is malicious, providing high-fidelity reasoning instead of generic alerts.",
                icon: <Brain className="w-8 h-8 text-cyber-blue" />
              },
              {
                step: "03",
                title: "Instant Neutralization",
                desc: "The 'Defender' agent instantly quarantines the threat and updates global reputations to prevent repeat attacks.",
                icon: <Shield className="w-8 h-8 text-green-500" />
              }
            ].map((item, i) => (
              <div key={i} className="glass-card p-10 relative overflow-hidden group">
                <div className="absolute top-0 right-0 p-4 opacity-5 text-8xl font-black italic group-hover:opacity-10 transition-opacity">{item.step}</div>
                <div className="mb-6 w-16 h-16 rounded-2xl bg-white/5 flex items-center justify-center group-hover:scale-110 transition-transform">
                  {item.icon}
                </div>
                <h4 className="text-2xl font-black italic tracking-tight mb-4">{item.title}</h4>
                <p className="text-gray-400 text-sm leading-relaxed">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* 🔥 ATTACK STORY ENGINE (USP) */}
      <section className="relative z-10 py-32 bg-cyber-red/5 border-y border-white/5">
        <div className="max-w-7xl mx-auto px-6 grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
            <div className="space-y-8">
                <div className="inline-block px-3 py-1 bg-cyber-red text-white text-[10px] font-black uppercase tracking-widest rounded">The Hook</div>
                <h2 className="text-5xl font-black tracking-tighter italic leading-none text-glow-red">
                    THE ATTACK <br /> STORY ENGINE.
                </h2>
                <p className="text-lg text-gray-400 leading-relaxed">
                    Don't just see logs—see the story. StealthVault AI predicts the intent behind the attack.
                </p>
                <div className="space-y-4">
                    <div className="flex items-start gap-4 p-4 bg-black/40 rounded-xl border border-white/5">
                        <Terminal className="w-5 h-5 text-cyber-red mt-1" />
                        <div>
                            <p className="text-xs font-black uppercase text-cyber-red mb-1">Predicted Sequence</p>
                            <p className="text-sm text-gray-300">Russia IP → Port Scan [Detected] → Brute Force Attempt [Blocked] → Lateral Movement [Prevented]</p>
                        </div>
                    </div>
                </div>
                <button className="flex items-center gap-2 text-sm font-black uppercase tracking-widest text-cyber-red hover:text-white transition-colors group">
                    Explain The Story <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                </button>
            </div>
            <div className="relative aspect-video glass-card overflow-hidden shadow-2xl">
                <div className="absolute inset-0 bg-black/80 flex flex-col p-6 font-mono text-xs overflow-hidden">
                    <div className="flex justify-between items-center mb-4 border-b border-white/10 pb-2">
                        <span className="text-green-500 font-bold tracking-widest uppercase">Live Attack Trace</span>
                        <span className="text-cyber-red animate-pulse">● RECORDING</span>
                    </div>
                    <div className="space-y-2 text-gray-500">
                        <p><span className="text-white opacity-40">09:41:02</span> [INFRA] Incoming SYN Request from 103.55.24.11 (Moscow, RU)</p>
                        <p><span className="text-white opacity-40">09:41:02</span> [BRAIN] Analyzing packet metadata... Anomaly high (0.94)</p>
                        <p className="text-cyber-red"><span className="text-white opacity-40">09:41:03</span> [ALARM] Pattern matched: Directory Traversal Attempt Detected</p>
                        <p className="text-cyber-red font-bold animate-blink">[ACTION] IP 103.55.24.11 Blacklisted at Edge Gateway</p>
                        <p className="text-cyber-blue"><span className="text-white opacity-40">09:41:04</span> [STORY] Attacker signature matched "Group-44" TTPs.</p>
                        <p className="text-green-500 mt-4 opacity-50">... Waiting for next sequence ...</p>
                    </div>
                </div>
                <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent"></div>
            </div>
        </div>
      </section>

      {/* 👤 ABOUT THE FOUNDER SECTION */}
      <section id="about" className="relative z-10 py-32 px-6">
        <div className="max-w-4xl mx-auto glass-card p-12 flex flex-col md:flex-row items-center gap-12 border-cyber-blue/20">
            <div className="w-40 h-40 rounded-full bg-gradient-to-br from-cyber-red to-cyber-blue p-1 flex-shrink-0">
                <div className="w-full h-full rounded-full bg-black flex items-center justify-center overflow-hidden">
                    <User className="w-20 h-20 text-white opacity-20" />
                    {/* Replace with real photo if available */}
                </div>
            </div>
            <div className="space-y-6 text-center md:text-left">
                <div className="inline-block px-3 py-1 bg-cyber-blue text-white text-[10px] font-black uppercase tracking-widest rounded">Founder & Lead Engineer</div>
                <h3 className="text-4xl font-black tracking-tighter italic">ARYAN GUPTA</h3>
                <p className="text-gray-400 leading-relaxed italic">
                    "I built StealthVault AI because standard firewalls are blind to intent. We combine 
                    <span className="text-white"> CSE rigor</span> with <span className="text-white"> Cybersecurity aggression</span> to create a platform that doesn't just block—it learns."
                </p>
                <div className="flex flex-wrap justify-center md:justify-start gap-4">
                    <span className="text-[10px] font-black uppercase tracking-widest px-3 py-1 bg-white/5 rounded border border-white/10">B.Tech CSE</span>
                    <span className="text-[10px] font-black uppercase tracking-widest px-3 py-1 bg-white/5 rounded border border-white/10">Cybersecurity Expert</span>
                    <span className="text-[10px] font-black uppercase tracking-widest px-3 py-1 bg-white/5 rounded border border-white/10">AI Researcher</span>
                </div>
            </div>
        </div>
      </section>

      {/* 💰 PRICING PREVIEW */}
      <section id="pricing" className="relative z-10 py-32 px-6">
        <div className="max-w-7xl mx-auto">
            <div className="text-center mb-20">
                <h3 className="text-4xl md:text-6xl font-black tracking-tighter italic">SCALABLE SECURITY.</h3>
                <p className="mt-4 text-gray-500 uppercase tracking-widest font-black text-xs">Choose the plan that fits your growth</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                {/* FREE */}
                <div className="glass-card p-10 flex flex-col group border-white/5">
                    <h4 className="text-xl font-black uppercase tracking-widest mb-2">Free Tier</h4>
                    <p className="text-gray-500 text-sm mb-8">For personal security enthusiasts.</p>
                    <div className="text-4xl font-black italic mb-8">₹0 <span className="text-xs text-gray-600">/ forever</span></div>
                    <ul className="space-y-4 mb-12 flex-1">
                        <li className="flex items-center gap-2 text-sm text-gray-400 group-hover:text-white"><CheckCircle2 className="w-4 h-4 text-green-500" /> 100k Packets / Month</li>
                        <li className="flex items-center gap-2 text-sm text-gray-400 group-hover:text-white"><CheckCircle2 className="w-4 h-4 text-green-500" /> Basic AI Analyst</li>
                        <li className="flex items-center gap-2 text-sm text-gray-400 group-hover:text-white"><CheckCircle2 className="w-4 h-4 text-green-500" /> Community Support</li>
                    </ul>
                    <Link href="/register" className="w-full py-4 text-center border border-white/10 hover:bg-white/5 rounded-xl text-xs font-black uppercase tracking-widest transition-all">Get Started</Link>
                </div>

                {/* PRO */}
                <div className="glass-card p-10 flex flex-col relative border-cyber-red/30 shadow-[0_0_40px_rgba(239,68,68,0.1)] group overflow-hidden">
                    <div className="absolute top-0 right-0 bg-cyber-red text-white px-6 py-1.5 text-[8px] font-black uppercase tracking-[0.3em] origin-bottom-left rotate-45 translate-x-[25%] translate-y-[50%]">Best Value</div>
                    <h4 className="text-xl font-black uppercase tracking-widest mb-2 text-cyber-red">Pro SOC</h4>
                    <p className="text-gray-500 text-sm mb-8">For startups & high-growth apps.</p>
                    <div className="text-4xl font-black italic mb-8">₹499 <span className="text-xs text-gray-600">/ month</span></div>
                    <ul className="space-y-4 mb-12 flex-1">
                        <li className="flex items-center gap-2 text-sm text-white"><CheckCircle2 className="w-4 h-4 text-cyber-red" /> Unlimited Packets</li>
                        <li className="flex items-center gap-2 text-sm text-white"><CheckCircle2 className="w-4 h-4 text-cyber-red" /> Advanced Explainer Engine</li>
                        <li className="flex items-center gap-2 text-sm text-white"><CheckCircle2 className="w-4 h-4 text-cyber-red" /> 24/7 SOC Dashboard</li>
                        <li className="flex items-center gap-2 text-sm text-white"><CheckCircle2 className="w-4 h-4 text-cyber-red" /> Attack Story Generator</li>
                    </ul>
                    <Link href="/register" className="w-full py-4 text-center bg-cyber-red hover:bg-red-700 rounded-xl text-xs font-black uppercase tracking-widest transition-all shadow-lg hover:shadow-cyber-red/20 text-white">Upgrade to Pro</Link>
                </div>

                {/* ENTERPRISE */}
                <div className="glass-card p-10 flex flex-col group border-white/5">
                    <h4 className="text-xl font-black uppercase tracking-widest mb-2">Enterprise</h4>
                    <p className="text-gray-500 text-sm mb-8">Custom hardening for large infra.</p>
                    <div className="text-4xl font-black italic mb-8">CONTACT <span className="text-xs text-gray-600">/ sales</span></div>
                    <ul className="space-y-4 mb-12 flex-1">
                        <li className="flex items-center gap-2 text-sm text-gray-400 group-hover:text-white"><CheckCircle2 className="w-4 h-4 text-cyber-blue" /> Dedicated Defensive Agents</li>
                        <li className="flex items-center gap-2 text-sm text-gray-400 group-hover:text-white"><CheckCircle2 className="w-4 h-4 text-cyber-blue" /> SOC-2 Compliance Pack</li>
                        <li className="flex items-center gap-2 text-sm text-gray-400 group-hover:text-white"><CheckCircle2 className="w-4 h-4 text-cyber-blue" /> On-Premise Deployment</li>
                    </ul>
                    <Link href="/contact" className="w-full py-4 text-center border border-white/10 hover:bg-white/5 rounded-xl text-xs font-black uppercase tracking-widest transition-all">Contact Sales</Link>
                </div>
            </div>
        </div>
      </section>

      {/* 🚀 FOOTER */}
      <footer className="relative z-10 py-20 px-6 border-t border-white/5 bg-black">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-start gap-16">
          <div className="space-y-6">
            <Logo />
            <p className="text-xs text-gray-600 max-w-xs uppercase leading-relaxed font-bold tracking-widest">
              Autonomous security for the future of the internet. Built with aggression, intelligence, and pride.
            </p>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-12">
            <div className="space-y-4">
                <h5 className="text-[10px] font-black uppercase tracking-[0.3em] text-white">Platform</h5>
                <ul className="space-y-2 text-xs text-gray-500 font-bold uppercase tracking-widest">
                    <li><Link href="#how-it-works" className="hover:text-cyber-red transition-colors">Features</Link></li>
                    <li><Link href="/dashboard" className="hover:text-cyber-red transition-colors">SOC Dashboard</Link></li>
                    <li><Link href="/register" className="hover:text-cyber-red transition-colors">Join Beta</Link></li>
                </ul>
            </div>
            <div className="space-y-4">
                <h5 className="text-[10px] font-black uppercase tracking-[0.3em] text-white">Company</h5>
                <ul className="space-y-2 text-xs text-gray-500 font-bold uppercase tracking-widest">
                    <li><Link href="#about" className="hover:text-cyber-red transition-colors">Founder</Link></li>
                    <li><Link href="/pricing" className="hover:text-cyber-red transition-colors">Pricing</Link></li>
                    <li><Link href="/privacy" className="hover:text-cyber-red transition-colors">Trust Center</Link></li>
                </ul>
            </div>
            <div className="space-y-4">
                <h5 className="text-[10px] font-black uppercase tracking-[0.3em] text-white">Legal</h5>
                <ul className="space-y-2 text-xs text-gray-500 font-bold uppercase tracking-widest">
                    <li><Link href="/privacy" className="hover:text-cyber-red transition-colors">Privacy Policy</Link></li>
                    <li><Link href="/terms" className="hover:text-cyber-red transition-colors">Terms of Service</Link></li>
                </ul>
            </div>
          </div>
        </div>
        <div className="max-w-7xl mx-auto mt-20 pt-8 border-t border-white/5 flex flex-col md:flex-row justify-between gap-6 opacity-30">
            <p className="text-[10px] font-black uppercase tracking-widest text-gray-500">&copy; 2026 StealthVault AI by Aryan Gupta. All rights reserved.</p>
            <div className="flex gap-6">
                <ShieldCheck className="w-4 h-4 cursor-help" />
                <Lock className="w-4 h-4 cursor-help" />
                <Server className="w-4 h-4 cursor-help" />
            </div>
        </div>
      </footer>
    </div>
  );
}
