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
    <div className="relative w-full h-[400px] bg-black/40 rounded-3xl border border-gray-800 shadow-2xl overflow-hidden group">
      {/* Background Grid/Effect */}
      <div className="absolute inset-0 opacity-10 pointer-events-none bg-[radial-gradient(#ef4444_1px,transparent_1px)] [background-size:20px_20px]"></div>
      
      <div className="absolute top-6 left-8 z-10">
        <h2 className="text-lg font-black tracking-tighter uppercase italic flex items-center gap-2">
           <span className="text-red-500 animate-pulse">🌍</span> Global Threat Matrix
        </h2>
        <p className="text-[10px] text-gray-500 font-bold uppercase tracking-widest mt-1">Real-Time Origin Tracking</p>
      </div>

      <ComposableMap
        projection="geoEqualEarth"
        height={400}
        projectionConfig={{ scale: 160 }}
        style={{ width: "100%", height: "100%" }}
      >
        <Sphere stroke="#1f2937" strokeWidth={0.5} id="sphere" fill="transparent" />
        <Graticule stroke="#1f2937" strokeWidth={0.5} />
        
        <Geographies geography={geoUrl}>
          {({ geographies }: { geographies: any[] }) =>
            geographies.map((geo) => (
              <Geography
                key={geo.rsmKey}
                geography={geo}
                fill="#111827"
                stroke="#1f2937"
                strokeWidth={0.5}
                style={{
                  default: { outline: "none" },
                  hover: { fill: "#ef444410", outline: "none", transition: "all 0.3s" },
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
              r={severity === "critical" ? 8 : 5}
              fill="rgba(239, 68, 68, 0.4)"
              className="animate-ping"
            />
            {/* Solid Center */}
            <circle
              r={severity === "critical" ? 3 : 2}
              fill="#ef4444"
              className={severity === "critical" ? "shadow-[0_0_10px_red]" : ""}
            >
                <title>{label}</title>
            </circle>
          </Marker>
        ))}
      </ComposableMap>

      {/* Map Legend */}
      <div className="absolute bottom-6 right-8 flex items-center gap-6 z-10 bg-black/60 backdrop-blur-md p-3 rounded-2xl border border-gray-800">
         <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-red-500 shadow-[0_0_8px_red]"></div>
            <span className="text-[10px] font-black text-gray-400 uppercase tracking-tighter">Critical</span>
         </div>
         <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-orange-500"></div>
            <span className="text-[10px] font-black text-gray-400 uppercase tracking-tighter">Anomalous</span>
         </div>
         <div className="flex items-center gap-2">
            <div className="w-10 h-0.5 bg-gray-800 rounded-full overflow-hidden">
               <div className="h-full bg-red-600 animate-pulse w-full"></div>
            </div>
            <span className="text-[10px] font-black text-red-600 uppercase tracking-widest animate-pulse">Live Link</span>
         </div>
      </div>
    </div>
  );
};

export default AttackMap;
