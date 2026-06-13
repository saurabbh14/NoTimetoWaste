from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import requests
import folium
import polyline
import os
import random
from geopy.geocoders import Nominatim

app = FastAPI(title="NoTimeToWaste Routing API")

VALHALLA_URL = "http://localhost:8002/optimized_route"
geolocator = Nominatim(user_agent="notimetowaste_hackathon")

class RoutingRequest(BaseModel):
    mode: str  # "random" or "custom"
    num_points: Optional[int] = 10
    addresses: Optional[List[str]] = None
    coordinates: Optional[List[dict]] = None

def get_optimized_route(locations, costing="auto", costing_options=None):
    payload = {
        "locations": locations,
        "costing": costing,
        "units": "kilometers"
    }
    if costing_options:
        payload["costing_options"] = costing_options
        
    try:
        response = requests.post(VALHALLA_URL, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to Valhalla: {e}")
        return None

def generate_random_locations(start_end_point, num_points=10):
    # Add snapping radius to start point to prevent unroutable errors
    start_end_point["radius"] = 1000
    locations = [start_end_point]
    min_lat, max_lat = 50.9231, 50.9324
    min_lon, max_lon = 11.5746, 11.5945
    
    # Use fixed seed so we don't accidentally generate points in the river
    random.seed(42) 
    
    for _ in range(num_points):
        locations.append({
            "lat": random.uniform(min_lat, max_lat),
            "lon": random.uniform(min_lon, max_lon),
            "radius": 1000  # 1km snapping radius to find nearest road
        })
    return locations

def geocode_addresses(addresses: List[str]):
    locations = []
    for address in addresses:
        # Append Jena to make the search more robust
        search_query = f"{address}, Jena, Germany"
        location = geolocator.geocode(search_query)
        if location:
            locations.append({
                "lat": location.latitude, 
                "lon": location.longitude,
                "radius": 1000
            })
        else:
            print(f"Warning: Could not geocode address: {address}")
    return locations

@app.post("/optimize_route")
def optimize_route(req: RoutingRequest):
    start_end_point = {"lat": 50.9270, "lon": 11.5830} # KSJ Depot
    locations = []
    
    if req.mode == "random":
        locations = generate_random_locations(start_end_point, req.num_points)
    elif req.mode == "custom":
        locations.append(start_end_point)
        if req.addresses:
            locations.extend(geocode_addresses(req.addresses))
        elif req.coordinates:
            locations.extend(req.coordinates)
        else:
            raise HTTPException(status_code=400, detail="Custom mode requires addresses or coordinates")
    else:
        raise HTTPException(status_code=400, detail="Mode must be 'random' or 'custom'")
        
    # Append the start point to the end to force a round trip!
    if req.mode == "custom" and len(locations) > 1:
        locations.append(start_end_point)
    elif req.mode == "random" and locations[-1] != start_end_point:
        locations.append(start_end_point)
        
    if len(locations) < 2:
        raise HTTPException(status_code=400, detail="Not enough valid locations to route")

    # Fetch Truck TSP Route
    truck_options = {
        "truck": {
            "length": 10.6,
            "width": 2.55,
            "height": 3.55,
            "weight": 26.0
        }
    }
    truck_route = get_optimized_route(locations, costing="truck", costing_options=truck_options)
    
    if not truck_route:
        raise HTTPException(status_code=500, detail="Failed to connect to Valhalla")

    # Decode path for visualization (if needed)
    coords = []
    for leg in truck_route['trip']['legs']:
        coords.extend(polyline.decode(leg['shape'], 6))
        
    # Generate map
    m = folium.Map(location=[start_end_point["lat"], start_end_point["lon"]], zoom_start=14)
    
    # Extract the optimized order of locations from Valhalla
    # Valhalla returns the locations in the exact order they should be visited
    optimized_locations = truck_route['trip']['locations']
    
    # Add Markers in order
    for idx, loc in enumerate(optimized_locations):
        is_depot = (idx == 0 or idx == len(optimized_locations) - 1)
        
        marker_color = 'black' if is_depot else 'blue'
        marker_icon = 'home' if is_depot else 'info-sign'
        label = "Start Depot" if idx == 0 else ("End Depot" if is_depot else f"Stop {idx}")
        
        folium.Marker(
            [loc["lat"], loc["lon"]], 
            tooltip=f"{label} (Original Input #{loc.get('original_index', '?')})", 
            icon=folium.Icon(color=marker_color, icon=marker_icon),
            popup=f"<b>{label}</b>"
        ).add_to(m)
        
        # Add a text label showing the stop number directly on the map
        if not is_depot:
            folium.map.Marker(
                [loc["lat"], loc["lon"]],
                icon=folium.DivIcon(
                    icon_size=(150,36),
                    icon_anchor=(0,0),
                    html=f'<div style="font-size: 14pt; font-weight: bold; color: red;">{idx}</div>'
                )
            ).add_to(m)
        
    # Add route polyline
    # Use AntPath to show direction of travel (animated arrows)
    from folium import plugins
    plugins.AntPath(
        locations=coords,
        color="red",
        weight=5,
        opacity=0.8,
        delay=800,
        dash_array=[15, 30],
        tooltip="Optimized Garbage Truck TSP Route (Follow the arrows)"
    ).add_to(m)
    
    map_path = os.path.join(os.path.dirname(__file__), "api_tsp_map.html")
    m.save(map_path)
        
    return {
        "status": "success",
        "num_locations_routed": len(locations),
        "locations_used": locations,
        "map_generated_at": map_path,
        "valhalla_response": truck_route
    }
