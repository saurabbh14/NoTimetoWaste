import requests

VALHALLA_URL = "http://localhost:8002/optimized_route"

payload = {
    "locations": [
        {"lat": 50.9270, "lon": 11.5830},
        {"lat": 50.9300, "lon": 11.5800}
    ],
    "costing": "truck",
    "exclude_polygons": [
        [
            [11.5810, 50.9280],
            [11.5815, 50.9285],
            [11.5810, 50.9290]
        ]
    ]
}

resp = requests.post(VALHALLA_URL, json=payload)
print(resp.status_code)
print(resp.text)
