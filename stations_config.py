from pprint import pprint
import json
import datetime
import collections
import string

import geosphereapi



metadata = geosphereapi.get_metadata("klima-v1-1m")
metadata_daily = geosphereapi.get_metadata("klima-v1-1d")

end_date = datetime.datetime(2023, 1, 1, tzinfo=datetime.timezone.utc)
start_date = end_date.replace(year=end_date.year - 30)

available_daily = set(station["id"] for station in metadata_daily["stations"])

active_stations = []
for station in metadata["stations"]:
    valid_from = datetime.datetime.fromisoformat(station["valid_from"])
    valid_to = datetime.datetime.fromisoformat(station["valid_to"])
    if valid_from <= start_date and valid_to >= end_date and not station["group_id"]:
        if station["id"] in available_daily:
            active_stations.append(station)
        else:
            print(station["name"], "not in daily")

active_stations.sort(key=lambda s: s["name"])
for station in active_stations:
    print(station["name"], station["type"], station["id"], station["group_id"])
print(len(active_stations))

stations_index = collections.defaultdict(list)
for station in active_stations:
    stations_index[station["state"]].append(station["name"])

pprint(stations_index)

def write_names():
    configfile = open("station_names_new.ini", "w")
    for station in active_stations:
        station_id = station["id"]
        name = station["name"]
        displayname = name.title()
        slug = ""
        for c in name.casefold():
            if c in string.ascii_letters:
                slug += c
            else:
                slug += '_'
        configfile.write(
            f"[{station_id}]\n"
            f"name = {name}\n"
            f"displayname = {displayname}\n"
            f"slug = {slug}\n"
            "\n"
        )

write_names()

stations_map = {station["id"]: station for station in active_stations}
json.dump(stations_map, open("stations_meta.json", "w"), indent=2, ensure_ascii=False)
