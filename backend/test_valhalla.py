import requests

VALHALLA_URL = "http://localhost:8002/optimized_route"

payload = {
    "locations": [
        {"lat": 50.9270, "lon": 11.5830},
        {"lat": 50.9300, "lon": 11.5800},
        {"lat": 50.9250, "lon": 11.5700}
    ],
    "costing": "truck"
}

resp = requests.post(VALHALLA_URL, json=payload)
print(resp.status_code)
print(resp.text)
