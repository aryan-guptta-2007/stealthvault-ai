"use client";

import { useState } from "react";
import axios from "axios";

export default function RegisterPage() {
  const [org, setOrg] = useState("");
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const handleRegister = async () => {
    // 🧪 Payload Validation Log
    console.log("INITIALIZING ONBOARDING:", {
      organization_name: org,
      username: username,
      email: email,
      password: (password ? "********" : "EMPTY")
    });

    try {
      const res = await axios.post("https://stealthvault-ai.onrender.com/api/v1/auth/register", {
        organization_name: org,
        username: username,
        email: email,
        password: password,
      });

      console.log("SUCCESS:", res.data);
      alert("Registered successfully 🚀");
    } catch (err: any) {
      console.error("ERROR RESPONSE:", err.response?.data || err.message);
      alert("Registration failed ❌ - See console for details");
    }
  };

  return (
    <div className="flex h-screen items-center justify-center bg-black text-white selection:bg-red-500/30">
      <div className="bg-gray-950 border border-gray-800 p-10 rounded-[2rem] w-[450px] shadow-2xl relative overflow-hidden group">
        <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-red-600 via-red-400 to-red-600"></div>
        
        <div className="text-center mb-10">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-red-600/10 mb-4 group-hover:scale-110 transition-transform">
             <span className="text-3xl">🛡️</span>
          </div>
          <h1 className="text-3xl font-black italic tracking-tighter uppercase font-mono">Join StealthVault</h1>
          <p className="text-[10px] text-gray-500 font-bold uppercase tracking-[0.2em] mt-2">Initialize Your Identity</p>
        </div>

        <div className="space-y-4">
          <div className="group/input relative">
            <input
              type="text"
              placeholder="Organization Name"
              className="w-full p-4 rounded-xl bg-black border border-gray-800 focus:border-red-600/50 focus:ring-1 focus:ring-red-600/30 transition-all outline-none text-sm placeholder:text-gray-700 font-mono"
              onChange={(e) => setOrg(e.target.value)}
            />
          </div>

          <div className="group/input relative">
            <input
              type="text"
              placeholder="Username"
              className="w-full p-4 rounded-xl bg-black border border-gray-800 focus:border-red-600/50 focus:ring-1 focus:ring-red-600/30 transition-all outline-none text-sm placeholder:text-gray-700 font-mono"
              onChange={(e) => setUsername(e.target.value)}
            />
          </div>

          <div className="group/input relative">
            <input
              type="email"
              placeholder="Email"
              className="w-full p-4 rounded-xl bg-black border border-gray-800 focus:border-red-600/50 focus:ring-1 focus:ring-red-600/30 transition-all outline-none text-sm placeholder:text-gray-700 font-mono"
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>

          <div className="group/input relative">
            <input
              type="password"
              placeholder="Password"
              className="w-full p-4 rounded-xl bg-black border border-gray-800 focus:border-red-600/50 focus:ring-1 focus:ring-red-600/30 transition-all outline-none text-sm placeholder:text-gray-700 font-mono"
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>

          <button
            onClick={handleRegister}
            className="w-full mt-6 bg-red-600 hover:bg-red-500 text-white font-black uppercase tracking-widest p-4 rounded-xl shadow-[0_0_20px_rgba(220,38,38,0.3)] transition-all active:scale-95"
          >
            Create Global Account
          </button>
        </div>

        <p className="mt-8 text-center text-[10px] text-gray-600 uppercase tracking-widest font-bold">
          Already Enrolled? <a href="/login" className="text-red-500 hover:underline">Access Vault</a>
        </p>
      </div>
    </div>
  );
}
