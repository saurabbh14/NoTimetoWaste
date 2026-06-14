# No Time to Waste – Smarte Routen für Jenas Müllfahrzeuge

Wie navigiert man ein Müllfahrzeug sicher und effizient durch enge Straßen, Sackgassen und zugeparkte Viertel? Bisher basiert die Routenplanung des Kommunalservice Jena vor allem auf Erfahrungswissen der Fahrer:innen. Dabei existieren bereits wertvolle Geodaten zu Straßenbreiten, Kreuzungen und Verkehrsregeln – sie werden jedoch noch nicht für das Routing miteinander in Verbindung gesetzt.

**Deine Challenge**

Eure Aufgabe ist es, einen Prototypen zu entwickeln, der städtische GIS-Daten mit OpenStreetMap und dem Routingdienst Valhalla verbindet. Ziel ist eine realitätsnahe Navigation speziell für Müllfahrzeuge, die problematische Straßen erkennt und fahrzeugspezifische Anforderungen wie Breite, Länge oder Wendekreis berücksichtigt. Gesucht sind kreative Ansätze für datengetriebene Mobilität und smarte Stadtlogistik!

# No Time to Waste – Smart Routes for Jena’s Garbage Trucks

How do you navigate a garbage truck safely and efficiently through narrow streets, dead-ends, and neighborhoods clogged with parked cars? Until now, route planning at Kommunalservice Jena has relied primarily on drivers’ experience. Yet valuable geodata on street widths, intersections, and traffic rules already exists—it just hasn’t been integrated into the routing process yet.

**Your Challenge**

Your task is to develop a prototype that integrates municipal GIS data with OpenStreetMap and the Valhalla routing service. The goal is to create realistic navigation specifically for garbage trucks that identifies problematic roads and takes vehicle-specific requirements—such as width, length, and turning radius—into account. We’re looking for creative approaches to data-driven mobility and smart urban logistics!

---

## 🌟 Key Features & Problem Solving Methods

This repository contains a full MVP application (Backend + Interactive Frontend) for routing 10.6m x 2.55m garbage trucks efficiently through Jena, avoiding narrow streets and optimizing pickup sequences (TSP - Traveling Salesperson Problem).

* **Multi-Fleet Optimization:** You can assign multiple trucks simultaneously. The frontend assigns distinct color-coded markers and animated route vectors for each fleet.
* **Smart U-Turn Avoidance:** Garbage trucks cannot easily U-turn in the middle of standard streets. We explicitly customized Valhalla's `truck` costing options with heavy `turn_penalty` and `maneuver_penalty` values. This strictly forces the routing algorithm to drive *through* locations sequentially—only allowing U-turns when safely trapped inside a necessary dead-end street.
* **Turn-by-turn Navigation:** The backend cleanly extracts exact driving `maneuvers` from the Valhalla graph. These are displayed in the frontend dashboard, providing drivers with step-by-step instructions, distances, and travel times.
* **Live Address Autocomplete:** The frontend uses OpenStreetMap's Nominatim API to provide live, debounced search recommendations directly restricted to Jena, instantly plotting valid GPS coordinates to the map upon selection.
* **Dynamic Route Reordering:** Once Valhalla calculates the optimal mathematically shortest path, the frontend automatically re-orders the user's input fields and map markers to strictly reflect the true driving sequence.
* **Native Map Rendering:** Bypassing static HTML generation, the backend decodes Valhalla's encrypted polylines using precision 6 mathematics and passes raw GPS arrays to the frontend. The `react-leaflet` map renders these paths dynamically with CSS-animated arrows indicating driving direction.
* **Smart Caching:** Features a built-in SQLite persistence layer (`routes_cache.db`). If an identical route was already calculated, it is instantly loaded from the cache to save heavy compute time.

---

## 🚀 Getting Started

### 1. Prerequisites (WSL & Windows)
You need `uv` (for Python), `Python 3.10+`, `Docker`, and `Node.js / npm` installed.
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

### 4. Run the Multi-Vehicle Routing API (Backend)
Start the highly modular FastAPI service that exposes the Valhalla endpoints.
```bash
cd backend
uv run uvicorn api:app --host 0.0.0.0 --port 8000 --reload
```

### 5. Start the Interactive Frontend Dashboard
Open a new terminal to start the React UI.
```bash
cd frontend
npm install
npm run dev
```
Open your browser to `http://localhost:5173`. 
**Using the Dashboard:**
1. Select a Start Point (it automatically becomes the End Point unless you toggle the "Different end point" switch).
2. Click `+ Add Truck` to create independent fleets. Use the dropdown to switch between them.
3. Start typing in the "Stops" inputs to see live autocomplete suggestions in Jena.
4. Click `Optimize Route`. The system will snap the stops into the correct TSP order and plot the animated directions!

### 6. Testing the Backend API (Raw JSON)
If you prefer to bypass the frontend, visit **[http://localhost:8000/docs](http://localhost:8000/docs)** to test the `/optimize_route` endpoint using Swagger UI.

**Test Case: Multiple Trucks with Custom Addresses**
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

---

## 🔮 Outlook & Future Integration: Live Traffic Data

As a future enhancement, the project includes a `Live_update` directory dedicated to monitoring real-time traffic updates and road closures. Currently, the foundation is laid out, but this live database is not yet fully integrated into the main routing backend. 

The goal is to seamlessly inject these live road closures directly into the Valhalla routing engine (via `exclude_locations` or dynamic cost adjustments) so that garbage trucks are instantly re-routed around sudden accidents or heavy congestion.

### Setting up the Live Update Database
Developers looking to contribute or test the live traffic integration can set up the monitoring system locally.

1. **Obtain an API Key**: The system uses the TomTom API. You must obtain a key and set it as an environment variable:
   - Linux/macOS: `export tomtom_key="YOUR_API_KEY"`
   - Windows (Command Prompt): `set tomtom_key="YOUR_API_KEY"`
   - Windows (PowerShell): `$env:tomtom_key="YOUR_API_KEY"`

2. **Install Dependencies**:
   Navigate to the directory. To maintain a unified development environment, we recommend using `uv`, though standard `pip` works perfectly as a fallback:
   ```bash
   cd Live_update
   
   # Recommended (using uv)
   uv venv
   uv pip install -r requirements.txt
   
   # Fallback (using standard pip)
   pip install -r requirements.txt
   ```

3. **Run the Fetch & Conversion Script**:
   This script reads coordinates from `road_midpoints1.csv`, queries the TomTom API, and generates the `traffic_data.geojson` database:
   ```bash
   # If using uv:
   uv run python convert_to_geojson.py
   
   # If using standard python:
   python convert_to_geojson.py
   ```

4. **Run the Stale Data Checker**:
   To ensure trucks don't route around stale (old) traffic data, this script checks if the GeoJSON file is older than 20 minutes and wipes it clean if it is outdated:
   ```bash
   # If using uv:
   uv run python check_geojson_update.py
   
   # If using standard python:
   python check_geojson_update.py
   ```
*(Note: There are also GitHub Actions workflows included in the `.github` directory designed to automate this checking and updating process on a schedule.)*
