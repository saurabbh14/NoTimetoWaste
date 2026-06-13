import json
import os
import sqlite3
from datetime import datetime, timezone
from math import atan2, cos, radians, sin, sqrt

import pandas as pd
import requests

# URL to fetch traffic flow data
base_url = "https://api.tomtom.com/traffic/services/4/flowSegmentData/relative0/10/json"
api_key = os.getenv('tomtom_key')

# Local input files
traffic_points_file = 'road_midpoints1.csv'
incidents_file = 'traffic_incidents.csv'

# Outputs
output_file = 'traffic_data.geojson'
database_file = 'traffic.db'
traffic_area_table = 'traffic_area_state'


def haversine_distance(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return 6371.0 * c


def load_csv_data(path):
    if not os.path.exists(path):
        return None
    return pd.read_csv(path)


def initialize_database(path):
    conn = sqlite3.connect(path, timeout=30)
    conn.execute('PRAGMA journal_mode=WAL;')
    conn.execute('PRAGMA busy_timeout = 30000;')

    conn.execute('''
        CREATE TABLE IF NOT EXISTS traffic_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            generated_at TEXT NOT NULL,
            source TEXT NOT NULL,
            incident_source TEXT
        )
    ''')

    conn.execute(f'''
        CREATE TABLE IF NOT EXISTS {traffic_area_table} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_latitude REAL NOT NULL,
            source_longitude REAL NOT NULL,
            current_speed INTEGER NOT NULL,
            free_flow_speed INTEGER NOT NULL,
            traffic_ratio INTEGER NOT NULL,
            is_busy INTEGER NOT NULL DEFAULT 0,
            road_closure INTEGER NOT NULL DEFAULT 0,
            confidence REAL,
            incident_count INTEGER NOT NULL DEFAULT 0,
            incidents_json TEXT,
            flow_segment_source TEXT,
            last_updated TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    return conn


def normalize_column_name(name):
    return str(name).strip().lower()


def find_coordinate_columns(columns):
    lat_col = next((c for c in columns if normalize_column_name(c) in ('latitude', 'lat')), None)
    lon_col = next((c for c in columns if normalize_column_name(c) in ('longitude', 'lon', 'long')), None)
    return lat_col, lon_col


def load_incidents(path):
    df = load_csv_data(path)
    if df is None:
        return []

    lat_col, lon_col = find_coordinate_columns(df.columns)
    if lat_col is None or lon_col is None:
        raise ValueError(f"Incident CSV {path} must contain latitude and longitude columns")

    incidents = []
    for _, row in df.iterrows():
        incidents.append({
            'latitude': float(row[lat_col]),
            'longitude': float(row[lon_col]),
            'data': {k: row[k] for k in df.columns if k not in (lat_col, lon_col)}
        })
    return incidents


def find_nearby_incidents(lat, lon, incidents, max_distance_km=1.0):
    nearby = []
    for incident in incidents:
        distance = haversine_distance(lat, lon, incident['latitude'], incident['longitude'])
        if distance <= max_distance_km:
            nearby.append({
                'distance_km': round(distance, 3),
                **incident['data']
            })
    return nearby


def save_geojson(path, geojson):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(geojson, f, indent=2)


def main():
    if api_key is None:
        raise RuntimeError('Missing tomtom_key environment variable')

    traffic_df = load_csv_data(traffic_points_file)
    if traffic_df is None:
        raise FileNotFoundError(f'Cannot find {traffic_points_file}')

    incidents_data = load_incidents(incidents_file)
    if incidents_data:
        print(f'Loaded {len(incidents_data)} incidents from {incidents_file}')
    else:
        print(f'No incident file found or file is empty: {incidents_file}')

    lat_col, lon_col = find_coordinate_columns(traffic_df.columns)
    if lat_col is None or lon_col is None:
        raise ValueError(f"{traffic_points_file} must contain latitude and longitude columns")

    geojson = {
        'type': 'FeatureCollection',
        'features': [],
        'properties': {
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'source': traffic_points_file,
            'incident_source': incidents_file if incidents_data else None
        }
    }

    conn = initialize_database(database_file)
    with conn:
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO traffic_runs (generated_at, source, incident_source) VALUES (?, ?, ?)',
            (geojson['properties']['generated_at'], traffic_points_file, incidents_file if incidents_data else None)
        )
        run_id = cursor.lastrowid

        for _, row in traffic_df.iterrows():
            lat = float(row[lat_col])
            lon = float(row[lon_col])
            url = f"{base_url}?point={lat},{lon}&unit=MPH&openLr=false&key={api_key}"
            print(f'Fetching traffic data for {lat},{lon}')

            try:
                response = requests.get(url, timeout=30)
                response.raise_for_status()
            except requests.RequestException as exc:
                print(f'Network error for {lat},{lon}: {exc}')
                continue

            traffic_data = response.json()
            if 'flowSegmentData' not in traffic_data:
                print(f'No flowSegmentData for {lat},{lon}')
                continue

            segment = traffic_data['flowSegmentData']
            coords = segment.get('coordinates', {}).get('coordinate', [])
            if not coords:
                print(f'No coordinates in flowSegmentData for {lat},{lon}')
                continue

            line_coordinates = [[c['longitude'], c['latitude']] for c in coords if 'longitude' in c and 'latitude' in c]
            last_updated = datetime.now(timezone.utc).isoformat()
            current_speed = int(segment.get('currentSpeed', 0))
            free_flow_speed = int(segment.get('freeFlowSpeed', 0))
            road_closure = int(segment.get('roadClosure', 0))
            confidence = float(segment.get('confidence', 0.0)) if segment.get('confidence') is not None else None
            traffic_ratio = int(round((current_speed / free_flow_speed) * 100)) if free_flow_speed else 0
            nearby_incidents = find_nearby_incidents(lat, lon, incidents_data)

            feature = {
                'type': 'Feature',
                'geometry': {
                    'type': 'LineString',
                    'coordinates': line_coordinates
                },
                'properties': {
                    'currentSpeed': current_speed,
                    'freeFlowSpeed': free_flow_speed,
                    'confidence': confidence,
                    'roadClosure': road_closure,
                    'last_updated': last_updated,
                    'incident_count': len(nearby_incidents),
                    'run_id': run_id
                }
            }
            geojson['features'].append(feature)

            cursor.execute(f'''
                INSERT INTO {traffic_area_table} (
                    source_latitude,
                    source_longitude,
                    current_speed,
                    free_flow_speed,
                    traffic_ratio,
                    is_busy,
                    road_closure,
                    confidence,
                    incident_count,
                    incidents_json,
                    flow_segment_source,
                    last_updated
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                lat,
                lon,
                current_speed,
                free_flow_speed,
                traffic_ratio,
                1 if traffic_ratio >= 80 else 0,
                road_closure,
                confidence,
                len(nearby_incidents),
                json.dumps(nearby_incidents, ensure_ascii=False),
                'tomtom',
                last_updated
            ))

    save_geojson(output_file, geojson)
    print(f'Saved {len(geojson["features"])} features to {output_file}')


if __name__ == '__main__':
    main()
