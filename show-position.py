#!/usr/bin/env python3
import requests
import pandas as pd
from tabulate import tabulate

URL = "https://telemetry.worldsolarchallenge.org/wscearth/api/positions"

control_points = [
    {"distance": 0.0,    "id": "DAR", "type": "START",   "name": "Darwin"},
    {"distance": 192.5,  "id": "EMS", "type": "CONTROL", "name": "Emerald Springs"},
    {"distance": 321.9,  "id": "KAT", "type": "CONTROL", "name": "Katherine"},
    {"distance": 632.1,  "id": "DUN", "type": "CONTROL", "name": "Dunmarra"},
    {"distance": 986.8,  "id": "TEN", "type": "CONTROL", "name": "Tennant Creek"},
    {"distance": 1209.8, "id": "BAR", "type": "CONTROL", "name": "Barrow Creek"},
    {"distance": 1493.5, "id": "ALI", "type": "CONTROL", "name": "Alice Springs"},
    {"distance": 1691.7, "id": "ERL", "type": "CONTROL", "name": "Erlunda"},
    {"distance": 2178.4, "id": "COO", "type": "CONTROL", "name": "Coober Pedy"},
    {"distance": 2431.6, "id": "GLE", "type": "CONTROL", "name": "Glendambo"},
    {"distance": 2717.6, "id": "PTA", "type": "CONTROL", "name": "Port Augusta"},
    {"distance": 3000.1, "id": "AUA", "type": "END",     "name": "Adelaide Urban Area"},
    {"distance": 3024.5, "id": "MAR", "type": "RALLY",   "name": "Marshalling Area"},
    {"distance": 3027.4, "id": "ADL", "type": "FINISH",  "name": "Finish Line"},
  ]

def fetch_positions():
    """Fetch team telemetry from BWSC API."""
    response = requests.get(URL)
    response.raise_for_status()
    return response.json()

def display_table(data):
    """Convert telemetry data to a nicely formatted table."""
    teams = []
    for entry in data["items"]:
        teams.append({
            "Num": entry.get("teamnum"),
            "Name": entry.get("shortname"),
            "Car": entry.get("car"),
            "Dist (km)": round(entry.get("distance", 0),1),
            "Speed (km/h)": f"{entry.get("speed", 0):.1f}",
            "Avg Speed (km/h)": f"{entry.get("avg_speed", 0):1f}",
            "Class": entry.get("class"),
            "Competing": entry.get("competing"),
        })

    # Sort by distance to calculate race position
    df = pd.DataFrame(teams)
    df = df.sort_values("Dist (km)", ascending=False).reset_index(drop=True)
    df.insert(0, "Pos", df.index + 1)

    # Use tabulate for pretty table output
    rows = df.values.tolist()
    headers = df.columns.tolist()

    print(
        tabulate(
            rows,
            headers=headers,
            tablefmt="simple",
            colalign=("right", "right", "left", "left", "right", "right", "right")
        )
    )

##############################################################################
# More detailed table
def control_point_distances(control_points):
    cp_distances = [cp["distance"] for cp in control_points]
    return cp_distances

def control_point_progress(team_distance, cp_distances):
    """
    team_distance: current distance travelled
    cp_distances: list of distances to each control point (cumulative)
    """
    total = len(cp_distances)
    mark = "X"
    bar = "["+mark+"]"
    for i in range(1, total):
        if cp_distances[i] <= team_distance:
            bar = bar + "=="
            mark = "X"
        elif cp_distances[i-1] <= team_distance and team_distance <= cp_distances[i]:
            bar = bar + "=>"
            mark = " "
        else:
            bar = bar + "--"
            mark = " "

        if control_points[i]["type"] == "CONTROL":
            bar = bar + "["+mark+"]"
        elif control_points[i]["type"] == "END":
            bar = bar + "["+mark+"]"
        elif control_points[i]["type"] == "FINISH":
            bar = bar + "("+mark+")"
        else:
            bar = bar + "("+mark+")"
    return bar


def stage_progress(team_distance, cp_distances, length=20):
    """
    team_distance: current distance travelled
    cp_distances: list of distances to each control point (cumulative)
    """

    total = len(cp_distances)

    last = 0
    next = 1

    for i in range(1, total):
        if cp_distances[i-1] <= team_distance and team_distance <= cp_distances[i]:
            last = i-1
            next = i
    passed = team_distance - cp_distances[last]
    total = cp_distances[next] - cp_distances[last]

    filled_len = int(length * passed / total)
    bar =  "|" + "=" * filled_len + ">" + " " * (length - filled_len) +"|"
    return bar

##############################################################################
def output_table(data):
    """Convert telemetry data to data file for saving."""
    teams = []
    for entry in data["items"]:
        distance = round(entry.get("distance", 0),1)
        cp_distances = control_point_distances(control_points)
        speed = round(entry.get("speed", 0),1)
        if speed < 5.0:
            speed = "----"
        else:
            speed = f"{speed:.1f}"
        if entry.get("competing") == True:
            teams.append({
                "N": entry.get("teamnum"),
                "Team": entry.get("shortname"),
                "Car": entry.get("car"),
                "Dist": distance,
                "Spd": speed,
                # "Avg Speed": f"{entry.get("avg_speed", 0):1f}",
                "Class": entry.get("class"),
                # "Competing": entry.get("competing"),
                "Control Points": control_point_progress(distance, cp_distances),
                "Stage": stage_progress(distance, cp_distances),
            })

    # Sort by distance to calculate race position
    df = pd.DataFrame(teams)
    df = df.sort_values("Dist", ascending=False).reset_index(drop=True)
    df.insert(0, "P", df.index + 1)

    leader_distance = df["Dist"].iloc[0]
    df.insert(5,"Gap",0.0)
    df["Gap"] = leader_distance - df["Dist"]

    # Fix up some formatting in post-processing
    #df["Dist"] = df["Dist"].map(lambda x: x * 1.0)
    #df["Dist"] = df["Dist"].map(lambda x: f"{x:.1f}")

    # Use tabulate for pretty table output
    rows = df.values.tolist()
    headers = df.columns.tolist()

    control_point_ids = ""
    for i in range(0,len(control_points)):
        control_point_ids = control_point_ids + "  " + control_points[i]["id"]

    print(" " * 76 + control_point_ids)

    print(
        tabulate(
            rows,
            headers=headers,
            tablefmt="simple",
            colalign=("right",
                      "right",
                      "left",
                      "left",
                      "right",
                      "right",
                      "right",
                      #"right",
                      # "left",
                      "left",
                      "left",
                      "left"),
            floatfmt=".1f",
        )
    )

if __name__ == "__main__":
    data = fetch_positions()
#    display_table(data)
    output_table(data)
