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
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-10">
      {/* THREAT DISTRIBUTION */}
      <div className="bg-gray-900/40 p-6 rounded-3xl border border-gray-800 shadow-xl group hover:border-gray-700 transition-all">
        <h3 className="text-xs font-black uppercase tracking-widest text-gray-500 mb-6">Threat Distribution</h3>
        <div className="h-[250px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={data}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={80}
                paddingAngle={5}
                dataKey="value"
                stroke="none"
              >
                {data.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} opacity={0.8} />
                ))}
              </Pie>
              <Tooltip 
                contentStyle={{ backgroundColor: "#000", border: "1px solid #333", borderRadius: "10px", fontSize: "10px", fontWeight: "bold" }}
                itemStyle={{ color: "#fff" }}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>
        <div className="grid grid-cols-2 gap-4 mt-6">
            {data.map((entry, index) => (
                <div key={entry.name} className="flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full" style={{ backgroundColor: COLORS[index % COLORS.length] }}></div>
                    <span className="text-[10px] font-bold text-gray-400 uppercase tracking-widest">{entry.name}: {entry.value}</span>
                </div>
            ))}
        </div>
      </div>

      {/* RISK HISTORY */}
      <div className="bg-gray-900/40 p-6 rounded-3xl border border-gray-800 shadow-xl group hover:border-gray-700 transition-all">
        <h3 className="text-xs font-black uppercase tracking-widest text-gray-500 mb-6">24H Threat Vector Trend</h3>
        <div className="h-[250px] w-full">
           <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={trendData}>
                <defs>
                  <linearGradient id="colorRisk" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#ef4444" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" vertical={false} />
                <XAxis dataKey="time" stroke="#4b5563" fontSize={10} tickLine={false} axisLine={false} />
                <YAxis stroke="#4b5563" fontSize={10} tickLine={false} axisLine={false} />
                <Tooltip 
                   contentStyle={{ backgroundColor: "#000", border: "1px solid #333", borderRadius: "10px", fontSize: "10px", fontWeight: "bold" }}
                   itemStyle={{ color: "#fff" }}
                />
                <Area type="monotone" dataKey="risk" stroke="#ef4444" fillOpacity={1} fill="url(#colorRisk)" strokeWidth={3} />
              </AreaChart>
           </ResponsiveContainer>
        </div>
        <p className="text-[10px] text-gray-600 mt-4 italic">* Simulated trend data based on historical heuristics.</p>
      </div>
    </div>
  );
};
