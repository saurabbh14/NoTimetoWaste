import requests
import random

VALHALLA_URL = "http://localhost:8002/optimized_route"

start_end_point = {"lat": 50.9270, "lon": 11.5830}
locations = [start_end_point]
min_lat, max_lat = 50.9231, 50.9324
min_lon, max_lon = 11.5746, 11.5945
random.seed(42)
for _ in range(5):
    locations.append({
        "lat": random.uniform(min_lat, max_lat),
        "lon": random.uniform(min_lon, max_lon)
    })

payload = {
    "locations": locations,
    "costing": "truck"
}

resp = requests.post(VALHALLA_URL, json=payload)
print(resp.status_code)
print(resp.text)
