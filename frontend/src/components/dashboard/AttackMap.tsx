"use client";

import React, { useMemo } from "react";
import {
  ComposableMap,
  Geographies,
  Geography,
  Marker,
  Sphere,
  Graticule,
} from "react-simple-maps";
import { Radio } from "lucide-react";

// World TopoJSON - using 110m resolution for performance
const geoUrl = "https://unpkg.com/world-atlas@2.0.2/countries-110m.json";

interface GeoLocation {
  city: string;
  country: string;
  latitude: number;
  longitude: number;
  country_code: string;
}

interface Alert {
  id: string;
  geo_location: GeoLocation;
  risk: {
      severity: string;
      score: number;
  };
  classification: {
      attack_type: string;
  };
}

interface AttackMapProps {
  alerts: Alert[];
}

const AttackMap: React.FC<AttackMapProps> = ({ alerts }) => {
  // Only show markers for alerts with valid coordinates
  const markers = useMemo(() => {
    return alerts
      .filter((a) => a.geo_location && a.geo_location.latitude !== 0)
      .map((a) => ({
        id: a.id,
        coordinates: [a.geo_location.longitude, a.geo_location.latitude] as [number, number],
        severity: a.risk.severity,
        label: `${a.classification.attack_type} - ${a.geo_location.city}`,
      }));
  }, [alerts]);

  return (
    <div className="glass-card w-full h-[450px] bg-black/40 border-white/5 relative overflow-hidden group">
      {/* Background Decorative Grid */}
      <div className="absolute inset-0 opacity-[0.03] pointer-events-none cyber-grid-small"></div>
      
      <div className="absolute top-8 left-10 z-10 flex items-center gap-4">
        <div className="p-2 bg-cyber-red/10 border border-cyber-red/20 rounded-lg">
            <Radio className="w-4 h-4 text-cyber-red animate-pulse" />
        </div>
        <div>
            <h2 className="text-sm font-black tracking-tighter uppercase italic text-glow-red">GLOBAL THREAT MATRIX.</h2>
            <p className="text-[10px] text-gray-500 font-black uppercase tracking-[0.4em] mt-1">Origin Node Tracking // REAL-TIME</p>
        </div>
      </div>

      <ComposableMap
        projection="geoEqualEarth"
        height={450}
        projectionConfig={{ scale: 180 }}
        style={{ width: "100%", height: "100%" }}
      >
        <Sphere stroke="rgba(255,255,255,0.05)" strokeWidth={0.5} id="sphere" fill="transparent" />
        <Graticule stroke="rgba(255,255,255,0.05)" strokeWidth={0.5} />
        
        <Geographies geography={geoUrl}>
          {({ geographies }: { geographies: any[] }) =>
            geographies.map((geo) => (
              <Geography
                key={geo.rsmKey}
                geography={geo}
                fill="#0a0a0a"
                stroke="rgba(255,255,255,0.05)"
                strokeWidth={0.5}
                style={{
                  default: { outline: "none" },
                  hover: { fill: "rgba(239, 68, 68, 0.05)", stroke: "rgba(239, 68, 68, 0.2)", outline: "none", transition: "all 0.3s" },
                  pressed: { outline: "none" },
                }}
              />
            ))
          }
        </Geographies>

        {markers.map(({ id, coordinates, severity, label }) => (
          <Marker key={id} coordinates={coordinates}>
            {/* Pulsing Ripple Effect */}
            <circle
              r={severity === "critical" ? 10 : 6}
              fill="rgba(239, 68, 68, 0.3)"
              className="animate-ping"
            />
            {/* Solid Center */}
            <circle
              r={severity === "critical" ? 4 : 3}
              fill="#ef4444"
              className={severity === "critical" ? "shadow-[0_0_15px_red]" : ""}
              style={{ filter: severity === "critical" ? "drop-shadow(0 0 8px #ef4444)" : "" }}
            >
                <title>{label}</title>
            </circle>
          </Marker>
        ))}
      </ComposableMap>

      {/* Map Legend */}
      <div className="absolute bottom-8 right-10 flex items-center gap-8 z-10 bg-black/60 backdrop-blur-xl px-6 py-3 rounded-2xl border border-white/5 shadow-2xl">
         <div className="flex items-center gap-3 group">
            <div className="w-2.5 h-2.5 rounded-full bg-cyber-red shadow-[0_0_10px_rgba(239,68,68,0.8)] transition-transform group-hover:scale-125"></div>
            <span className="text-[10px] font-black text-gray-500 uppercase tracking-widest group-hover:text-white transition-colors">Critical</span>
         </div>
         <div className="flex items-center gap-3 group">
            <div className="w-2.5 h-2.5 rounded-full bg-orange-500 transition-transform group-hover:scale-125"></div>
            <span className="text-[10px] font-black text-gray-500 uppercase tracking-widest group-hover:text-white transition-colors">Anomalous</span>
         </div>
         <div className="flex items-center gap-4">
            <div className="w-12 h-1 bg-white/5 rounded-full overflow-hidden border border-white/5">
               <div className="h-full bg-cyber-red animate-pulse w-full shadow-[0_0_10px_red]"></div>
            </div>
            <span className="text-[10px] font-black text-cyber-red uppercase tracking-[0.3em] animate-pulse">Live Link</span>
         </div>
      </div>
    </div>
  );
};

export default AttackMap;
