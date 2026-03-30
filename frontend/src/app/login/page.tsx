"use client";

import { useState } from "react";
import { API } from "@/lib/api";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const handleLogin = async () => {
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
      alert("Login successful 🚀");

      localStorage.setItem("token", res.data.access_token);
    } catch (err: any) {
      console.error(err);
      alert("Login failed ❌");
    }
  };

  return (
    <div className="flex h-screen items-center justify-center bg-black text-white">
      <div className="bg-gray-900 p-8 rounded-xl w-96 shadow-lg">
        <h1 className="text-2xl font-bold mb-6 text-center">🔐 Login</h1>

        <input
          type="email"
          placeholder="Email"
          className="w-full p-2 mb-4 rounded bg-black border border-gray-700"
          onChange={(e) => setEmail(e.target.value)}
        />

        <input
          type="password"
          placeholder="Password"
          className="w-full p-2 mb-4 rounded bg-black border border-gray-700"
          onChange={(e) => setPassword(e.target.value)}
        />

        <button
          onClick={handleLogin}
          className="w-full bg-green-500 hover:bg-green-600 p-2 rounded"
        >
          Login
        </button>
      </div>
    </div>
  );
}
