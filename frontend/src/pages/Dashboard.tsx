import { useState } from "react";
import { Box } from "@mui/material";

import MapView from "../components/MapView";
import ControlPanel from "../components/ControlPanel";
import { optimizeRoute } from "../services/api";

import type { Point } from "../types/point";
import type { Truck } from "../types/truck";

export type TruckState = {
  id: string;
  points: Point[];
  addresses: string[];
};

export default function Dashboard() {
  const [depot, setDepot] = useState<Point | null>(null);
  const [endPoint, setEndPoint] = useState<Point | null>(null);
  const [trucks, setTrucks] = useState<TruckState[]>([{ id: "Truck 1", points: [], addresses: [""] }]);
  const [routes, setRoutes] = useState<any[]>([]);
  const [instructions, setInstructions] = useState<any[][]>([]);

  const handleOptimizeRoute = async (mode: string, numRandomPoints: number) => {
    try {
      const payload: any = {
        mode,
        trucks: trucks.map((t, idx) => ({
          truck_id: t.id,
          coordinates: mode === "custom" ? t.points.filter(p => p != null) : undefined,
          num_points: mode === "random" ? numRandomPoints : undefined
        }))
      };

      if (depot) {
        payload.start_point = { lat: depot.lat, lon: depot.lng, radius: 1000 };
      }
      if (endPoint) {
        payload.end_point = { lat: endPoint.lat, lon: endPoint.lng, radius: 1000 };
      }

      const result = await optimizeRoute(payload);
      
      if (result.truck_routes) {
        // Extract the decoded routes for each truck
        const decodedRoutes = result.truck_routes.map((tr: any) => tr.decoded_route).filter(Boolean);
        setRoutes(decodedRoutes);

        // Extract instructions
        const parsedInstructions = result.truck_routes.map((tr: any) => tr.instructions || []);
        setInstructions(parsedInstructions);

        // Reorder truck stops based on Valhalla's optimized TSP order
        if (mode === "custom") {
          const newTrucks = [...trucks];
          result.truck_routes.forEach((tr: any, idx: number) => {
            const valhallaLocations = tr.valhalla_response?.trip?.locations;
            if (valhallaLocations) {
              const currentTruck = newTrucks[idx];
              
              // Create lists of valid points and addresses that were actually sent to the backend
              const validIndices = currentTruck.points.map((p, i) => p ? i : -1).filter(i => i !== -1);
              const validPoints = validIndices.map(i => currentTruck.points[i]);
              const validAddresses = validIndices.map(i => currentTruck.addresses[i]);
              
              const optimizedPoints: Point[] = [];
              const optimizedAddresses: string[] = [];
              const originalLen = validPoints.length + 2; // +2 for start and end
              
              for (const loc of valhallaLocations) {
                const origIdx = loc.original_index;
                // Check if it's an intermediate collection point
                if (origIdx > 0 && origIdx < originalLen - 1) {
                  const collectionIdx = origIdx - 1;
                  optimizedPoints.push(validPoints[collectionIdx]);
                  optimizedAddresses.push(validAddresses[collectionIdx]);
                }
              }
              
              // Only update if the lengths match to avoid data loss
              if (optimizedPoints.length === validPoints.length) {
                // Keep the exact same array length, filling the valid spots with optimized order
                let optIdx = 0;
                const finalPoints = [...currentTruck.points];
                const finalAddresses = [...currentTruck.addresses];
                
                for (let i = 0; i < finalPoints.length; i++) {
                  if (finalPoints[i]) {
                    finalPoints[i] = optimizedPoints[optIdx];
                    finalAddresses[i] = optimizedAddresses[optIdx];
                    optIdx++;
                  }
                }
                
                newTrucks[idx] = { ...currentTruck, points: finalPoints, addresses: finalAddresses };
              }
            }
          });
          setTrucks(newTrucks);
        }
      }
      
    } catch (error: any) {
      alert("Error optimizing route: " + (error.response?.data?.detail || error.message));
    }
  };

  return (
    <Box sx={{ display: "flex", height: "100vh", overflow: "auto" }}>
      <Box sx={{ width: 400, p: 2, overflowY: "auto", display: 'flex', flexDirection: 'column' }}>
        <ControlPanel
          depot={depot}
          setDepot={setDepot}
          endPoint={endPoint}
          setEndPoint={setEndPoint}
          trucks={trucks}
          setTrucks={setTrucks}
          onOptimizeRoute={handleOptimizeRoute}
          instructions={instructions}
        />
      </Box>

      <Box sx={{ flex: 1 }}>
        <MapView
          depot={depot}
          endPoint={endPoint}
          trucks={trucks}
          routes={routes}
        />
      </Box>
    </Box>
  );
}