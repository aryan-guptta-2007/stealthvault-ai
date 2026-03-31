"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { API } from "@/lib/api";
import { Shield, Lock, Mail, ChevronRight } from "lucide-react";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleLogin = async () => {
    setIsLoading(true);
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

      console.log("LOGIN SUCCESS:", res.data);
      
      // ✅ STORE TOKENS (Shared keys for compatibility)
      localStorage.setItem("token", res.data.access_token);
      localStorage.setItem("access_token", res.data.access_token);

      console.log("Login success, redirecting...");
      
      // 🚀 REDIRECT TO DASHBOARD (Next.js Navigation)
      router.push("/dashboard");
    } catch (err: any) {
      console.error(err);
      alert("Login failed ❌ - Check your credentials");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex h-screen items-center justify-center bg-black text-white selection:bg-red-500/30">
      <div className="bg-gray-950 border border-gray-800 p-10 rounded-[2rem] w-[450px] shadow-2xl relative overflow-hidden group">
        {/* Glow Effect */}
        <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-red-600 via-red-400 to-red-600"></div>
        
        <div className="text-center mb-10">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-red-600/10 mb-4 group-hover:scale-110 transition-transform">
             <Shield className="w-8 h-8 text-red-500" />
          </div>
          <h1 className="text-3xl font-black italic tracking-tighter uppercase font-mono">Access Vault</h1>
          <p className="text-[10px] text-gray-500 font-bold uppercase tracking-[0.2em] mt-2">Authorization Mandatory</p>
        </div>

        <div className="space-y-4">
          <div className="group/input relative">
            <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-700 group-focus-within/input:text-red-500 transition-colors" />
            <input
              type="email"
              placeholder="Operational Email"
              className="w-full p-4 pl-12 rounded-xl bg-black border border-gray-800 focus:border-red-600/50 focus:ring-1 focus:ring-red-600/30 transition-all outline-none text-sm placeholder:text-gray-700 font-mono"
              onChange={(e) => setEmail(e.target.value)}
              disabled={isLoading}
            />
          </div>

          <div className="group/input relative">
            <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-700 group-focus-within/input:text-red-500 transition-colors" />
            <input
              type="password"
              placeholder="Secure Decryption Key"
              className="w-full p-4 pl-12 rounded-xl bg-black border border-gray-800 focus:border-red-600/50 focus:ring-1 focus:ring-red-600/30 transition-all outline-none text-sm placeholder:text-gray-700 font-mono"
              onChange={(e) => setPassword(e.target.value)}
              disabled={isLoading}
            />
          </div>

          <button
            onClick={handleLogin}
            disabled={isLoading}
            className="w-full mt-6 bg-red-600 hover:bg-red-500 text-white font-black uppercase tracking-widest p-4 rounded-xl shadow-[0_0_20px_rgba(220,38,38,0.3)] transition-all active:scale-95 flex items-center justify-center gap-2 group/btn"
          >
            {isLoading ? (
              <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
            ) : (
              <>
                AUTHENTICATE <ChevronRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
              </>
            )}
          </button>
        </div>

        <p className="mt-8 text-center text-[10px] text-gray-600 uppercase tracking-widest font-bold">
          New Operative? <a href="/register" className="text-red-500 hover:underline">Enroll Now</a>
        </p>
      </div>
    </div>
  );
}
