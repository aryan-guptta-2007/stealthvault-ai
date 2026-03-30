"use client";

import React from "react";
import { X, Brain, ShieldAlert, Cpu, CheckCircle } from "lucide-react";

interface BrainAnalysis {
  attack_name: string;
  description: string;
  danger_level: string;
  what_is_happening: string;
  how_to_stop: string;
  technical_details: string;
  recommended_actions: string[];
}

interface BrainPanelProps {
  isOpen: boolean;
  onCloseAction: () => void;
  analysis: BrainAnalysis | null;
  loading: boolean;
}

export const BrainPanel: React.FC<BrainPanelProps> = ({ isOpen, onCloseAction, analysis, loading }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-y-0 right-0 w-full md:w-[500px] bg-black border-l border-white/5 z-[100] shadow-[0_0_50px_rgba(0,0,0,0.8)] animate-in slide-in-from-right duration-300">
      <div className="h-full flex flex-col p-8 overflow-y-auto custom-scrollbar selection:bg-red-500/30">
        <header className="flex items-center justify-between mb-10">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-red-600 rounded-lg">
              <Brain className="w-6 h-6 text-white" />
            </div>
            <div>
              <h2 className="text-xl font-black italic tracking-tighter uppercase font-mono">XAI Security Brain</h2>
              <p className="text-[10px] text-red-500 font-bold uppercase tracking-[0.2em]">Explainable AI Analysis</p>
            </div>
          </div>
          <button 
            onClick={onCloseAction}
            className="p-2 hover:bg-neutral-900 rounded-full transition-colors"
          >
            <X className="w-6 h-6 text-neutral-500" />
          </button>
        </header>

        {loading ? (
          <div className="flex-1 flex flex-col items-center justify-center space-y-4">
            <div className="w-12 h-12 border-2 border-red-500 border-t-transparent rounded-full animate-spin"></div>
            <p className="text-[10px] font-black tracking-widest uppercase text-neutral-600">Synthesizing Neural Reasoning...</p>
          </div>
        ) : analysis ? (
          <div className="flex-1 space-y-8 pb-10">
            {/* THREAT OVERVIEW */}
            <div className="p-6 bg-red-950/10 border border-red-500/20 rounded-3xl">
              <div className="flex items-center gap-2 mb-3">
                <ShieldAlert className="w-4 h-4 text-red-500" />
                <span className="text-[10px] font-black uppercase text-red-500 tracking-widest">Identified Threat</span>
              </div>
              <h3 className="text-3xl font-black italic tracking-tighter uppercase mb-2">{analysis.attack_name}</h3>
              <p className="text-sm text-neutral-400 leading-relaxed italic">{analysis.description}</p>
            </div>

            {/* WHAT IS HAPPENING */}
            <section className="space-y-3">
              <div className="flex items-center gap-2 opacity-50">
                <Cpu className="w-4 h-4" />
                <h4 className="text-[10px] font-black uppercase tracking-widest">Autonomous Reasoning</h4>
              </div>
              <div className="p-5 bg-neutral-900/50 border border-white/5 rounded-2xl">
                <p className="text-sm text-neutral-300 leading-relaxed">
                  {analysis.what_is_happening}
                </p>
              </div>
            </section>

            {/* TECHNICAL DETAILS */}
            <section className="space-y-3">
                <h4 className="text-[10px] font-black uppercase tracking-widest opacity-50">Technical Forensics</h4>
                <div className="p-5 bg-black border border-white/5 rounded-2xl font-mono text-[11px] text-blue-400/80 leading-relaxed">
                    {analysis.technical_details}
                </div>
            </section>

             {/* RECOMMENDED ACTIONS */}
             <section className="space-y-3">
                <h4 className="text-[10px] font-black uppercase tracking-widest opacity-50">Mitigation Protocol</h4>
                <div className="space-y-2">
                    {analysis.recommended_actions.map((action, i) => (
                        <div key={i} className="flex items-start gap-3 p-3 bg-green-500/5 border border-green-500/10 rounded-xl group hover:border-green-500/30 transition-colors">
                            <CheckCircle className="w-4 h-4 text-green-500 mt-0.5" />
                            <p className="text-xs text-neutral-400 group-hover:text-green-200 transition-colors">{action}</p>
                        </div>
                    ))}
                </div>
            </section>
          </div>
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center text-center px-10">
             <div className="text-4xl opacity-20 mb-4">🛡️</div>
             <p className="text-xs text-neutral-600 font-bold uppercase tracking-widest leading-loose">
               Select an intercepted packet <br /> for deep neural analysis.
             </p>
          </div>
        )}
      </div>
    </div>
  );
};
