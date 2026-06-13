import requests

# The standard public endpoint for Overpass API
OVERPASS_URL = "https://overpass-api.de/api/interpreter"

def get_jena_street_data(bbox):
    """
    Queries OpenStreetMap via Overpass API for road infrastructure in a bounding box.
    bbox format: (south, west, north, east)
    """
    print(f"Fetching road data for bounding box: {bbox}...")
    
    # Overpass QL (Query Language)
    # 1. We look for 'way's that have a 'highway' tag (which means they are roads/paths).
    # 2. We exclude footways and cycleways to keep the data relevant to trucks.
    # 3. out geom; returns the latitude/longitude points of the road shapes.
    overpass_query = f"""
    [out:json][timeout:25];
    (
      way["highway"]["highway"!~"footway|cycleway|pedestrian|steps|path"]
      ({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]});
    );
    out body geom;
    """
    # Overpass strictly requires a descriptive User-Agent to prevent abuse
    headers = {
        "User-Agent": "JenaGarbageRoutingHackathon/1.0"
    }

    response = requests.post(OVERPASS_URL, data={'data': overpass_query}, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Overpass API failed with status code {response.status_code}")

def analyze_truck_constraints(osm_data):
    """
    Extracts and analyzes tags relevant to garbage truck routing.
    """
    roads = []
    
    # Iterate through all the map features (elements) returned
    for element in osm_data.get('elements', []):
        if element['type'] == 'way':
            tags = element.get('tags', {})
            
            # Extract standard routing tags
            road_info = {
                'osm_id': element['id'],
                'name': tags.get('name', 'Unnamed Street'),
                'type': tags.get('highway', 'Unknown'),
                'oneway': tags.get('oneway', 'no'),
                # Truck-specific constraints
                'width': tags.get('width', 'Not specified'),
                'maxweight': tags.get('maxweight', 'Not specified'),
                'noexit': tags.get('noexit', 'no'),
                'parking': tags.get('parking:lane:both', 'Not specified') 
            }
            roads.append(road_info)
            
    return roads