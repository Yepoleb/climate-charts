from dataclasses import dataclass
import datetime
import itertools

import requests
import requests_cache

# ~ import logging
# ~ logging.basicConfig()
# ~ logging.getLogger().setLevel(logging.DEBUG)
# ~ requests_log = logging.getLogger("requests.packages.urllib3")
# ~ requests_log.setLevel(logging.DEBUG)
# ~ requests_log.propagate = True

requests_cache.install_cache("requests")
session = requests.Session()

@dataclass
class StationData:
    coordinates: tuple[float, float]
    rows: list[dict]

@dataclass
class ParameterInfo:
    name: str
    description: str
    unit: str

@dataclass
class StationDataset:
    parameters: list[ParameterInfo]
    stations: dict[str, StationData]

def make_table(series):
    columns = list(series.keys())
    # transform {"a": [1, 2], "b": [3, 4]} into [{"a": 1, "b": 2}, {"a": 2, "b": 4}]
    rows = [
        dict(y) for y in zip(
            *[zip(itertools.repeat(column_name), value) for column_name, value in series.items()]
        )
    ]
    return {"columns": columns, "data": rows}

def get_dataset(dataset_name, start, end, station_id, parameter_names):
    print(f"Requesting {dataset_name} from {start} to {end}, station {station_id}, parameters {parameter_names}")
    resp = session.get(
        f"https://dataset.api.hub.zamg.ac.at/v1/station/historical/{dataset_name}",
        params={
            "parameters": ",".join(parameter_names),
            "start": start.strftime("%Y-%m-%dT%H:%M"),
            "end": end.strftime("%Y-%m-%dT%H:%M"),
            "station_ids": station_id
        }
    )
    assert resp.headers["Content-Type"] == "application/json"
    resp_data = resp.json()
    native_timestamps = [
        datetime.datetime.fromisoformat(d)
        for d in resp_data["timestamps"]
    ]
    parameters = [
        ParameterInfo(
            name = param_name,
            description = resp_data["features"][0]["properties"]["parameters"][param_name]["name"],
            unit = resp_data["features"][0]["properties"]["parameters"][param_name]["unit"]
        )
        for param_name in parameter_names
    ]
    stations = {}
    for feature in resp_data["features"]:
        coordinates = feature["geometry"]["coordinates"]
        station_id = feature["properties"]["station"]
        param_series = {
            param_name: feature["properties"]["parameters"][param_name]["data"]
            for param_name in parameter_names
        }
        param_series["timestamp"] = native_timestamps
        rows = make_table(param_series)["data"]
        stations[station_id] = StationData(coordinates, rows)

    return StationDataset(parameters, stations)

def get_dataset_year_range(dataset_name, start, end, station_id, parameter_names):
    year_start = datetime.datetime(start, 1, 1, 0, 0, 0)
    year_end = datetime.datetime(end, 12, 31, 23, 59, 59)
    return get_dataset(dataset_name, year_start, year_end, station_id, parameter_names)

def get_metadata(dataset_name):
    resp = session.get(f"https://dataset.api.hub.zamg.ac.at/v1/station/historical/{dataset_name}/metadata")
    assert resp.headers["Content-Type"] == "application/json"
    resp_data = resp.json()
    return resp_data
