import datetime
import json
import configparser
import pathlib
import itertools

import charts


MONTH_LABELS = ["J", "F", "M", "A", "M", "J", "J", "A", "S", "O", "N", "D"]

def draw_template(data_path, chart_path):
    chart_style = {}

    chart = charts.Chart(charts.merge_styles(charts.default_style, chart_style))

    chart_data = json.load(open(data_path))["data"]
    labels = MONTH_LABELS

    chart.add_background()
    chart.set_x_edges(charts.calc_edges(len(labels)))
    chart.set_left_scale(charts.Scale(0, 100, 10))
    chart.draw_subdivisions()
    chart.draw_baseline()
    chart.draw_labels_x_between(labels)
    chart.draw_labels_left()
    chart.draw_unit_left("°C")
    chart.add_border()

    chart.save(chart_path, pretty=True)


def draw_temp(data_path, chart_path):
    chart_style = {
        "draw-area": {
            "margin-right": 140
        },
        "label-left": {
            "fill": "#B01500"
        },
        "unit-left": {
            "fill": "#B01500"
        },
        "series-t": {
            "stroke": "#1dbf00",
            "fill": "none",
            "stroke-width": "5px",
            "stroke-linejoin": "round"
        },
        "series-tmax": {
            "stroke": "#E61700",
            "fill": "none",
            "stroke-width": "2px",
            "stroke-linejoin": "round"
        },
        "series-tmin": {
            "stroke": "#0F00E6",
            "fill": "none",
            "stroke-width": "2px",
            "stroke-linejoin": "round"
        },
        "series-mtmax": {
            "stroke": "#E67800",
            "fill": "none",
            "stroke-width": "3px",
            "stroke-linejoin": "round"
        },
        "series-mtmin": {
            "stroke": "#00B2E6",
            "fill": "none",
            "stroke-width": "3px",
            "stroke-linejoin": "round"
        },
        "poly-max": {
            "stroke": "none",
            "fill": "#E60011",
            "fill-opacity": 0.05
        },
        "poly-min": {
            "stroke": "none",
            "fill": "#003AE6",
            "fill-opacity": 0.05
        },
        "poly-mid": {
            "stroke": "none",
            "fill": "#E6AC00",
            "fill-opacity": 0.2
        }
    }

    chart = charts.Chart(charts.merge_styles(charts.default_style, chart_style))

    chart_data = json.load(open(data_path))["data"]
    labels = MONTH_LABELS
    series_names = ["t", "tmax", "tmin", "mtmax", "mtmin"]

    all_values = list(itertools.chain.from_iterable(
        [r[series_name] for r in chart_data] for series_name in series_names
    ))

    chart.add_background()
    chart.set_x_edges(charts.calc_edges(len(labels)))
    chart.set_left_scale(charts.auto_fit_scale(-20, 40, 10, all_values))
    chart.draw_subdivisions()
    chart.draw_baseline()
    chart.draw_labels_x_between(labels)
    chart.draw_labels_left()
    chart.draw_unit_left("°C")


    points = {}
    for series_name in series_names:
        series_temp = [r[series_name] for r in chart_data]
        series_points = chart.to_line(series_temp, "left", "between")
        points[series_name] = series_points
        chart.add_legend(series_name)

    area_max = points["tmax"] + list(reversed(points["mtmax"]))
    chart.draw_polygon("max", area_max)
    area_min = points["tmin"] + list(reversed(points["mtmin"]))
    chart.draw_polygon("min", area_min)
    area_mid = points["mtmax"] + list(reversed(points["mtmin"]))
    chart.draw_polygon("mid", area_mid)

    for series_name in series_names:
        chart.draw_line(series_name, points[series_name])

    chart.draw_legend()
    chart.add_border()

    chart.save(chart_path, pretty=True)


def draw_climate(data_path, chart_path):
    chart_style = {
        "label-left": {
            "fill": "#B01500"
        },
        "unit-left": {
            "fill": "#B01500"
        },
        "label-right": {
            "fill": "#0099D0"
        },
        "unit-right": {
            "fill": "#0099D0"
        },
        "series-t": {
            "stroke": "#B01500",
            "fill": "none",
            "stroke-width": 3,
            "stroke-linejoin": "round"
        },
        "series-rsum": {
            "stroke": "#0099D0",
            "fill": "none",
            "stroke-width": 3
        },
        "poly-rsum": {
            "stroke": "none",
            "fill": "#0099D0",
            "fill-opacity": 0.35
        }
    }

    chart = charts.Chart(charts.merge_styles(charts.default_style, chart_style))
    chart_data = json.load(open(data_path))["data"]
    labels = MONTH_LABELS
    rsum_data = [r["rsum"] for r in chart_data]
    t_data = [r["t"] for r in chart_data]

    chart.add_background()
    chart.add_border()
    chart.set_x_edges(charts.calc_edges(len(labels)))
    chart.set_left_scale(charts.auto_fit_scale(-20, 50, 10, t_data))
    chart.set_right_scale(charts.auto_fit_scale(0, 200, 20, rsum_data))
    chart.draw_subdivisions()
    chart.draw_baseline()
    chart.draw_labels_x_between(labels)
    chart.draw_labels_left()
    chart.draw_labels_right()
    chart.draw_unit_left("°C")
    chart.draw_unit_right("mm")
    rsum_points = chart.to_stepped_line(rsum_data, "right")
    chart.draw_polygon("rsum", rsum_points + list(reversed(chart.baseline_points())))
    chart.draw_line("rsum", rsum_points)
    chart.draw_line("t", chart.to_line(t_data, "left", "between"))

    chart.save(chart_path, pretty=True)


def draw_temp_daily(data_path, chart_path):
    chart_style = {
        "draw-area": {
            "width": 1000,
            "height": 400,
            "margin-right": 140
        },
        "label-left": {
            "fill": "#B01500"
        },
        "unit-left": {
            "fill": "#B01500"
        },
        "series-t": {
            "stroke": "#000000",
            "fill": "none",
            "stroke-width": "2px",
            "stroke-linejoin": "round"
        },
        "series-tmax": {
            "stroke": "#E61700",
            "fill": "none",
            "stroke-width": "1px",
            "stroke-linejoin": "round"
        },
        "series-tmin": {
            "stroke": "#0F00E6",
            "fill": "none",
            "stroke-width": "1px",
            "stroke-linejoin": "round"
        },
        "poly-max": {
            "stroke": "none",
            "fill": "#E60011",
            "fill-opacity": 0.4
        },
        "poly-min": {
            "stroke": "none",
            "fill": "#003AE6",
            "fill-opacity": 0.4
        }
    }

    chart = charts.Chart(charts.merge_styles(charts.default_style, chart_style))

    chart_data = json.load(open(data_path))["data"]
    labels = MONTH_LABELS
    series_names = ["t", "tmax", "tmin"]

    all_values = list(itertools.chain.from_iterable(
        [r[series_name] for r in chart_data] for series_name in series_names
    ))
    if None in all_values:
        return False

    year = 2022
    year_start = datetime.datetime(year, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc)
    year_end = datetime.datetime(year, 12, 31, 23, 59, 59, tzinfo=datetime.timezone.utc)
    year_time = year_end - year_start
    month_divisions_pos = []
    for month in range(2, 13):
        month_start = datetime.datetime(year, month, 1, 0, 0, 0, tzinfo=datetime.timezone.utc)
        month_time = month_start - year_start
        month_fraction = month_time / year_time
        month_divisions_pos.append(month_fraction)

    chart.add_background()
    chart.set_x_edges(month_divisions_pos)
    chart.set_left_scale(charts.auto_fit_scale(-20, 40, 10, all_values))
    chart.draw_subdivisions()
    chart.draw_baseline()
    chart.draw_labels_x_between(labels)
    chart.draw_labels_left()
    chart.draw_unit_left("°C")

    num_rows = len(chart_data)
    points = {}
    for series_name in series_names:
        series_temp = []
        for i, r in enumerate(chart_data):
            val = r[series_name]
            if val is not None:
                series_temp.append((i / (num_rows - 1), val))
        series_points = chart.line_from_xy(series_temp, "left")
        points[series_name] = series_points
        chart.add_legend(series_name)

    area_max = points["tmax"] + list(reversed(points["t"]))
    chart.draw_polygon("max", area_max)
    area_min = points["tmin"] + list(reversed(points["t"]))
    chart.draw_polygon("min", area_min)
    chart.draw_line("t", points["t"])

    chart.draw_legend()
    chart.add_border()

    chart.save(chart_path, pretty=True)


def draw_temp_freq(data_path, chart_path):
    chart_style = {
        "draw-area": {
            "margin-right": 140,
        },
        "series-tmin-count": {
            "stroke": "#0F00E6",
            "fill": "#0F00E6",
            "stroke-width": "3",
            "fill-opacity": 0.5,
            "stroke-linejoin": "round"
        },
        "series-tmax-count": {
            "stroke": "#E61700",
            "fill": "#E61700",
            "stroke-width": "3",
            "fill-opacity": 0.5,
            "stroke-linejoin": "round"
        }
    }

    chart = charts.Chart(charts.merge_styles(charts.default_style, chart_style))

    chart_data = json.load(open(data_path))["data"]
    labels = [r["label"] for r in chart_data]
    tmin_data = [r["tmin_count"] for r in chart_data]
    tmax_data = [r["tmax_count"] for r in chart_data]

    chart.add_background()
    chart.set_x_edges(charts.calc_edges(len(labels)))
    chart.set_left_scale(charts.auto_fit_scale(0, 40, 10, tmin_data + tmax_data))
    chart.draw_subdivisions()
    chart.draw_baseline()
    labels_lower = [label.split(" - ")[0] for label in labels]
    chart.draw_labels_x_edges(labels_lower)
    chart.draw_unit_x("°C")
    chart.draw_labels_left()
    chart.draw_unit_left("Tage")
    chart.add_legend("tmin-count", "tmin")
    chart.add_legend("tmax-count", "tmax")
    chart.draw_legend()
    chart.draw_bars("tmin-count", tmin_data, "left")
    chart.draw_bars("tmax-count", tmax_data, "left")
    chart.add_border()  # draw border last so it overlays the bars

    chart.save(chart_path, pretty=True)


def draw_heatingdays(data_path, chart_path):
    chart_style = {
        "draw-area": {
            "margin-right": 140
        },
        "label-left": {
            "fill": "#C32B00"
        },
        "unit-left": {
            "fill": "#C32B00"
        },
        "label-right": {
            "fill": "#00C314"
        },
        "unit-right": {
            "fill": "#00C314"
        },
        "legend-line": {
            "margin": 70,  # virtual
        },
        "series-ht": {
            "stroke": "#00C314",
            "fill": "#00C314",
            "fill-opacity": 0.7,
            "stroke-width": "3px",
            "stroke-linejoin": "round"
        },
        "series-gradt": {
            "stroke": "#0023C3",
            "fill": "#0023C3",
            "fill-opacity": 0.4,
            "stroke-width": "3px",
            "stroke-linejoin": "round"
        }
    }

    chart = charts.Chart(charts.merge_styles(charts.default_style, chart_style))

    chart_data = json.load(open(data_path))["data"]
    labels = MONTH_LABELS
    ht_data = [r["ht"] for r in chart_data]
    gradt_data = [r["gradt"] for r in chart_data]

    chart.add_background()
    chart.set_x_edges(charts.calc_edges(len(labels)))
    chart.set_left_scale(charts.auto_fit_scale(0, 30, 5, ht_data))
    chart.set_right_scale(charts.auto_fit_scale(0, 700, 100, gradt_data))
    chart.draw_subdivisions()
    chart.draw_baseline()
    chart.draw_labels_x_between(labels)
    chart.draw_labels_left()
    chart.draw_labels_right()
    chart.draw_unit_left("Tage")
    chart.draw_unit_right("Kd")
    chart.add_legend("ht")
    chart.add_legend("gradt")
    chart.draw_legend()

    chart.draw_bars("ht", ht_data, "left")
    chart.draw_bars("gradt", gradt_data, "right")

    chart.add_border()

    chart.save(chart_path, pretty=True)


def draw_sun(data_path, chart_path):
    chart_style = {
        "draw-area": {
            "margin-right": 180
        },
        "label-left": {
            "fill": "#FF8600"
        },
        "unit-left": {
            "fill": "#FF8600"
        },
        "label-right": {
            "margin": 57,
            "fill": "#A600FF"
        },
        "unit-right": {
            "fill": "#A600FF"
        },
        "legend-line": {
            "margin": 85,  # virtual
        },
        "series-s": {
            "stroke": "#FF8600",
            "fill": "none",
            "stroke-width": "3px",
            "stroke-linejoin": "round"
        },
        "series-global": {
            "stroke": "#A600FF",
            "fill": "none",
            "stroke-width": "3px",
            "stroke-linejoin": "round"
        }
    }

    chart = charts.Chart(charts.merge_styles(charts.default_style, chart_style))

    chart_data = json.load(open(data_path))["data"]
    labels = MONTH_LABELS
    s_data = [r["s"] for r in chart_data]
    global_data = [r["global"] for r in chart_data]

    chart.add_background()
    chart.set_x_edges(charts.calc_edges(len(labels)))
    chart.set_left_scale(charts.auto_fit_scale(0, 250, 50, s_data))
    chart.set_right_scale(charts.auto_fit_scale(0, 70000, 10000, global_data))
    chart.draw_subdivisions()
    chart.draw_baseline()
    chart.draw_labels_x_between(labels)
    chart.draw_labels_left()
    chart.draw_labels_right()
    chart.draw_unit_left("h")
    chart.draw_unit_right("J/cm²")
    chart.add_legend("s")
    chart.add_legend("global")
    chart.draw_legend()

    chart.draw_line("s", chart.to_line(s_data, "left", "between"))
    chart.draw_line("global", chart.to_line(global_data, "right", "between"))

    chart.add_border()

    chart.save(chart_path, pretty=True)


def draw_humid(data_path, chart_path):
    chart_style = {
        "draw-area": {
            "margin-right": 150,
        },
        "label-left": {
            "fill": "#FF8600"
        },
        "unit-left": {
            "fill": "#FF8600"
        },
        "legend-line": {
            "margin": 30,  # virtual
        },
        "series-rel": {
            "stroke": "#0AB300",
            "fill": "none",
            "fill-opacity": 0.7,
            "stroke-width": "3px",
            "stroke-linejoin": "round"
        },
        "series-rel7": {
            "stroke": "#0046E8",
            "fill": "none",
            "fill-opacity": 0.7,
            "stroke-width": "3px",
            "stroke-linejoin": "round"
        },
        "series-rel14": {
            "stroke": "#E80D00",
            "fill": "none",
            "stroke-width": "3px",
            "stroke-linejoin": "round"
        },
        "series-equiv20": {
            "stroke": "#E8BA00",
            "fill": "none",
            "stroke-width": "3px",
            "stroke-linejoin": "round"
        }
    }

    chart = charts.Chart(charts.merge_styles(charts.default_style, chart_style))

    chart_data = json.load(open(data_path))["data"]
    labels = MONTH_LABELS

    chart.add_background()
    chart.set_x_edges(charts.calc_edges(len(labels)))
    chart.set_left_scale(charts.Scale(0, 100, 10))
    chart.draw_subdivisions()
    chart.draw_baseline()
    chart.draw_labels_x_between(labels)
    chart.draw_labels_left()
    chart.draw_unit_left("%")
    chart.add_legend("rel")
    chart.add_legend("rel7")
    chart.add_legend("rel14")
    chart.add_legend("equiv20")
    chart.draw_legend()

    chart.draw_line("rel", chart.to_line([r["rel"] for r in chart_data], "left", "between"))
    chart.draw_line("rel7", chart.to_line([r["rel7"] for r in chart_data], "left", "between"))
    chart.draw_line("rel14", chart.to_line([r["rel14"] for r in chart_data], "left", "between"))
    chart.draw_line("equiv20", chart.to_line([r["equiv20"] for r in chart_data], "left", "between"))

    chart.add_border()

    chart.save(chart_path, pretty=True)


def draw_precip(data_path, chart_path):
    chart_style = {
        "draw-area": {
            "margin-right": 140
        },
        "label-left": {
            "fill": "#0099D0"
        },
        "unit-left": {
            "fill": "#0099D0"
        },
        # ~ "legend-line": {
            # ~ "margin": 70,  # virtual
        # ~ },
        "series-rsum": {
            "stroke": "#0099D0",
            "fill": "none",
            "stroke-width": "3px",
            "stroke-linejoin": "round"
        },
        "series-festrr": {
            "stroke": "#74F2FF",
            "fill": "none",
            "stroke-width": "3px",
            "stroke-linejoin": "round"
        },
        "poly-rsum": {
            "stroke": "none",
            "fill": "#0099D0",
            "fill-opacity": 0.35
        },
        "poly-festrr": {
            "stroke": "none",
            "fill": "#74F2FF",
            "fill-opacity": 0.5
        }
    }

    chart = charts.Chart(charts.merge_styles(charts.default_style, chart_style))

    chart_data = json.load(open(data_path))["data"]
    labels = MONTH_LABELS
    rsum_data = [r["rsum"] for r in chart_data]
    festrr_data = [r["festrr"] for r in chart_data]

    chart.add_background()
    chart.set_x_edges(charts.calc_edges(len(labels)))
    chart.set_left_scale(charts.auto_fit_scale(0, 200, 20, rsum_data + festrr_data))
    chart.draw_subdivisions()
    chart.draw_baseline()
    chart.draw_labels_x_between(labels)
    chart.draw_labels_left()
    chart.draw_unit_left("mm")
    chart.add_legend("rsum")
    chart.add_legend("festrr")
    chart.draw_legend()

    rsum_points = chart.to_stepped_line(rsum_data, "left")
    festrr_points = chart.to_stepped_line(festrr_data, "left")
    chart.draw_polygon("rsum", rsum_points + list(reversed(festrr_points)))
    chart.draw_polygon("festrr", festrr_points + list(reversed(chart.baseline_points())))
    chart.draw_line("rsum", rsum_points)
    chart.draw_line("festrr", festrr_points)

    chart.add_border()

    chart.save(chart_path, pretty=True)


stations_config = configparser.ConfigParser()
stations_config.read_file(open("station_names.ini"))
stations_meta = json.load(open("stations_meta.json"))
output_path = pathlib.Path("out")

for station_meta in stations_meta.values():
    station_id = station_meta["id"]
    station_slug = stations_config[station_id]["slug"]
    station_path = output_path / station_slug

    station_path.mkdir(parents=True, exist_ok=True)
    draw_temp(station_path / "table_temp.json", station_path / "chart_temp.svg")
    draw_climate(station_path / "table_climate.json", station_path / "chart_climate.svg")
    draw_temp_daily(station_path / "table_temp_daily.json", station_path / "chart_temp_daily.svg")
    draw_temp_freq(station_path / "table_temp_freq.json", station_path / "chart_temp_freq.svg")
    draw_heatingdays(station_path / "table_heatingdays.json", station_path / "chart_heatingdays.svg")
    if (station_path / "table_sun.json").exists():
        draw_sun(station_path / "table_sun.json", station_path / "chart_sun.svg")
    draw_humid(station_path / "table_humid.json", station_path / "chart_humid.svg")
    if (station_path / "table_precip.json").exists():
        draw_precip(station_path / "table_precip.json", station_path / "chart_precip.svg")
