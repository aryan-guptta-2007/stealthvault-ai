# 🚀 Deploying StealthVault AI Frontend

This guide covers the production deployment of the StealthVault AI Next.js frontend.

## 📦 Deployment Options

### 1. Vercel (Recommended)
The easiest way to deploy Next.js apps.
- [ ] Push your code to GitHub.
- [ ] Import the repository into **Vercel**.
- [ ] Set **Build Command**: `npm run build`
- [ ] Set **Output Directory**: `.next`
- [ ] Add Environment Variables (see below).

### 2. Render.com
Use this if you want to keep your Frontend and Backend on the same platform.
- [ ] Select **Static Site** on Render.
- [ ] Connect your GitHub repo.
- [ ] **Build Command**: `npm run build`
- [ ] **Publish Directory**: `out` (Note: If using `output: 'export'` in `next.config.js`)
- [ ] *Recommended for Next.js*: Use a **Web Service** with `npm run start`.

---

## 🔐 Environment Variables

Ensure your frontend knows where the backend is:

| Variable | Description | Value |
| :--- | :--- | :--- |
| `NEXT_PUBLIC_API_URL` | Backend HTTP URL | `https://stealthvault-ai.onrender.com` |
| `NEXT_PUBLIC_WS_URL` | Backend WebSocket URL | `wss://stealthvault-ai.onrender.com/ws` |

---

## 🔥 Production Checklist

1. **Update `next.config.ts`**:
   Ensure you have configured any external image domains or output settings.
   ```typescript
   const nextConfig = {
     output: 'standalone', // Best for Docker/Render
     images: {
       domains: ['stealthvault-ai.onrender.com'],
     },
   };
   ```

2. **Run Local Build Test**:
   Before pushing, verify the build locally:
   ```bash
   npm run build
   ```

3. **CORS Configuration**:
   Ensure your backend has the production frontend domain in its `CORS_ORIGINS` environment variable.

---

## 🛡️ Support
For enterprise scaling or custom agent configurations, contact the **StealthVault Security Group**.
