import requests
import folium
import polyline
import os
import random

VALHALLA_URL = "http://localhost:8002/optimized_route"

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
    locations = [start_end_point] # First point is start/end
    
    # Jena approximate bounding box
    min_lat, max_lat = 50.9231, 50.9324
    min_lon, max_lon = 11.5746, 11.5945
    
    # Set seed for reproducible results
    random.seed(42)
    
    for _ in range(num_points):
        lat = random.uniform(min_lat, max_lat)
        lon = random.uniform(min_lon, max_lon)
        locations.append({"lat": lat, "lon": lon})
        
    return locations

def create_tsp_comparison_map(output_file="valhalla_tsp_comparison.html"):
    # KSJ Depot or Start point (approximate)
    start_end_point = {"lat": 50.9270, "lon": 11.5830}
    
    # Generate 1 start point + 10 waypoints
    locations = generate_random_locations(start_end_point, num_points=10)
    
    print("Fetching optimized standard car route (TSP)...")
    auto_route = get_optimized_route(locations, costing="auto")
    
    print("Fetching optimized garbage truck route (TSP)...")
    truck_options = {
        "truck": {
            "length": 10.6,
            "width": 2.55,
            "height": 3.55,
            "weight": 26.0
        }
    }
    truck_route = get_optimized_route(locations, costing="truck", costing_options=truck_options)
    
    if not auto_route or not truck_route:
        print("Failed to get routes. Make sure Valhalla is running on http://localhost:8002")
        return

    # Decode polylines
    # For optimized_route, the shape is in trip -> legs -> shape
    auto_coords = []
    for leg in auto_route['trip']['legs']:
        auto_coords.extend(polyline.decode(leg['shape'], 6))
        
    truck_coords = []
    for leg in truck_route['trip']['legs']:
        truck_coords.extend(polyline.decode(leg['shape'], 6))
    
    # Create map
    m = folium.Map(location=[start_end_point["lat"], start_end_point["lon"]], zoom_start=14)
    
    # Add Markers for all points
    folium.Marker(
        [start_end_point["lat"], start_end_point["lon"]], 
        tooltip="Start / End Depot", 
        icon=folium.Icon(color='black', icon='home')
    ).add_to(m)
    
    for idx, loc in enumerate(locations[1:], 1):
        folium.Marker(
            [loc["lat"], loc["lon"]], 
            tooltip=f"Pickup Point {idx}", 
            icon=folium.Icon(color='gray', icon='info-sign')
        ).add_to(m)
    
    # Add standard route (Blue, thinner)
    folium.PolyLine(
        auto_coords, 
        color="blue", 
        weight=3, 
        opacity=0.6,
        tooltip="Standard Car TSP Route"
    ).add_to(m)
    
    # Add truck route (Red, thicker)
    folium.PolyLine(
        truck_coords, 
        color="red", 
        weight=5, 
        opacity=0.8,
        tooltip="Garbage Truck TSP Route"
    ).add_to(m)
    
    map_path = os.path.join(os.path.dirname(__file__), output_file)
    m.save(map_path)
    print(f"\nMap saved to {map_path}")
    print("- Blue line: Standard Car (Optimized Path)")
    print("- Red line: Garbage Truck (Optimized Path avoiding tight turns/narrow streets)")

if __name__ == "__main__":
    create_tsp_comparison_map()
