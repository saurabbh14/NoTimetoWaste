import requests
import folium
import polyline

# Standard Valhalla local endpoint
VALHALLA_URL = "http://127.0.0.1:8002/route"

def get_valhalla_route(start_coords, end_coords, costing="auto", truck_options=None):
    """
    Sends a routing request to Valhalla.
    coords should be tuples of (lat, lon)
    """
    # Build the Valhalla JSON payload
    payload = {
        "locations": [
            {"lat": start_coords[0], "lon": start_coords[1]},
            {"lat": end_coords[0], "lon": end_coords[1]}
        ],
        "costing": costing,
        "units": "kilometers"
    }
    
    # If we are routing a truck, pass the specific constraints
    if costing == "truck" and truck_options:
        payload["costing_options"] = {
            "truck": truck_options
        }
        
    print(f"Requesting {costing} route from Valhalla...")
    try:
        # Added a 10-second timeout
        response = requests.post(VALHALLA_URL, json=payload, timeout=10)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Valhalla Error ({response.status_code}): {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Failed to connect to Valhalla: {e}")
        return None

def create_valhalla_comparison_map():
    # Example coordinates in Jena (Start: Paradies, End: West)
    start_pt = (50.9255, 11.5872)
    end_pt = (50.9261, 11.5721)
    
    # 1. Get standard car route
    car_route_data = get_valhalla_route(start_pt, end_pt, costing="auto")
    
    # 2. Get Garbage Truck route (Specifying heavy constraints)
    truck_constraints = {
        "width": 3.0,     # meters
        "weight": 18.0,   # tonnes
        "length": 10.0,   # meters
        "use_highways": 0 # Garbage trucks generally avoid Autobahns
    }
    truck_route_data = get_valhalla_route(start_pt, end_pt, costing="truck", truck_options=truck_constraints)
    
    # 3. Setup Folium Map
    m = folium.Map(location=[start_pt[0], start_pt[1]], zoom_start=14, tiles="CartoDB positron")
    
    # Add start and end markers
    folium.Marker(start_pt, tooltip="Start").add_to(m)
    folium.Marker(end_pt, tooltip="End").add_to(m)

    # 4. Decode and draw the Car Route (Blue)
    if car_route_data:
        # Valhalla returns geometry as a 6-decimal precision encoded polyline
        car_shape = car_route_data['trip']['legs'][0]['shape']
        car_coordinates = polyline.decode(car_shape, 6)
        
        folium.PolyLine(
            car_coordinates,
            color="#0066CC", # Blue
            weight=4,
            opacity=0.7,
            tooltip="Standard Auto Route"
        ).add_to(m)

    # 5. Decode and draw the Truck Route (Red)
    if truck_route_data:
        truck_shape = truck_route_data['trip']['legs'][0]['shape']
        truck_coordinates = polyline.decode(truck_shape, 6)
        
        folium.PolyLine(
            truck_coordinates,
            color="#FF0000", # Red
            weight=4,
            opacity=0.7,
            tooltip="Garbage Truck Route (Avoids narrow/weight-limited streets)"
        ).add_to(m)

    output_file = "jena_valhalla_routing.html"
    m.save(output_file)
    print(f"Map saved! Open {output_file} to see how the truck route differs from the car route.")