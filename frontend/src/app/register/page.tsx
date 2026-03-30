"use client";

import { useState } from "react";
import { API } from "@/lib/api";

export default function RegisterPage() {
  const [tenantName, setTenantName] = useState("");
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const handleRegister = async () => {
    try {
      const res = await API.post("/api/v1/auth/register", {
        tenant_name: tenantName,
        username,
        email,
        password,
        plan: "FREE",
      });

      console.log("REGISTER SUCCESS:", res.data);
      alert("Registered successfully 🚀");
    } catch (err: any) {
      console.error(err);
      alert("Registration failed ❌");
    }
  };

  return (
    <div className="flex h-screen items-center justify-center bg-black text-white">
      <div className="bg-gray-900 p-8 rounded-xl w-96 shadow-lg">
        <h1 className="text-2xl font-bold mb-6 text-center">
          🧑‍💻 Register
        </h1>

        <input
          type="text"
          placeholder="Organization Name"
          className="w-full p-2 mb-4 rounded bg-black border border-gray-700"
          onChange={(e) => setTenantName(e.target.value)}
        />

        <input
          type="text"
          placeholder="Username"
          className="w-full p-2 mb-4 rounded bg-black border border-gray-700"
          onChange={(e) => setUsername(e.target.value)}
        />

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
          onClick={handleRegister}
          className="w-full bg-blue-500 hover:bg-blue-600 p-2 rounded"
        >
          Register
        </button>
      </div>
    </div>
  );
}
