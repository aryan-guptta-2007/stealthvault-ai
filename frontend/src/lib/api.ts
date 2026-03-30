import axios from "axios";

export const API = axios.create({
  baseURL: "https://stealthvault-ai.onrender.com",
});

// 🔐 SESSION HANDLER: Automate Auth Headers
API.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});
