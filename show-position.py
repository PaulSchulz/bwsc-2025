#!/usr/bin/env python3

#!/usr/bin/env python3
import requests
import pandas as pd

URL = "https://telemetry.worldsolarchallenge.org/wscearth/api/positions"

def fetch_positions():
    response = requests.get(URL)
    response.raise_for_status()
    return response.json()

def display_table(data):
    teams = []
    for entry in data["items"]:
        teams.append({
            "Number": entry.get("teamnum"),
            "Name": entry.get("shortname"),
            "Car": entry.get("car"),
            "Distance (km)": round(entry.get("distance", 0), 2),
            "Speed (km/h)": round(entry.get("speed", 0), 2),
            "Avg Speed (km/h)": round(entry.get("avg_speed", 0), 2),
        })

    # Sort by distance to calculate race position
    df = pd.DataFrame(teams)
    df = df.sort_values("Distance (km)", ascending=False).reset_index(drop=True)
    df.insert(0, "Position", df.index + 1)

    print(df.to_string(index=False))

if __name__ == "__main__":
    data = fetch_positions()
    display_table(data)
