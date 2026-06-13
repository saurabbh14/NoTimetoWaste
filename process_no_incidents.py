import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'traffic.db')


def load_rows():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(
        "SELECT id, source_latitude, source_longitude, currentSpeed, freeFlowSpeed, confidence, roadClosure, flowSegmentSource, last_updated, incident_count, incidents, raw_response FROM traffic_flow WHERE incident_count != 0 AND roadClosure = True AND currentSpeed IS NOT NULL AND currentSpeed > 10.5"
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def print_rows(rows):
    print(f"Found {len(rows)} rows with incident_count != 0 and roadClosure = True")
    print("-")
    for row in rows:
        print(f"id={row['id']}")
        print(f"source_latitude={row['source_latitude']}")
        print(f"source_longitude={row['source_longitude']}")
        print(f"currentSpeed={row['currentSpeed']}")
        print(f"freeFlowSpeed={row['freeFlowSpeed']}")
        print(f"confidence={row['confidence']}")
        print(f"roadClosure={bool(row['roadClosure']) if row['roadClosure'] is not None else False}")
        print(f"flowSegmentSource={row['flowSegmentSource']}")
        print(f"last_updated={row['last_updated']}")
        print(f"incident_count={row['incident_count']}")
        print(f"incidents={row['incidents']}")
        print(f"raw_response={row['raw_response']}")
        print("-")


def main():
    rows = load_rows()
    if not rows:
        print('No rows with incident_count == 0 found in traffic_flow.')
        return
    print_rows(rows)


if __name__ == '__main__':
    main()
