import jinja2
import json
import configparser
import pathlib
import collections
import shutil



jenv = jinja2.Environment(
    loader=jinja2.FileSystemLoader("templates"),
    autoescape=True, trim_blocks=True, lstrip_blocks=True,
    keep_trailing_newline=False)

stations_config = configparser.ConfigParser()
stations_config.read_file(open("station_names.ini"))
stations_meta = json.load(open("stations_meta.json"))
output_path = pathlib.Path("out")

stations_index = collections.defaultdict(list)
for station in stations_meta.values():
    station_id = station["id"]
    station_slug = stations_config[station_id]["slug"]
    station_displayname = stations_config[station_id]["displayname"]
    station_path = output_path / station_slug
    stations_index[station["state"]].append({
        "displayname": station_displayname,
        "slug": station_slug
    })
    has_sun = (station_path / "chart_sun.svg").exists()
    has_daily = (station_path / "chart_temp_daily.svg").exists()
    has_precip = (station_path / "chart_precip.svg").exists()
    station_template = jenv.get_template("station.html")

    station_path.mkdir(parents=True, exist_ok=True)
    open(station_path / "index.html", "w").write(
        station_template.render(
            station=station, displayname=station_displayname, slug=station_slug,
            has_sun=has_sun, has_daily=has_daily, has_precip=has_precip)
    )


states = [
    "Burgenland", "Kärnten", "Niederösterreich", "Oberösterreich", "Salzburg", "Steiermark",
    "Tirol", "Vorarlberg", "Wien"
]

output_path.mkdir(parents=True, exist_ok=True)
template = jenv.get_template("list.html")
open(output_path / "index.html", "w").write(
    template.render(stations_index=stations_index, states=states)
)

shutil.copytree("assets", output_path / "assets", dirs_exist_ok=True)
