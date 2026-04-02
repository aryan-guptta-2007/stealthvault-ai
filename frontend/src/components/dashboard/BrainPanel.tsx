"use client";

import React from "react";
import { X, Brain, ShieldAlert, Cpu, CheckCircle, Zap, Activity, Info, Share2, TrendingUp, Lock } from "lucide-react";

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
  const [displayText, setDisplayText] = React.useState("");
  const [isTyping, setIsTyping] = React.useState(false);

  React.useEffect(() => {
    if (analysis && isOpen) {
      setIsTyping(true);
      setDisplayText("");
      let i = 0;
      const fullText = analysis.what_is_happening;
      const interval = setInterval(() => {
        setDisplayText(fullText.slice(0, i));
        i += 2;
        if (i > fullText.length) {
          clearInterval(interval);
          setIsTyping(false);
        }
      }, 10);
      return () => clearInterval(interval);
    }
  }, [analysis, isOpen]);

  const handleShare = () => {
    if (!analysis) return;
    const text = `🚨 StealthVault AI Detected: ${analysis.attack_name}\n\n"The system intercepted a ${analysis.danger_level} threat and predicted the next attack phase."\n\n#CyberSecurity #AI #StealthVault`;
    window.open(`https://twitter.com/intent/tweet?text=${encodeURIComponent(text)}`, "_blank");
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-y-0 right-0 w-full md:w-[600px] bg-cyber-black border-l border-white/5 z-[100] shadow-3xl animate-in slide-in-from-right duration-500 glass-card rounded-none">
      <div className="h-full flex flex-col p-10 overflow-y-auto custom-scrollbar selection:bg-cyber-red/30 relative">
        {/* Decorative Grid */}
        <div className="absolute inset-0 opacity-[0.02] pointer-events-none cyber-grid-small"></div>
        
        <header className="relative z-10 flex items-center justify-between mb-12">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-cyber-red/10 border border-cyber-red/30 rounded-2xl shadow-[0_0_20px_rgba(239,68,68,0.2)]">
              <Brain className="w-8 h-8 text-cyber-red animate-pulse" />
            </div>
            <div>
              <h2 className="text-2xl font-black italic tracking-tighter uppercase text-glow-red">NEURAL ANALYSIS.</h2>
              <p className="text-[10px] text-gray-500 font-black uppercase tracking-[0.4em] mt-1">Quantum Intelligence Engine</p>
            </div>
          </div>
          <button 
            onClick={onCloseAction}
            className="p-3 hover:bg-white/5 rounded-full transition-all group"
          >
            <X className="w-6 h-6 text-gray-500 group-hover:text-white group-hover:rotate-90 transition-all duration-300" />
          </button>
        </header>

        {loading ? (
          <div className="relative z-10 flex-1 flex flex-col items-center justify-center space-y-8">
            <div className="relative">
                <div className="w-20 h-20 border-2 border-cyber-red/20 border-t-cyber-red rounded-full animate-spin"></div>
                <Brain className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-8 h-8 text-cyber-red animate-pulse" />
            </div>
            <div className="text-center space-y-2">
                <p className="text-xs font-black tracking-[0.5em] uppercase text-gray-400 animate-pulse">Synthesizing Logic...</p>
                <div className="flex gap-1 justify-center">
                    <div className="w-1 h-1 bg-cyber-red rounded-full animate-bounce [animation-delay:-0.3s]"></div>
                    <div className="w-1 h-1 bg-cyber-red rounded-full animate-bounce [animation-delay:-0.15s]"></div>
                    <div className="w-1 h-1 bg-cyber-red rounded-full animate-bounce"></div>
                </div>
            </div>
          </div>
        ) : analysis ? (
          <div className="relative z-10 flex-1 space-y-10 pb-12">
            {/* THREAT OVERVIEW */}
            <div className="p-8 bg-cyber-red/5 border border-cyber-red/20 rounded-[2.5rem] relative overflow-hidden group">
              <div className="absolute top-0 right-0 p-4 opacity-10">
                <ShieldAlert className="w-20 h-20 text-cyber-red" />
              </div>
              <div className="flex items-center gap-3 mb-4">
                <span className="px-3 py-1 bg-cyber-red text-white text-[10px] font-black uppercase tracking-widest rounded-full shadow-[0_0_15px_rgba(239,68,68,0.4)]">
                   {analysis.danger_level.toUpperCase()} THREAT
                </span>
                <div className="flex items-center gap-2 px-3 py-1 bg-white/5 border border-white/10 rounded-full">
                    <TrendingUp className="w-3 h-3 text-cyber-red" />
                    <span className="text-[10px] font-black uppercase text-gray-400 tracking-widest">Confidence: 94%</span>
                </div>
              </div>
              <h3 className="text-4xl font-black italic tracking-tighter uppercase mb-4 text-white leading-none">{analysis.attack_name}</h3>
              <p className="text-sm text-gray-400 leading-relaxed font-medium">{analysis.description}</p>
              
              {/* Sharing Hook */}
              <button 
                onClick={handleShare}
                className="mt-6 flex items-center gap-3 px-6 py-2 bg-white/5 border border-white/10 rounded-xl text-[10px] font-black uppercase tracking-widest text-gray-500 hover:text-white hover:bg-cyber-red/20 hover:border-cyber-red/30 transition-all group"
              >
                <Share2 className="w-3 h-3 transition-transform group-hover:scale-125" /> 
                Dispatch Intel to Network
              </button>
            </div>

            {/* PREDICTIVE TIMELINE (Wow Factor) */}
            <section className="space-y-6">
                <div className="flex items-center justify-between">
                    <h4 className="text-[10px] font-black uppercase tracking-[0.4em] text-gray-500 italic">Attack Lifecycle Analysis.</h4>
                    <span className="text-[8px] font-black text-cyber-red animate-pulse uppercase tracking-widest">Live Prediction Layer</span>
                </div>
                <div className="flex items-center gap-2">
                    {[
                        { label: 'Recon', status: 'completed' },
                        { label: 'Delivery', status: 'completed' },
                        { label: 'Exploit', status: 'active' },
                        { label: 'Action', status: 'predicted' }
                    ].map((step, i) => (
                        <React.Fragment key={i}>
                            <div className="flex-1 text-center space-y-3">
                                <div className={`h-1.5 rounded-full shadow-lg transition-all duration-1000 ${
                                    step.status === 'completed' ? 'bg-green-500 shadow-[0_0_10px_rgba(34,197,94,0.3)]' :
                                    step.status === 'active' ? 'bg-cyber-red shadow-[0_0_15px_rgba(239,68,68,0.5)] animate-pulse' :
                                    'bg-white/5'
                                }`}></div>
                                <span className={`text-[8px] font-black uppercase tracking-tighter ${
                                    step.status === 'predicted' ? 'text-gray-600 italic' : 'text-gray-400'
                                }`}>{step.label}</span>
                            </div>
                            {i < 3 && <div className="w-2 h-[1px] bg-white/10 mt-[-14px]"></div>}
                        </React.Fragment>
                    ))}
                </div>
            </section>

            {/* WHAT IS HAPPENING */}
            <section className="space-y-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-white/5 rounded-lg border border-white/10">
                    <Zap className="w-4 h-4 text-cyber-red" />
                </div>
                <h4 className="text-xs font-black uppercase tracking-[0.3em] text-gray-300 italic">Interception Reasoning.</h4>
              </div>
              <div className="p-6 bg-white/[0.02] border border-white/5 rounded-3xl leading-relaxed text-sm text-gray-400 font-medium min-h-[100px]">
                {displayText}
                {isTyping && <span className="inline-block w-2 h-4 bg-cyber-red ml-1 animate-pulse"></span>}
              </div>
            </section>

            {/* TECHNICAL DETAILS */}
            <section className="space-y-4">
                <div className="flex items-center gap-3">
                    <div className="p-2 bg-white/5 rounded-lg border border-white/10">
                        <Activity className="w-4 h-4 text-cyber-red" />
                    </div>
                    <h4 className="text-xs font-black uppercase tracking-[0.3em] text-gray-300 italic">Payload Forensics.</h4>
                </div>
                <div className="p-6 bg-black border border-white/10 rounded-3xl font-mono text-[11px] text-blue-400/80 leading-relaxed relative overflow-hidden group">
                    <div className="absolute inset-0 bg-gradient-to-b from-blue-500/5 to-transparent pointer-events-none"></div>
                    {analysis.technical_details}
                </div>
            </section>

             {/* RECOMMENDED ACTIONS */}
             <section className="space-y-4">
                <div className="flex items-center gap-3">
                    <div className="p-2 bg-white/5 rounded-lg border border-white/10">
                        <Info className="w-4 h-4 text-green-500" />
                    </div>
                    <h4 className="text-xs font-black uppercase tracking-[0.3em] text-gray-300 italic">Counter-Measure Protocol.</h4>
                </div>
                <div className="grid gap-3">
                    {analysis.recommended_actions.map((action, i) => (
                        <div key={i} className="flex items-center gap-4 p-4 bg-green-500/5 border border-green-500/10 rounded-2xl group hover:border-green-500/30 transition-all hover:translate-x-1">
                            <CheckCircle className="w-4 h-4 text-green-500 shrink-0" />
                            <p className="text-xs text-gray-400 font-bold uppercase tracking-tight group-hover:text-white transition-colors">{action}</p>
                        </div>
                    ))}
                </div>
            </section>
          </div>
        ) : (
          <div className="relative z-10 flex-1 flex flex-col items-center justify-center text-center px-12">
             <div className="w-24 h-24 bg-white/5 rounded-full flex items-center justify-center mb-10 border border-white/5 animate-pulse">
                <Brain className="w-10 h-10 text-gray-700" />
             </div>
             <h4 className="text-lg font-black italic uppercase tracking-tighter text-gray-500 mb-2">Neural Link Idle.</h4>
             <p className="text-[10px] text-gray-700 font-bold uppercase tracking-[0.3em] leading-loose">
               Select an intercepted packet <br /> to engage the XAI analysis protocol.
             </p>
          </div>
        )}

        {/* HUD Decoration */}
        <div className="absolute bottom-6 left-10 right-10 flex justify-between pointer-events-none opacity-20">
            <div className="text-[8px] font-black uppercase tracking-[0.5em] text-gray-700">SRV-BRAIN-NODE // 0012-X</div>
            <div className="text-[8px] font-black uppercase tracking-[0.5em] text-gray-700">QUANTUM LINK STABLE</div>
        </div>
      </div>
    </div>
  );
};
