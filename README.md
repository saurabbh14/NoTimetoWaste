# No Time to Waste – Smarte Routen für Jenas Müllfahrzeuge

Wie navigiert man ein Müllfahrzeug sicher und effizient durch enge Straßen, Sackgassen und zugeparkte Viertel? Bisher basiert die Routenplanung des Kommunalservice Jena vor allem auf Erfahrungswissen der Fahrer:innen. Dabei existieren bereits wertvolle Geodaten zu Straßenbreiten, Kreuzungen und Verkehrsregeln – sie werden jedoch noch nicht für das Routing miteinander in Verbindung gesetzt.

**Deine Challenge**

Eure Aufgabe ist es, einen Prototypen zu entwickeln, der städtische GIS-Daten mit OpenStreetMap und dem Routingdienst Valhalla verbindet. Ziel ist eine realitätsnahe Navigation speziell für Müllfahrzeuge, die problematische Straßen erkennt und fahrzeugspezifische Anforderungen wie Breite, Länge oder Wendekreis berücksichtigt. Gesucht sind kreative Ansätze für datengetriebene Mobilität und smarte Stadtlogistik!

# No Time to Waste – Smart Routes for Jena’s Garbage Trucks

How do you navigate a garbage truck safely and efficiently through narrow streets, dead-ends, and neighborhoods clogged with parked cars? Until now, route planning at Kommunalservice Jena has relied primarily on drivers’ experience. Yet valuable geodata on street widths, intersections, and traffic rules already exists—it just hasn’t been integrated into the routing process yet.

**Your Challenge**

Your task is to develop a prototype that integrates municipal GIS data with OpenStreetMap and the Valhalla routing service. The goal is to create realistic navigation specifically for garbage trucks that identifies problematic roads and takes vehicle-specific requirements—such as width, length, and turning radius—into account. We’re looking for creative approaches to data-driven mobility and smart urban logistics!

---

## 🚀 MVP Implementation / Getting Started

This repository contains a full MVP backend for routing 10.6m x 2.55m garbage trucks efficiently through Jena, avoiding narrow streets and optimizing pickup sequences (TSP - Traveling Salesperson Problem).

### 1. Prerequisites (WSL)
You need `uv`, `Python 3.10+`, and `Docker` installed.
```bash
cd backend
# Install required dependencies
uv add fastapi uvicorn geopy requests folium polyline geopandas fiona mapclassify
cd ..
```

### 2. Start the Valhalla Routing Server
The Valhalla routing engine (including Jena's graph data) is bundled via Docker.
```bash
# Run this from the root directory to extract the provided Valhalla data
uv run python extract_valhalla.py

# Start the Valhalla Docker container (runs on port 8002)
cd backend/valhalla_data/valhalla
docker-compose -f docker-compose.dev.yml up -d
cd ../../..
```

### 3. Extracting Municipal Street Widths
To prove that we can integrate municipal GIS data, we created an ATKIS parser. It dynamically extracts `.dbf`/shapefiles, finds the `breiteDerFahrBahn` (BRF), and color-codes roads in Jena.
```bash
cd backend
uv run python atkis_parser.py
```
*Output: Open `backend/atkis_widths_map.html` to see roads color-coded by width (Red < 2.55m).*

### 4. Run the Multi-Vehicle Routing API
We built a highly modular FastAPI service that exposes Valhalla's TSP (Traveling Salesperson Problem) optimization. 
* **Multi-Truck Support:** You can send multiple fleets in a single request, and each truck will get its own fully optimized, color-coded route.
* **Smart Caching:** Features a built-in SQLite persistence layer (`routes_cache.db`). If a route was already calculated, it is instantly loaded from the cache to save compute time!
* **Geocoding:** Handles raw address strings natively by automatically converting them into GPS coordinates.

```bash
cd backend
uv run uvicorn api:app --host 0.0.0.0 --port 8000 --reload
```

### 5. Testing the API
Once the API is running, visit **[http://localhost:8000/docs](http://localhost:8000/docs)** to test the `/optimize_route` endpoint using Swagger UI.

**Test Case 1: Multiple Trucks with Custom Addresses**
Assign specific addresses to multiple trucks. The API will geocode them and generate individual optimized loops returning to the depot.
```json
{
  "mode": "custom",
  "trucks": [
    {
      "truck_id": "Truck 1 (Red)",
      "addresses": ["Holzmarkt", "Markt"]
    },
    {
      "truck_id": "Truck 2 (Blue)",
      "addresses": ["Löbdergraben 10", "Teichgasse"]
    },
    {
      "truck_id": "Truck 3 (Green)",
      "addresses": ["Lutherstraße 12", "Westbahnhofstraße"]
    }
  ]
}
```