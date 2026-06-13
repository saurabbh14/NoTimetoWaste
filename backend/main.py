import osmqueries
import json
import map_visual

if __name__ == "__main__":
    # Approximate Bounding Box for Jena Zentrum / Paradies area
    # Coordinates: (South Lat, West Lon, North Lat, East Lon)
    jena_bbox = (50.9231, 11.5746, 50.9324, 11.5945)
    
    # 1. Fetch the data
    osm_data = osmqueries.get_jena_street_data(jena_bbox)
    
    # 2. Analyze the constraints
    analyzed_roads = osmqueries.analyze_truck_constraints(osm_data)
    
    print(f"\nSuccessfully processed {len(analyzed_roads)} road segments.")
    
    # 3. Let's look at a few examples, prioritizing roads that actually have width data
    print("\n--- Sample of Roads with Specific Constraints ---")
    constrained_roads = [r for r in analyzed_roads if r['width'] != 'Not specified' or r['noexit'] == 'yes']
    
    for road in constrained_roads[:5]:  # Print first 5
        print(json.dumps(road, indent=2))
        
    # If OSM is missing width data (which is very common), print some regular streets
    if not constrained_roads:
        print("\nNo specific width/noexit constraints found in this sample. Here are standard roads:")
        for road in analyzed_roads[:3]:
            print(json.dumps(road, indent=2))


    map_visual.create_valhalla_comparison_map()
