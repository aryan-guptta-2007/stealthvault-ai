import React, { useState, useEffect, useRef } from "react";
import { Terminal as TerminalIcon } from "lucide-react";

interface LogEntry {
  id: string;
  timestamp: string;
  message: string;
  type: "info" | "warning" | "error" | "success";
}

export const TerminalLogs = ({ logs: initialLogs = [] }: { logs?: LogEntry[] }) => {
  const [logs, setLogs] = useState<LogEntry[]>(initialLogs);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs]);

  // Mock incoming logs if none provided for "alive" feel
  useEffect(() => {
    if (initialLogs.length > 0) {
      setLogs(initialLogs);
      return;
    }

    const mockMessages = [
      { msg: "Neural Engine: Analyzing throughput...", type: "info" },
      { msg: "Gateway: SYN Flood detected from 45.66.12.3", type: "warning" },
      { msg: "Defender: IP 45.66.12.3 quarantined successfully.", type: "success" },
      { msg: "Analyst: XSS Pattern matched in /api/v1/user/profile", type: "error" },
      { msg: "System: Global reputation database updated.", type: "info" },
    ];

    const interval = setInterval(() => {
      const randomMsg = mockMessages[Math.floor(Math.random() * mockMessages.length)];
      const newLog: LogEntry = {
        id: Math.random().toString(36).substr(2, 9),
        timestamp: new Date().toLocaleTimeString(),
        message: randomMsg.msg,
        type: randomMsg.type as any,
      };
      setLogs((prev) => [...prev.slice(-19), newLog]);
    }, 4000);

    return () => clearInterval(interval);
  }, [initialLogs]);

  return (
    <div className="glass-card bg-black/60 border-white/5 overflow-hidden flex flex-col h-[300px]">
      <div className="px-4 py-2 bg-white/5 border-b border-white/5 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <TerminalIcon className="w-3 h-3 text-cyber-red" />
          <span className="text-[10px] font-black uppercase tracking-[0.2em] text-gray-500">System Logs // Raw Feed</span>
        </div>
        <div className="flex gap-1.5">
          <div className="w-1.5 h-1.5 rounded-full bg-red-500/20"></div>
          <div className="w-1.5 h-1.5 rounded-full bg-yellow-500/20"></div>
          <div className="w-1.5 h-1.5 rounded-full bg-green-500/20"></div>
        </div>
      </div>
      <div 
        ref={scrollRef}
        className="flex-1 p-4 font-mono text-[10px] space-y-1 overflow-y-auto custom-scrollbar-thin"
      >
        {logs.map((log) => (
          <div key={log.id} className="flex gap-3 group">
            <span className="text-gray-600 shrink-0">[{log.timestamp}]</span>
            <span className={`
              ${log.type === "info" ? "text-gray-400" : ""}
              ${log.type === "warning" ? "text-yellow-500" : ""}
              ${log.type === "error" ? "text-cyber-red" : ""}
              ${log.type === "success" ? "text-green-500" : ""}
            `}>
              {log.message}
            </span>
          </div>
        ))}
        <div className="flex gap-2 items-center text-cyber-red animate-pulse">
            <span>_</span>
        </div>
      </div>
    </div>
  );
};
