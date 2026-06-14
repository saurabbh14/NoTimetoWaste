import { useEffect, useRef } from "react";
import {
  MapContainer,
  TileLayer,
  Marker,
  Polyline,
} from "react-leaflet";
import "leaflet/dist/leaflet.css";
import L from "leaflet";

// Animated Polyline Component
function AnimatedPolyline({ positions, color }: { positions: any[], color: string }) {
  const polylineRef = useRef<any>(null);

  useEffect(() => {
    let animationFrameId: number;
    let offset = 45;

    const animate = () => {
      offset -= 1; // Speed of animation
      if (offset <= 0) offset = 45;

      const element = polylineRef.current?.getElement();
      if (element) {
        element.style.strokeDasharray = "15, 30";
        element.style.strokeDashoffset = offset.toString();
      }

      animationFrameId = requestAnimationFrame(animate);
    };

    if (polylineRef.current) {
      animate();
    }

    return () => {
      cancelAnimationFrame(animationFrameId);
    };
  }, []);

  return (
    <>
      <Polyline positions={positions} pathOptions={{ color: color, weight: 6, opacity: 0.5 }} />
      <Polyline ref={polylineRef} positions={positions} pathOptions={{ color: "#000", weight: 3, opacity: 0.8 }} />
    </>
  );
}

// Custom Home (Start) Marker replicating black Folium Home Marker
const startIcon = L.divIcon({
  html: `
    <div style="position: relative; width: 30px; height: 40px;">
      <svg viewBox="0 0 384 512" width="30" height="40" style="filter: drop-shadow(0px 4px 4px rgba(0,0,0,0.5));">
        <path fill="#212121" d="M384 192c0 87.4-117 243-168.3 307.2c-12.3 15.3-35.1 15.3-47.4 0C117 435 0 279.4 0 192C0 86 86 0 192 0S384 86 384 192z"/>
        <path fill="#ffffff" d="M192 64l-80 72v88h48v-64h64v64h48v-88l-80-72zm-32 112v32h64v-32h-64z"/>
      </svg>
    </div>
  `,
  className: "",
  iconSize: [30, 40],
  iconAnchor: [15, 40],
});

// Custom End Marker (Red)
const endIcon = L.divIcon({
  html: `<div style="background-color: #F44336; color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; border: 2px solid white; box-shadow: 0 2px 4px rgba(0,0,0,0.4);">🏁</div>`,
  className: "",
  iconSize: [24, 24],
  iconAnchor: [12, 12],
});

const ROUTE_COLORS = ["#2196F3", "#F44336", "#4CAF50", "#9C27B0", "#FF9800", "#795548", "#607D8B"];

// Helper for numbered collection markers
const createNumberedIcon = (number: number, color: string) => {
  return L.divIcon({
    html: `<div style="background-color: ${color}; color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; border: 2px solid white; box-shadow: 0 2px 4px rgba(0,0,0,0.4); font-weight: bold; font-size: 12px;">${number}</div>`,
    className: "",
    iconSize: [24, 24],
    iconAnchor: [12, 12],
  });
};

export default function MapView({
  depot,
  endPoint,
  trucks = [],
  routes = [],
}: {
  depot?: any,
  endPoint?: any,
  trucks?: any[],
  routes?: any[][]
}) {
  const center = [50.9271, 11.5892];

  return (
    <MapContainer
      center={center}
      zoom={13}
      style={{ height: "100vh", width: "100%" }}
    >
      <TileLayer url="https://tile.openstreetmap.org/{z}/{x}/{y}.png" />

      {/* START POINT */}
      {depot && (
        <Marker position={[depot.lat, depot.lng]} icon={startIcon} />
      )}

      {/* END POINT */}
      {endPoint && (
        <Marker position={[endPoint.lat, endPoint.lng]} icon={endIcon} />
      )}

      {/* POINTS */}
      {trucks.map((truck, tIdx) => {
        const color = ROUTE_COLORS[tIdx % ROUTE_COLORS.length];
        return truck.points?.map((p: any, i: number) => {
          if (!p) return null;
          return (
            <Marker
              key={`truck-${tIdx}-point-${i}`}
              position={[p.lat, p.lng]}
              icon={createNumberedIcon(i + 1, color)}
            />
          );
        });
      })}

      {/* ROUTES */}
      {routes.map((routeLine, idx) => {
        const color = ROUTE_COLORS[idx % ROUTE_COLORS.length];
        return (
          <AnimatedPolyline
            key={`route-${idx}`}
            positions={routeLine}
            color={color}
          />
        );
      })}
    </MapContainer>
  );
}