"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { API } from "@/lib/api";
import { Shield, Lock, Mail, ChevronRight, ArrowLeft } from "lucide-react";
import { Logo } from "@/components/Logo";
import Link from "next/link";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  const handleLogin = async () => {
    setIsLoading(true);
    setError("");
    try {
      const res = await API.post(
        "/api/v1/auth/token",
        new URLSearchParams({
          username: email,
          password: password,
        }),
        {
          headers: { "Content-Type": "application/x-www-form-urlencoded" },
        }
      );

      localStorage.setItem("token", res.data.access_token);
      localStorage.setItem("access_token", res.data.access_token);
      router.push("/dashboard");
    } catch (err: any) {
      setError("AUTHENTICATION FAILED: INVALID CREDENTIALS");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex h-screen items-center justify-center bg-cyber-black text-white selection:bg-cyber-red/30 cyber-grid overflow-hidden relative">
      <Link href="/" className="absolute top-10 left-10 flex items-center gap-2 text-[10px] font-black uppercase tracking-widest text-gray-500 hover:text-white transition-colors group">
         <ArrowLeft className="w-3 h-3 group-hover:-translate-x-1 transition-transform" /> Back to Base
      </Link>

      <div className="glass-card p-12 w-[480px] shadow-3xl relative overflow-hidden group border-white/5 bg-black/60">
        <div className="absolute top-0 left-0 w-full h-[2px] bg-gradient-to-r from-transparent via-cyber-red to-transparent"></div>
        
        <div className="text-center mb-12">
          <Logo className="justify-center mb-8" />
          <h1 className="text-2xl font-black italic tracking-tighter uppercase text-glow-red">SECURE LOGIN</h1>
          <p className="text-[10px] text-gray-600 font-bold uppercase tracking-[0.4em] mt-3 italic">Level 4 Authorization Required</p>
        </div>

        <div className="space-y-6">
          {error && (
            <div className="p-4 bg-cyber-red/10 border border-cyber-red/20 rounded-xl flex items-center gap-3 animate-shake">
                <Shield className="w-4 h-4 text-cyber-red shrink-0" />
                <span className="text-[10px] font-black uppercase tracking-widest text-cyber-red">{error}</span>
            </div>
          )}

          <div className="group/input relative">
            <Mail className="absolute left-5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-700 group-focus-within/input:text-cyber-red transition-colors" />
            <input
              type="email"
              placeholder="Operational Email"
              className="w-full p-5 pl-14 rounded-2xl bg-black/40 border border-white/5 focus:border-cyber-red/50 focus:ring-1 focus:ring-cyber-red/20 transition-all outline-none text-sm placeholder:text-gray-700 font-sans font-bold uppercase tracking-widest"
              onChange={(e) => setEmail(e.target.value)}
              disabled={isLoading}
            />
          </div>

          <div className="group/input relative">
            <Lock className="absolute left-5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-700 group-focus-within/input:text-cyber-red transition-colors" />
            <input
              type="password"
              placeholder="Decryption Key"
              className="w-full p-5 pl-14 rounded-2xl bg-black/40 border border-white/5 focus:border-cyber-red/50 focus:ring-1 focus:ring-cyber-red/20 transition-all outline-none text-sm placeholder:text-gray-700 font-sans font-bold uppercase tracking-widest"
              onChange={(e) => setPassword(e.target.value)}
              disabled={isLoading}
            />
          </div>

          <button
            onClick={handleLogin}
            disabled={isLoading}
            className="w-full mt-6 bg-cyber-red hover:bg-red-700 text-white font-black uppercase tracking-[0.3em] p-5 rounded-2xl shadow-[0_0_30px_rgba(239,68,68,0.2)] transition-all active:scale-95 flex items-center justify-center gap-3 group/btn"
          >
            {isLoading ? (
              <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
            ) : (
              <>
                AUTHORIZE ACCESS <ChevronRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
              </>
            )}
          </button>
        </div>

        <p className="mt-10 text-center text-[10px] text-gray-600 uppercase tracking-[0.3em] font-black">
          NO CREDENTIALS? <Link href="/register" className="text-cyber-red hover:text-white transition-colors">DECRYPT ENROLLMENT</Link>
        </p>
      </div>

      {/* FOOTER DECOR */}
      <div className="absolute bottom-10 text-[8px] font-black uppercase tracking-[0.5em] text-gray-800 pointer-events-none">
        STEALTHVAULT AI // SECURE AUTH LINK ALPHA-9
      </div>
    </div>
  );
}
