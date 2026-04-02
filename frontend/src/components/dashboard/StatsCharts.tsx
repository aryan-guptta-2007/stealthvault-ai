"use client";

import React from "react";
import { 
  PieChart, Pie, Cell, ResponsiveContainer, Tooltip, 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, AreaChart, Area 
} from "recharts";

interface StatsChartsProps {
  distribution: Record<string, number>;
}

const COLORS = ["#ef4444", "#3b82f6", "#10b981", "#f59e0b", "#8b5cf6", "#ec4899"];

export const StatsCharts: React.FC<StatsChartsProps> = ({ distribution }) => {
  const data = Object.entries(distribution).map(([name, value]) => ({
    name,
    value,
  }));

  // Mock data for trends (since history isn't in simple stats endpoint yet)
  const trendData = [
    { time: "00:00", threats: 4, risk: 20 },
    { time: "04:00", threats: 10, risk: 45 },
    { time: "08:00", threats: 6, risk: 30 },
    { time: "12:00", threats: 15, risk: 65 },
    { time: "16:00", threats: 25, risk: 85 },
    { time: "20:00", threats: 12, risk: 50 },
    { time: "23:59", threats: 8, risk: 35 },
  ];

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-10 mb-12">
      {/* THREAT DISTRIBUTION */}
      <div className="glass-card p-10 border-white/5 bg-black/40 relative overflow-hidden group">
        <div className="flex items-center justify-between mb-8">
            <h3 className="text-xs font-black uppercase tracking-[0.4em] text-gray-500 italic">Threat Distribution.</h3>
            <div className="w-1.5 h-1.5 bg-cyber-red rounded-full animate-pulse shadow-[0_0_10px_rgba(239,68,68,0.8)]"></div>
        </div>
        <div className="h-[280px] w-full relative">
          {/* Decorative Ring */}
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-48 h-48 border border-white/5 rounded-full pointer-events-none"></div>
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={data}
                cx="50%"
                cy="50%"
                innerRadius={70}
                outerRadius={95}
                paddingAngle={8}
                dataKey="value"
                stroke="none"
              >
                {data.map((entry, index) => (
                  <Cell 
                    key={`cell-${index}`} 
                    fill={COLORS[index % COLORS.length]} 
                    className="hover:opacity-100 transition-opacity cursor-pointer shadow-lg"
                    style={{ filter: `drop-shadow(0 0 10px ${COLORS[index % COLORS.length]}44)` }}
                  />
                ))}
              </Pie>
              <Tooltip 
                contentStyle={{ backgroundColor: "#0a0a0a", border: "1px solid rgba(255,255,255,0.05)", borderRadius: "16px", fontSize: "10px", fontWeight: "900", textTransform: "uppercase", letterSpacing: "0.1em" }}
                itemStyle={{ color: "#fff" }}
                cursor={false}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>
        <div className="grid grid-cols-2 gap-6 mt-10 p-4 bg-white/[0.02] rounded-2xl border border-white/5">
            {data.map((entry, index) => (
                <div key={entry.name} className="flex items-center gap-3 group/item">
                    <div className="w-3 h-3 rounded-full shadow-lg transition-transform group-hover/item:scale-125" style={{ backgroundColor: COLORS[index % COLORS.length], boxShadow: `0 0 15px ${COLORS[index % COLORS.length]}66` }}></div>
                    <span className="text-[10px] font-black text-gray-400 uppercase tracking-widest group-hover/item:text-white transition-colors">{entry.name}: {entry.value}</span>
                </div>
            ))}
        </div>
      </div>

      {/* RISK HISTORY */}
      <div className="glass-card p-10 border-white/5 bg-black/40 relative overflow-hidden group">
        <div className="flex items-center justify-between mb-8">
            <h3 className="text-xs font-black uppercase tracking-[0.4em] text-gray-500 italic">Live Threat Vector Trend.</h3>
            <div className="text-[8px] font-black uppercase tracking-[0.2em] text-cyber-red animate-pulse">24H CYCLE</div>
        </div>
        <div className="h-[280px] w-full">
           <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={trendData}>
                <defs>
                  <linearGradient id="colorRisk" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#ef4444" stopOpacity={0.4}/>
                    <stop offset="95%" stopColor="#ef4444" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.03)" vertical={false} />
                <XAxis dataKey="time" stroke="rgba(255,255,255,0.2)" fontSize={9} tickLine={false} axisLine={false} tick={{ fontWeight: 900 }} dy={10} />
                <YAxis stroke="rgba(255,255,255,0.2)" fontSize={9} tickLine={false} axisLine={false} tick={{ fontWeight: 900 }} dx={-10} />
                <Tooltip 
                   contentStyle={{ backgroundColor: "#0a0a0a", border: "1px solid rgba(255,255,255,0.05)", borderRadius: "16px", fontSize: "10px", fontWeight: "900", textTransform: "uppercase", letterSpacing: "0.1em" }}
                   itemStyle={{ color: "#fff" }}
                />
                <Area 
                    type="monotone" 
                    dataKey="risk" 
                    stroke="#ef4444" 
                    fillOpacity={1} 
                    fill="url(#colorRisk)" 
                    strokeWidth={4} 
                    dot={{ fill: "#ef4444", r: 4, strokeWidth: 0 }}
                    activeDot={{ r: 8, stroke: "#fff", strokeWidth: 2 }}
                />
              </AreaChart>
           </ResponsiveContainer>
        </div>
        <div className="mt-10 pt-6 border-t border-white/5 flex items-center justify-between">
            <p className="text-[10px] text-gray-700 font-black uppercase tracking-widest italic flex items-center gap-2">
                <span className="w-2 h-2 bg-gray-800 rounded-full"></span> Simulation Layer Active
            </p>
            <div className="w-16 h-1 bg-white/5 rounded-full overflow-hidden">
                <div className="h-full bg-cyber-red w-3/4 animate-pulse"></div>
            </div>
        </div>
      </div>
    </div>
  );
};
