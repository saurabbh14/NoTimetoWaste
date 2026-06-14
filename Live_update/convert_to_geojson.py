import requests
import json
import os
import pandas as pd
from datetime import datetime
import sqlite3

# URL to fetch traffic flow data
base_url = "https://api.tomtom.com/traffic/services/4/flowSegmentData/relative0/10/json"
api_key = os.getenv('tomtom_key')

# Path to the CSV file in your GitHub repository
#csv_url = "https://raw.githubusercontent.com/MillcreekGIS/traffic/main/road_midpoints1.csv"

# Read the CSV file
df = pd.read_csv('road_midpoints1.csv')

# Initialize GeoJSON structure
geojson = {
    "type": "FeatureCollection",
    "features": []
}

# Set up SQLite database to store same properties
db_path = 'traffic.db'
conn = sqlite3.connect(db_path)
cur = conn.cursor()
# Create table if it doesn't exist
cur.execute('''
CREATE TABLE IF NOT EXISTS traffic_flow (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_latitude REAL,
    source_longitude REAL,
    currentSpeed REAL,
    freeFlowSpeed REAL,
    confidence REAL,
    roadClosure INTEGER,
    flowSegmentSource TEXT,
    last_updated TEXT,
    incident_count INTEGER,
    incidents TEXT,
    raw_response TEXT,
    geometry TEXT
)
''')
conn.commit()

# Loop through each row in the CSV file
for index, row in df.iterrows():
    lat = row['Latitude']
    lon = row['Longitude']
    
    # Build the request URL
    url = f"{base_url}?point={lat},{lon}&unit=MPH&openLr=false&key={api_key}"
    print(f"Request URL: {url}")
    
    # Fetch the traffic data
    response = requests.get(url)
    if response.status_code == 200:
        traffic_data = response.json()
        
        # Print the response to debug
        print(json.dumps(traffic_data, indent=2))
        
        # Ensure the correct path to the data
        if "flowSegmentData" in traffic_data:
            segment = traffic_data["flowSegmentData"]
            coordinates = segment["coordinates"]["coordinate"]
            
            # Create a list of coordinate pairs for the LineString
            line_coordinates = [[coord["longitude"], coord["latitude"]] for coord in coordinates]

            # Get the current timestamp
            last_updated = datetime.utcnow().isoformat() + 'Z'

            # Build properties using the exact schema requested by the user
            properties = {
                "source_latitude": row.get("Latitude"),
                "source_longitude": row.get("Longitude"),
                "currentSpeed": segment.get("currentSpeed"),
                "freeFlowSpeed": segment.get("freeFlowSpeed"),
                "confidence": segment.get("confidence"),
                "roadClosure": segment.get("roadClosure", False),
                "flowSegmentSource": segment.get("flowSegmentSource"),
                "last_updated": last_updated,
                "incident_count": 0,
                "incidents": [],
                "raw_response": None
            }

            # Populate incidents if present; keep raw_response as null by default
            incidents = None
            if isinstance(segment, dict) and "incidents" in segment:
                incidents = segment.get("incidents")
            elif "incidents" in traffic_data:
                incidents = traffic_data.get("incidents")
            elif "alerts" in traffic_data:
                incidents = traffic_data.get("alerts")

            if incidents:
                # normalize to list when possible
                if isinstance(incidents, list):
                    properties["incidents"] = incidents
                    properties["incident_count"] = len(incidents)
                else:
                    properties["incidents"] = [incidents]
                    properties["incident_count"] = 1

            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": line_coordinates
                },
                "properties": properties
            }
            geojson["features"].append(feature)

            # Insert same properties into SQLite DB
            try:
                cur.execute(
                    '''INSERT INTO traffic_flow (
                        source_latitude, source_longitude, currentSpeed,
                        freeFlowSpeed, confidence, roadClosure, flowSegmentSource,
                        last_updated, incident_count, incidents, raw_response, geometry
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                    (
                        properties.get("source_latitude"),
                        properties.get("source_longitude"),
                        properties.get("currentSpeed"),
                        properties.get("freeFlowSpeed"),
                        properties.get("confidence"),
                        int(bool(properties.get("roadClosure"))) if properties.get("roadClosure") is not None else 0,
                        properties.get("flowSegmentSource"),
                        properties.get("last_updated"),
                        properties.get("incident_count"),
                        json.dumps(properties.get("incidents")) if properties.get("incidents") is not None else None,
                        None,
                        json.dumps(feature.get("geometry"))
                    )
                )
                conn.commit()
            except Exception as e:
                print(f"Failed to insert into DB for {lat},{lon}: {e}")
        else:
            print("No flowSegmentData found in the response.")
    else:
        print(f"Failed to fetch data for {lat}, {lon}: {response.status_code}")
        print(f"Response content: {response.content}")

# Save the GeoJSON to a file
with open('traffic_data.geojson', 'w') as f:
    json.dump(geojson, f)

print("GeoJSON file created successfully.")
