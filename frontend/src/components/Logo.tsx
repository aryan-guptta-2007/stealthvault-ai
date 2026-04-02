import React from "react";
import { Shield } from "lucide-react";

export const Logo = ({ className = "" }: { className?: string }) => {
  return (
    <div className={`flex items-center gap-2 group cursor-pointer ${className}`}>
      <div className="relative">
        <div className="absolute inset-0 bg-cyber-red/20 blur-lg rounded-lg group-hover:bg-cyber-red/40 transition-all"></div>
        <div className="relative w-8 h-8 bg-gradient-to-br from-cyber-red to-red-700 rounded-lg flex items-center justify-center shadow-[0_0_15px_rgba(239,68,68,0.5)] group-hover:scale-110 transition-transform duration-300">
          <Shield className="w-5 h-5 text-white" />
        </div>
      </div>
      <div className="flex flex-col">
        <span className="text-xl font-black tracking-tighter uppercase italic leading-none text-white">
          StealthVault
        </span>
        <span className="text-[8px] font-bold tracking-[0.3em] uppercase text-cyber-red leading-none mt-1">
          AI Defence
        </span>
      </div>
    </div>
  );
};
