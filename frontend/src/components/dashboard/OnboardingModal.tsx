"use client";

import React, { useState, useEffect } from "react";
import { X, Shield, Activity, Zap, Play, ChevronRight, Brain, Target, Radio } from "lucide-react";

interface OnboardingModalProps {
  onCloseAction: () => void;
}

export const OnboardingModal: React.FC<OnboardingModalProps> = ({ onCloseAction }) => {
  const [step, setStep] = useState(1);
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => setIsVisible(true), 500);
    return () => clearTimeout(timer);
  }, []);

  const totalSteps = 3;

  const nextStep = () => {
    if (step < totalSteps) {
      setStep(step + 1);
    } else {
      handleClose();
    }
  };

  const handleClose = () => {
    setIsVisible(false);
    setTimeout(onCloseAction, 500);
  };

  if (!isVisible && step === 1) return null;

  return (
    <div className={`fixed inset-0 z-[200] flex items-center justify-center p-6 transition-all duration-700 ${isVisible ? 'opacity-100 backdrop-blur-2xl bg-black/80' : 'opacity-0 backdrop-blur-0 bg-transparent pointer-events-none'}`}>
      <div className={`w-full max-w-2xl glass-card overflow-hidden transition-all duration-700 transform ${isVisible ? 'scale-100 translate-y-0' : 'scale-95 translate-y-8'}`}>
        {/* Header Decor */}
        <div className="absolute top-0 left-0 w-full h-[2px] bg-gradient-to-r from-transparent via-cyber-red to-transparent opacity-50"></div>
        
        <div className="p-12 relative">
            <button 
                onClick={handleClose}
                className="absolute top-8 right-8 p-3 hover:bg-white/5 rounded-full transition-all group"
            >
                <X className="w-5 h-5 text-gray-500 group-hover:text-white group-hover:rotate-90 transition-all duration-300" />
            </button>

            <div className="space-y-12">
                {/* ICON & TITLE */}
                <div className="flex flex-col items-center text-center space-y-6">
                    <div className="p-5 bg-cyber-red/10 border border-cyber-red/30 rounded-[2rem] shadow-[0_0_30px_rgba(239,68,68,0.2)] animate-pulse">
                        <Shield className="w-12 h-12 text-cyber-red" />
                    </div>
                    <div>
                        <h2 className="text-3xl font-black italic tracking-tighter uppercase text-white leading-none">
                            Welcome to the <span className="text-cyber-red">War Room.</span>
                        </h2>
                        <p className="text-[10px] text-gray-500 font-black uppercase tracking-[0.5em] mt-4">StealthVault AI // Onboarding Alpha-1</p>
                    </div>
                </div>

                {/* CONTENT AREA */}
                <div className="min-h-[200px] flex flex-col items-center justify-center text-center px-10">
                    {step === 1 && (
                        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-700">
                            <h3 className="text-lg font-black uppercase tracking-widest text-gray-300 italic">Phase 1: Real-Time Detection</h3>
                            <p className="text-sm text-gray-400 leading-relaxed max-w-md mx-auto">
                                StealthVault analyzes every packet in your network using quantum-inspired AI. When a threat is detected, it is instantly quarantined and analyzed for intent.
                            </p>
                            <div className="flex justify-center gap-4 text-cyber-red">
                                <Activity className="w-5 h-5 animate-pulse" />
                                <div className="w-[1px] h-5 bg-white/10"></div>
                                <Zap className="w-5 h-5 animate-pulse [animation-delay:0.2s]" />
                                <div className="w-[1px] h-5 bg-white/10"></div>
                                <Radio className="w-5 h-5 animate-pulse [animation-delay:0.4s]" />
                            </div>
                        </div>
                    )}

                    {step === 2 && (
                        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-700">
                            <h3 className="text-lg font-black uppercase tracking-widest text-gray-300 italic">Phase 2: The Attack Story</h3>
                            <p className="text-sm text-gray-400 leading-relaxed max-w-md mx-auto">
                                Don't just see alerts. Our **Neural Analysis** engine reconstructs the attacker's story, predicting their next move before it happens.
                            </p>
                            <div className="flex gap-2 justify-center py-2">
                                <div className="px-3 py-1 bg-white/5 border border-white/10 rounded-lg text-[10px] font-black uppercase tracking-tighter text-gray-500">Recon</div>
                                <ChevronRight className="w-4 h-4 text-gray-700" />
                                <div className="px-3 py-1 bg-cyber-red/10 border border-cyber-red/30 rounded-lg text-[10px] font-black uppercase tracking-tighter text-cyber-red">Exploitation</div>
                                <ChevronRight className="w-4 h-4 text-gray-700" />
                                <div className="px-3 py-1 bg-white/5 border border-white/10 rounded-lg text-[10px] font-black uppercase tracking-tighter text-gray-400 opacity-30 italic">Exfiltration (Predicted)</div>
                            </div>
                        </div>
                    )}

                    {step === 3 && (
                        <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
                            <h3 className="text-lg font-black uppercase tracking-widest text-gray-300 italic">Phase 3: Tactical Advantage</h3>
                            <p className="text-sm text-gray-400 leading-relaxed max-w-md mx-auto">
                                Start by launching a **Live Simulation** to see StealthVault in action. Monitor the Global Radar and engage the Neural Link for deep forensics.
                            </p>
                            <div className="flex justify-center gap-6">
                                <div className="flex flex-col items-center gap-2 group">
                                    <div className="w-12 h-12 bg-white/5 border border-white/10 rounded-2xl flex items-center justify-center group-hover:border-cyber-red transition-all">
                                        <Play className="w-6 h-6 text-cyber-red" />
                                    </div>
                                    <span className="text-[8px] font-black uppercase text-gray-600">Simulate</span>
                                </div>
                                <div className="flex flex-col items-center gap-2 group">
                                    <div className="w-12 h-12 bg-white/5 border border-white/10 rounded-2xl flex items-center justify-center group-hover:border-cyber-blue transition-all">
                                        <Brain className="w-6 h-6 text-cyber-blue" />
                                    </div>
                                    <span className="text-[8px] font-black uppercase text-gray-600">Analyze</span>
                                </div>
                                <div className="flex flex-col items-center gap-2 group">
                                    <div className="w-12 h-12 bg-white/5 border border-white/10 rounded-2xl flex items-center justify-center group-hover:border-white transition-all">
                                        <Target className="w-6 h-6 text-white" />
                                    </div>
                                    <span className="text-[8px] font-black uppercase text-gray-600">Intercept</span>
                                </div>
                            </div>
                        </div>
                    )}
                </div>

                {/* NAVIGATION */}
                <div className="flex flex-col items-center space-y-6">
                    <button 
                        onClick={nextStep}
                        className="group relative px-12 py-5 bg-cyber-red text-white overflow-hidden transition-all hover:scale-105 active:scale-95"
                    >
                        <div className="absolute inset-0 bg-white/10 translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-1000"></div>
                        <span className="relative z-10 text-[10px] font-black uppercase tracking-[0.3em] flex items-center gap-4">
                            {step === totalSteps ? 'Enter War Room' : 'Next Protocol'} 
                            <ChevronRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                        </span>
                    </button>

                    {/* Step Indicators */}
                    <div className="flex gap-3">
                        {[1, 2, 3].map((s) => (
                            <div 
                                key={s} 
                                className={`h-1 transition-all duration-500 rounded-full ${s === step ? 'w-10 bg-cyber-red' : 'w-4 bg-white/10'}`}
                            ></div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
      </div>
    </div>
  );
};
