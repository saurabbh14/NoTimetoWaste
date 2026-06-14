import requests

VALHALLA_URL = "http://localhost:8002/optimized_route"

payload1 = {
    "locations": [
        {"lat": 50.9270, "lon": 11.5830},
        {"lat": 50.9300, "lon": 11.5800}
    ],
    "costing": "truck",
    "exclude_polygons": [
        [
            {"lat": 50.9280, "lon": 11.5810},
            {"lat": 50.9285, "lon": 11.5815},
            {"lat": 50.9290, "lon": 11.5810},
            {"lat": 50.9280, "lon": 11.5810}
        ]
    ]
}

resp1 = requests.post(VALHALLA_URL, json=payload1)
print(resp1.status_code, resp1.text)
