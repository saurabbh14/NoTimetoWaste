import os
import polyline
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional

from database import init_db, get_route_hash, get_cached_route, save_route_to_cache
from services import generate_random_locations, geocode_addresses, get_optimized_route
from mapping import generate_route_map

app = FastAPI(title="NoTimeToWaste Routing API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Run DB init on startup
init_db()

class TruckConfig(BaseModel):
    truck_id: str
    addresses: Optional[List[str]] = None
    coordinates: Optional[List[dict]] = None
    num_points: Optional[int] = None # for random mode per truck

class RoutingRequest(BaseModel):
    mode: str  # "random" or "custom"
    trucks: List[TruckConfig]
    start_point: Optional[dict] = None
    end_point: Optional[dict] = None

@app.post("/optimize_route")
def optimize_route(req: RoutingRequest):
    default_point = {"lat": 50.9270, "lon": 11.5830, "radius": 1000} # KSJ Depot
    start_point = req.start_point if req.start_point else default_point
    end_point = req.end_point if req.end_point else start_point
    
    all_truck_results = []
    
    # Process each truck
    for truck in req.trucks:
        locations = []
        if req.mode == "random":
            pts = truck.num_points if truck.num_points else 5
            locations = generate_random_locations(start_point, pts)
        elif req.mode == "custom":
            locations.append(start_point)
            if truck.addresses:
                locations.extend(geocode_addresses(truck.addresses))
            elif truck.coordinates:
                # The frontend sends standard {lat, lng} points, Valhalla expects {lat, lon}
                formatted_coords = []
                for c in truck.coordinates:
                    if "lng" in c:
                        formatted_coords.append({"lat": c["lat"], "lon": c["lng"], "radius": 1000})
                    else:
                        formatted_coords.append({"lat": c["lat"], "lon": c.get("lon", 0), "radius": 1000})
                locations.extend(formatted_coords)
            else:
                raise HTTPException(status_code=400, detail=f"Custom mode requires addresses or coordinates for {truck.truck_id}")
        else:
            raise HTTPException(status_code=400, detail="Mode must be 'random' or 'custom'")
            
        # Append the end point to the end to force a round trip
        if req.mode == "custom" and len(locations) > 1 and locations[-1] != end_point:
            locations.append(end_point)
        elif req.mode == "random" and locations[-1] != end_point:
            locations.append(end_point)
            
        if len(locations) < 2:
            continue

        # Check Cache
        route_hash = get_route_hash(locations)
        truck_route = get_cached_route(route_hash)
        is_cached = True
        
        if truck_route:
            print(f"Returning route for {truck.truck_id} from SQLite Cache!")
        else:
            print(f"Route for {truck.truck_id} not found in cache. Querying Valhalla...")
            is_cached = False
            truck_options = {
                "truck": {
                    "length": 10.6,
                    "width": 2.55,
                    "height": 3.55,
                    "weight": 26.0,
                    "maneuver_penalty": 100, # Higher penalty for complex maneuvers
                    "turn_penalty": 100      # Higher penalty for turning around
                }
            }
            truck_route = get_optimized_route(locations, costing="truck", costing_options=truck_options)
            
            if not truck_route:
                raise HTTPException(status_code=500, detail=f"Failed to connect to Valhalla for {truck.truck_id}")
                
            save_route_to_cache(route_hash, truck_route)
            
        decoded_route = []
        instructions = []
        if truck_route and "trip" in truck_route and "legs" in truck_route["trip"]:
            for leg in truck_route["trip"]["legs"]:
                if "shape" in leg:
                    # Valhalla uses precision 6
                    decoded_route.extend(polyline.decode(leg["shape"], 6))
                if "maneuvers" in leg:
                    for maneuver in leg["maneuvers"]:
                        if "instruction" in maneuver:
                            instructions.append({
                                "instruction": maneuver["instruction"],
                                "length": maneuver.get("length", 0),
                                "time": maneuver.get("time", 0)
                            })
            
        all_truck_results.append({
            "truck_id": truck.truck_id,
            "locations_used": locations,
            "valhalla_response": truck_route,
            "decoded_route": decoded_route,
            "instructions": instructions,
            "cached": is_cached
        })

    if not all_truck_results:
        raise HTTPException(status_code=400, detail="No valid routes could be generated")

    # Generate Map with all trucks
    map_path = generate_route_map(all_truck_results, start_point)
        
    return {
        "status": "success",
        "num_trucks_routed": len(all_truck_results),
        "truck_routes": all_truck_results,
        "map_generated_at": map_path
    }

@app.get("/{filename:path}")
def serve_html(filename: str):
    file_path = os.path.join(os.path.dirname(__file__), filename)
    if os.path.exists(file_path) and filename.endswith(".html"):
        return FileResponse(file_path)
    raise HTTPException(status_code=404, detail="File not found")
