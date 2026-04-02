"use client";

import { useState } from "react";
import axios from "axios";
import { Shield, Lock, Mail, User, Building, ChevronRight, ArrowLeft } from "lucide-react";
import { Logo } from "@/components/Logo";
import Link from "next/link";

export default function RegisterPage() {
  const [org, setOrg] = useState("");
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  const handleRegister = async () => {
    setIsLoading(true);
    setError("");
    try {
      const res = await axios.post("https://stealthvault-ai.onrender.com/api/v1/auth/register", {
        tenant_name: org,
        username: username,
        email: email,
        password: password,
        plan: "FREE",
      });

      localStorage.setItem("api_key", res.data.api_key);
      localStorage.setItem("tenant_id", res.data.tenant_id);
      window.location.href = "/dashboard";
    } catch (err: any) {
      setError("REGISTRATION FAILED: CHECK DATA INTEGRITY");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex h-screen items-center justify-center bg-cyber-black text-white selection:bg-cyber-red/30 cyber-grid overflow-hidden relative">
      <Link href="/" className="absolute top-10 left-10 flex items-center gap-2 text-[10px] font-black uppercase tracking-widest text-gray-500 hover:text-white transition-colors group">
         <ArrowLeft className="w-3 h-3 group-hover:-translate-x-1 transition-transform" /> Back to Base
      </Link>

      <div className="glass-card p-12 w-[520px] shadow-3xl relative overflow-hidden group border-white/5 bg-black/60">
        <div className="absolute top-0 left-0 w-full h-[2px] bg-gradient-to-r from-transparent via-cyber-red to-transparent"></div>
        
        <div className="text-center mb-12">
          <Logo className="justify-center mb-8" />
          <h1 className="text-2xl font-black italic tracking-tighter uppercase text-glow-red">IDENTITY ENROLLMENT</h1>
          <p className="text-[10px] text-gray-600 font-bold uppercase tracking-[0.4em] mt-3 italic">Establish Your Security Perimeter</p>
        </div>

        <div className="space-y-4">
          {error && (
            <div className="p-4 bg-cyber-red/10 border border-cyber-red/20 rounded-xl flex items-center gap-3">
                <Shield className="w-4 h-4 text-cyber-red shrink-0" />
                <span className="text-[10px] font-black uppercase tracking-widest text-cyber-red">{error}</span>
            </div>
          )}

          <div className="grid grid-cols-2 gap-4">
            <div className="group/input relative">
                <Building className="absolute left-5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-700 group-focus-within/input:text-cyber-red transition-colors" />
                <input
                type="text"
                placeholder="Org"
                className="w-full p-5 pl-14 rounded-2xl bg-black/40 border border-white/5 focus:border-cyber-red/50 transition-all outline-none text-sm placeholder:text-gray-700 font-bold uppercase tracking-widest"
                onChange={(e) => setOrg(e.target.value)}
                />
            </div>
            <div className="group/input relative">
                <User className="absolute left-5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-700 group-focus-within/input:text-cyber-red transition-colors" />
                <input
                type="text"
                placeholder="Name"
                className="w-full p-5 pl-14 rounded-2xl bg-black/40 border border-white/5 focus:border-cyber-red/50 transition-all outline-none text-sm placeholder:text-gray-700 font-bold uppercase tracking-widest"
                onChange={(e) => setUsername(e.target.value)}
                />
            </div>
          </div>

          <div className="group/input relative">
            <Mail className="absolute left-5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-700 group-focus-within/input:text-cyber-red transition-colors" />
            <input
              type="email"
              placeholder="Operational Email"
              className="w-full p-5 pl-14 rounded-2xl bg-black/40 border border-white/5 focus:border-cyber-red/50 transition-all outline-none text-sm placeholder:text-gray-700 font-bold uppercase tracking-widest"
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>

          <div className="group/input relative">
            <Lock className="absolute left-5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-700 group-focus-within/input:text-cyber-red transition-colors" />
            <input
              type="password"
              placeholder="Security Key"
              className="w-full p-5 pl-14 rounded-2xl bg-black/40 border border-white/5 focus:border-cyber-red/50 transition-all outline-none text-sm placeholder:text-gray-700 font-bold uppercase tracking-widest"
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>

          <button
            onClick={handleRegister}
            disabled={isLoading}
            className="w-full mt-6 bg-cyber-red hover:bg-red-700 text-white font-black uppercase tracking-[0.3em] p-5 rounded-2xl shadow-[0_0_30px_rgba(239,68,68,0.2)] transition-all active:scale-95 flex items-center justify-center gap-3 group/btn"
          >
            {isLoading ? (
              <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
            ) : (
              <>
                INITIALIZE ENROLLMENT <ChevronRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
              </>
            )}
          </button>
        </div>

        <p className="mt-10 text-center text-[10px] text-gray-600 uppercase tracking-[0.3em] font-black">
          ALREADY ENROLLED? <Link href="/login" className="text-cyber-red hover:text-white transition-colors">ACCESS VAULT</Link>
        </p>
      </div>

      {/* FOOTER DECOR */}
      <div className="absolute bottom-10 text-[8px] font-black uppercase tracking-[0.5em] text-gray-800 pointer-events-none">
        STEALTHVAULT AI // SECURE IDENTITY ESTABLISHMENT
      </div>
    </div>
  );
}
