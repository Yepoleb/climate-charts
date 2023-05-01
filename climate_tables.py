from dataclasses import dataclass
import configparser
import datetime
import statistics
import json
import collections
import math
import pathlib

import geosphereapi
from geosphereapi import make_table


def get_month_multi(dataset, month, series):
    return [row[series] for row in dataset if row["timestamp"].month == month]

def get_month_scalar(dataset, month, series):
    results = get_month_multi(dataset, month, series)
    if len(results) != 1:
        raise ValueError(f"dataset contains not 1 value for month {month}: {results}")
    return results[0]

def get_months_scalar(dataset, series):
    return [
        get_month_scalar(dataset, month, series)
        for month in range(1, 13)
    ]

# ~ def get_months_average(dataset, series, average_func):
    # ~ return [
        # ~ average_func(get_month_multi(dataset, month, series))
        # ~ for month in range(1, 13)
    # ~ ]

def get_months_average_unreliable(dataset, series, average_func):
    return [
        average_func(filter(lambda x: x is not None, get_month_multi(dataset, month, series)))
        for month in range(1, 13)
    ]

get_months_average = get_months_average_unreliable

def json_encoder(x):
    if isinstance(x, datetime.date) or isinstance(x, datetime.datetime):
        assert x.tzinfo is not None
        return x.isoformat()
    else:
        raise TypeError(type(x), repr(x))

def json_dump(obj, f):
    json.dump(obj, f, indent=2, ensure_ascii=False, default=json_encoder)


def make_table_temp(station_monthly):
    return make_table({
        "month": MONTH_NAMES,
        "t": get_months_average(station_monthly, "t", statistics.mean),
        "tmax": get_months_average(station_monthly, "tmax", max),
        "tmin": get_months_average(station_monthly, "tmin", min),
        "mtmax": get_months_average(station_monthly, "mtmax", statistics.mean),
        "mtmin": get_months_average(station_monthly, "mtmin", statistics.mean),
    })



def make_table_climate(station_monthly):
    return make_table({
        "month": MONTH_NAMES,
        "t": get_months_average(station_monthly, "t", statistics.mean),
        "rsum": get_months_average(station_monthly, "rsum", statistics.mean)
    })


def make_table_temp_daily(station_daily):
    year_days = (datetime.datetime(last_year + 1, 1, 1) - datetime.datetime(last_year, 1, 1)).days
    return make_table({
        "day": list(range(0, year_days)),
        "t": [d["t"] for d in station_daily if d["timestamp"].year == last_year],
        "tmax": [d["tmax"] for d in station_daily if d["timestamp"].year == last_year],
        "tmin": [d["tmin"] for d in station_daily if d["timestamp"].year == last_year]
    })


def make_table_temp_freq(station_daily):
    counters = {name: collections.defaultdict(int) for name in ["t", "tmin", "tmax"]}
    bucket_size = 5
    for day in station_daily:
        for parameter_name in counters.keys():
            day_value = day[parameter_name]
            if day_value is None:
                continue
            bucket = int(round(day_value)) // bucket_size * bucket_size
            counters[parameter_name][bucket] += 1

    temp_frequency_table = {
        "columns": ["label"],
        "data": []
    }

    for parameter_name in counters.keys():
        temp_frequency_table["columns"].append(parameter_name + "_count")
        temp_frequency_table["columns"].append(parameter_name + "_perc")

    for bucket_low in range(-20, 45, bucket_size):
        bucket_label = f"{bucket_low} - {bucket_low + bucket_size - 1}"
        temp_frequency_row = {
            "label": bucket_label
        }
        for parameter_name in counters.keys():
            count = round(counters[parameter_name][bucket_low] / num_years, 1)
            perc = round(counters[parameter_name][bucket_low] / num_days * 100, 1)
            temp_frequency_row[parameter_name + "_count"] = count
            temp_frequency_row[parameter_name + "_perc"] = perc
        temp_frequency_table["data"].append(temp_frequency_row)

    return temp_frequency_table


def make_table_special_days(station_monthly):
    return make_table({
        "month": MONTH_NAMES,
        "frost": get_months_average(station_monthly, "frost", statistics.mean),
        "eis": get_months_average(station_monthly, "eis", statistics.mean),
        "sommer": get_months_average(station_monthly, "sommer", statistics.mean)
    })



# ~ heatingdays_counter = collections.defaultdict(int)
# ~ heatingdegdays_counter = collections.defaultdict(float)
# ~ for day in station_daily:
    # ~ if day["t"] < 12.0:
        # ~ month_index = day["timestamp"].month - 1
        # ~ heatingdays_counter[month_index] += 1
        # ~ heatingdegdays_counter[month_index] += 20 - day["t"]

# ~ heatingdays_table = make_table({
    # ~ "month": MONTH_NAMES,
    # ~ "heatingdays": [round(heatingdays_counter[m] / num_years, 1) for m in range(12)],
    # ~ "heatingdegdays": [round(heatingdegdays_counter[m] / num_years, 1) for m in range(12)]
# ~ })
def make_table_heatingdays(station_monthly):
    return make_table({
        "month": MONTH_NAMES,
        "ht": get_months_average(station_monthly, "ht", statistics.mean),
        "gradt": get_months_average(station_monthly, "gradt", statistics.mean)
    })


def make_table_precip(station_monthly):
    return make_table({
        "month": MONTH_NAMES,
        "rsum": get_months_average(station_monthly, "rsum", statistics.mean),
        "rmax": get_months_average(station_monthly, "rmax", max),
        "festrr": get_months_average(station_monthly, "festrr", statistics.mean),
        "n1": get_months_average(station_monthly, "n1", statistics.mean),
        "n10": get_months_average(station_monthly, "n10", statistics.mean)
    })


def make_table_sun(station_monthly):
    return make_table({
        "month": MONTH_NAMES,
        "s": get_months_average(station_monthly, "s", statistics.mean),
        "global": get_months_average(station_monthly, "global", statistics.mean)
    })


def magnus_formula(t):
    # Return saturation vapor pressure of water in hPa
    return 6.122 * math.exp((17.62*t) / (243.12+t))

def make_table_humid(station_monthly):
    e_avg = get_months_average(station_monthly, "e", statistics.mean)
    t_avg = get_months_average(station_monthly, "t", statistics.mean)
    sat_pres_20 = magnus_formula(20)
    equiv20 = []
    for e, t in zip(e_avg, t_avg):
        rel = e / sat_pres_20 * 100
        equiv20.append(rel)

    return make_table({
        "month": MONTH_NAMES,
        "e": get_months_average(station_monthly, "e", statistics.mean),
        "rel": get_months_average(station_monthly, "rel", statistics.mean),
        "rel7": get_months_average(station_monthly, "rel7", statistics.mean),
        "rel14": get_months_average(station_monthly, "rel14", statistics.mean),
        "equiv20": equiv20
    })




last_year = 2022
num_years = 30
start_year = last_year - num_years

end_date = datetime.datetime(last_year + 1, 1, 1, tzinfo=datetime.timezone.utc)
start_date = datetime.datetime(start_year + 1, 1, 1, tzinfo=datetime.timezone.utc)
num_days = (end_date - start_date).days

monthly_params = [
    "t", "tmax", "tmin", "mtmax", "mtmin",
    "rsum", "rmax", "festrr", "n1", "n10", "s", "global",
    "frost", "eis", "sommer", "ht", "gradt",
    "rel", "rel7", "rel14", "e"
]
chart_temp_daily_params = ["t", "tmax", "tmin"]

MONTH_NAMES = ["Jan", "Feb", "Mär", "Apr", "Mai", "Jun", "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"]

stations_config = configparser.ConfigParser()
stations_config.read_file(open("station_names.ini"))
stations_meta = json.load(open("stations_meta.json"))
output_path = pathlib.Path("out")

for station_meta in stations_meta.values():
    station_id = station_meta["id"]
    station_slug = stations_config[station_id]["slug"]
    station_path = output_path / station_slug

    data_monthly = geosphereapi.get_dataset_year_range(
        "klima-v1-1m", start_year, last_year, station_id, monthly_params)
    data_daily = geosphereapi.get_dataset_year_range(
        "klima-v1-1d", start_year, last_year, station_id, chart_temp_daily_params)

    station_monthly = data_monthly.stations[station_id].rows
    station_daily = data_daily.stations[station_id].rows

    station_path.mkdir(parents=True, exist_ok=True)

    json_dump(station_monthly, open(station_path / "station_monthly.json", "w"))
    json_dump(station_daily, open(station_path / "station_daily.json", "w"))

    table_temp = make_table_temp(station_monthly)
    json_dump(table_temp, open(station_path / "table_temp.json", "w"))
    table_climate = make_table_climate(station_monthly)
    json_dump(table_climate, open(station_path / "table_climate.json", "w"))
    table_temp_daily = make_table_temp_daily(station_daily)
    json_dump(table_temp_daily, open(station_path / "table_temp_daily.json", "w"))
    table_temp_freq = make_table_temp_freq(station_daily)
    json_dump(table_temp_freq, open(station_path / "table_temp_freq.json", "w"))
    #table_special_days = make_table_special_days(station_monthly)
    #json_dump(table_special_days, open(station_path / "table_special_days.json", "w"))
    table_heatingdays = make_table_heatingdays(station_monthly)
    json_dump(table_heatingdays, open(station_path / "table_heatingdays.json", "w"))
    try:
        table_precip = make_table_precip(station_monthly)
        json_dump(table_precip, open(station_path / "table_precip.json", "w"))
    except statistics.StatisticsError:
        pass
    try:
        table_sun = make_table_sun(station_monthly)
        json_dump(table_sun, open(station_path / "table_sun.json", "w"))
    except statistics.StatisticsError:
        pass
    table_humid = make_table_humid(station_monthly)
    json_dump(table_humid, open(station_path / "table_humid.json", "w"))
