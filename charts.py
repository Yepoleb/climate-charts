from dataclasses import dataclass
import datetime
import xml.etree.ElementTree as etree
import copy
import math


@dataclass
class Scale:
    low: int
    high: int
    step: int

    @property
    def diff(self):
        return self.high - self.low

    @property
    def steps(self):
        return self.diff // self.step

    @property
    def steps_positive(self):
        return self.high // self.step

    @property
    def steps_negative(self):
        return -self.low // self.step


@dataclass
class Box:
    x: int
    y: int
    width: int
    height: int

    @property
    def top(self):
        return self.y

    @property
    def bottom(self):
        return self.y + self.height

    @property
    def left(self):
        return self.x

    @property
    def right(self):
        return self.x + self.width


def calc_edges(steps):
    step_list = [i/steps for i in range(1, steps)]
    return step_list

def pairs(l):
    return zip(l[:-1], l[1:])

def auto_fit_scale(low, high, step, data):
    data_low = int(math.floor(min(data) / step)) * step
    data_high = int(math.ceil(max(data) / step)) * step
    combined_low = min(data_low, low)
    combined_high = max(data_high, data_high)
    return Scale(combined_low, combined_high + step, step)

def subscale_labels(subscale, fullscale):
    labels = []
    for step_val in range(fullscale.low, fullscale.high + 1, fullscale.step):
        if subscale.low <= step_val <= subscale.high:
            labels.append(str(step_val))
        else:
            labels.append(None)
    return labels

class Chart:
    def __init__(self, style):
        self.style = style
        self.draw_area = Box(
            style["draw-area"]["margin-left"], style["draw-area"]["margin-top"],
            style["draw-area"]["width"], style["draw-area"]["height"]
        )
        self.image_area = Box(
            0, 0,
            self.draw_area.left + self.draw_area.width + style["draw-area"]["margin-right"],
            self.draw_area.top + self.draw_area.height + style["draw-area"]["margin-bottom"]
        )
        self.svg_root = etree.Element("svg", attrib={
            "baseProfile": "full",
            "version": "1.1",
            "xmlns": "http://www.w3.org/2000/svg",
            "width": str(self.image_area.width),
            "height": str(self.image_area.height)
        })
        self.scale_left = None
        self.scale_right = None
        self.legend = {}

    def calc_scales(self):
        if self.scale_left:
            if self.scale_right:
                self.calc_scales_dual()
            else:
                self.calc_scales_single()

    def calc_scales_single(self):
        self.scale_steps = self.scale_left.steps
        baseline_ratio = self.scale_left.high / (self.scale_left.high + abs(self.scale_left.low))
        self.baseline_y = self.draw_area.y + self.draw_area.height * baseline_ratio
        self.labels_left = []
        for step_val in range(self.scale_left.low, self.scale_left.high + 1, self.scale_left.step):
            self.labels_left.append(str(step_val))
        self.labels_right = []
        self.calc_y_edges()

    def calc_scales_dual(self):
        steps_positive = max(self.scale_left.steps_positive, self.scale_right.steps_positive)
        steps_negative = max(self.scale_left.steps_negative, self.scale_right.steps_negative)
        self.scale_steps = steps_positive + steps_negative
        baseline_ratio = steps_positive / (steps_positive + steps_negative)
        self.baseline_y = self.draw_area.y + self.draw_area.height * baseline_ratio
        adjusted_scale_left = Scale(
            self.scale_left.step * -steps_negative, self.scale_left.step * steps_positive,
            self.scale_left.step)
        adjusted_scale_right = Scale(
            self.scale_right.step * -steps_negative, self.scale_right.step * steps_positive,
            self.scale_right.step)
        self.labels_left = subscale_labels(self.scale_left, adjusted_scale_left)
        self.labels_right = subscale_labels(self.scale_right, adjusted_scale_right)
        self.calc_y_edges()

    def calc_y_edges(self):
        self.y_edges_px = [
            self.draw_area.top + y_frac * self.draw_area.height
            for y_frac in calc_edges(self.scale_steps)
        ]

    def add_element(self, tag, attrib={}, **extra):
        attrib_merged = attrib.copy()
        attrib_merged.update(extra)
        safe_attrib = {}
        for key, value in attrib_merged.items():
            attrib_name = key.replace('_', '-')
            if isinstance(value, float):
                value_str = str(round(value, 2))
            else:
                value_str = str(value)
            safe_attrib[attrib_name] = value_str
        return etree.SubElement(self.svg_root, tag, safe_attrib)

    def add_rect(self, x, y, width, height, attrib, **extra):
        return self.add_element("rect", attrib, x=x, y=y, width=width, height=height, **extra)

    def add_line(self, x1, y1, x2, y2, attrib, **extra):
        return self.add_element("line", attrib, x1=x1, y1=y1, x2=x2, y2=y2, **extra)

    def add_text(self, text, x, y, attrib, **extra):
        text_elem = self.add_element("text", attrib, x=x, y=y, **extra)
        text_elem.text = text
        return text_elem

    def add_path(self, d, attrib, **extra):
        if isinstance(d, str):
            d_str = d
        else:
            d_str = " ".join(d)

        return self.add_element("path", attrib, d=d_str, **extra)

    def save(self, filename, pretty=False):
        if pretty:
            etree.indent(self.svg_root)
        tree = etree.ElementTree(self.svg_root)
        tree.write(
            filename,
            encoding="utf-8",
            xml_declaration=True,
            method="xml",
            short_empty_elements=True
        )

    def add_background(self):
        self.add_rect(
            x=0, y=0,
            width=self.image_area.width, height=self.image_area.height,
            attrib=self.style["background"]
        )

    def add_border(self):
        self.add_rect(
            x=self.draw_area.left, y=self.draw_area.top,
            width=self.draw_area.width, height=self.draw_area.height,
            attrib=self.style["border"]
        )

    def set_x_edges(self, x_edges_fract):
        self.x_edges_px = [
            self.draw_area.left + x_fract * self.draw_area.width
            for x_fract in x_edges_fract
        ]

    def set_left_scale(self, scale):
        self.scale_left = scale
        self.calc_scales()

    def set_right_scale(self, scale):
        self.scale_right = scale
        self.calc_scales()

    def draw_subdivisions(self):
        for x in self.x_edges_px:
            self.add_line(
                x1=x, y1=self.draw_area.top, x2=x, y2=self.draw_area.bottom,
                attrib=self.style["subdivision"]
            )
        for y in self.y_edges_px:
            self.add_line(
                x1=self.draw_area.left, y1=y, x2=self.draw_area.right, y2=y,
                attrib=self.style["subdivision"]
            )

    def x_edges_with_outer(self):
        return [self.draw_area.left] + self.x_edges_px + [self.draw_area.right]

    def y_edges_with_outer(self):
        return [self.draw_area.top] + self.y_edges_px + [self.draw_area.bottom]

    def x_edges_between(self):
        return [(x1 + x2) / 2 for x1, x2 in pairs(self.x_edges_with_outer())]


    def draw_baseline(self):
        self.add_line(
            x1=self.draw_area.left, y1=self.baseline_y, x2=self.draw_area.right, y2=self.baseline_y,
            attrib=self.style["baseline"]
        )

    def draw_labels_x_between(self, labels):
        for x_pos, label in zip(self.x_edges_between(), labels):
            self.add_text(
                label, x=x_pos, y=self.draw_area.bottom + self.style["label-x"]["margin"],
                text_anchor="middle", attrib=self.style["label-x"]
            )

    def draw_labels_x_edges(self, labels, skip_last=True):
        x_positions = self.x_edges_with_outer()
        if skip_last:
            del x_positions[-1]
        for x_pos, label in zip(x_positions, labels):
            self.add_text(
                label, x=x_pos, y=self.draw_area.bottom + self.style["label-x"]["margin"],
                text_anchor="middle", attrib=self.style["label-x"]
            )

    def draw_unit_x(self, text):
        self.add_text(
            text,
            x=self.draw_area.right, y=self.draw_area.bottom + self.style["label-x"]["margin"],
            text_anchor="middle", attrib=self.style["unit-x"]
        )

    def draw_labels_left(self, skip_last=True):
        # Labels are drawn top to bottom so the list has to be reversed
        label_pairs = list(zip(reversed(self.labels_left), self.y_edges_with_outer()))
        if skip_last:
            del label_pairs[0]
        for scale_text, y in label_pairs:
            if scale_text is not None:
                self.add_text(
                    scale_text, x=self.draw_area.left - self.style["label-left"]["margin"], y=y,
                    text_anchor="end", dominant_baseline="middle", attrib=self.style["label-left"]
                )

    def draw_labels_right(self, skip_last=True):
        label_pairs = list(zip(reversed(self.labels_right), self.y_edges_with_outer()))
        if skip_last:
            del label_pairs[0]
        for scale_text, y in label_pairs:
            if scale_text is not None:
                self.add_text(
                    scale_text, x=self.draw_area.right + self.style["label-right"]["margin"], y=y,
                    text_anchor="end", dominant_baseline="middle", attrib=self.style["label-right"]
                )

    def draw_unit_left(self, unit):
        self.add_text(
            unit, x=self.draw_area.left - self.style["unit-left"]["margin"], y=self.draw_area.top,
            text_anchor="end", dominant_baseline="middle", attrib=self.style["unit-left"]
        )

    def draw_unit_right(self, unit):
        self.add_text(
            unit, x=self.draw_area.right + self.style["unit-right"]["margin"], y=self.draw_area.top,
            dominant_baseline="middle", attrib=self.style["unit-right"]
        )

    def series_style(self, series_name):
        return self.style["series-" + series_name]

    def add_legend(self, name, label=None):
        if label is None:
            label = name
        self.legend[name] = label

    def draw_legend(self):
        center_y = (self.draw_area.top + self.draw_area.bottom) // 2
        num_legends = len(self.legend)
        legend_top = center_y - self.style["legend-text"]["spacing"] * (num_legends / 2)
        for i, (series_name, label) in enumerate(self.legend.items()):
            y = legend_top + i * self.style["legend-text"]["spacing"]
            x_line = self.draw_area.right + self.style["legend-line"]["margin"]
            x_text = x_line + self.style["legend-line"]["width"] + self.style["legend-text"]["margin"]
            self.add_line(
                x1=x_line, y1=y, x2=x_line + self.style["legend-line"]["width"], y2=y,
                stroke=self.series_style(series_name)["stroke"], attrib=self.style["legend-line"]
            )
            self.add_text(
                text=label, x=x_text, y=y, dominant_baseline="middle",
                attrib=self.style["legend-text"]
            )

    def scaler_left(self):
        return self.draw_area.height / self.scale_steps / self.scale_left.step

    def scaler_right(self):
        return self.draw_area.height / self.scale_steps / self.scale_right.step

    def get_scaler(self, side):
        if side == "left":
            return self.scaler_left()
        elif side == "right":
            return self.scaler_right()
        else:
            raise ValueError(f"Invalid side: {side}")

    def get_x_edges(self, x_type):
        if x_type == "edge":
            return self.x_edges_with_outer()
        elif x_type == "between":
            return self.x_edges_between()
        else:
            raise ValueError(f"Invalid x_type: {x_type}")

    def baseline_points(self):
        return [
            f"{self.draw_area.left},{self.baseline_y}",
            f"{self.draw_area.right},{self.baseline_y}"
        ]

    def draw_bars(self, series_name, datapoints, side):
        scaler = self.get_scaler(side)

        for val, (x1, x2) in zip(datapoints, pairs(self.x_edges_with_outer())):
            val_y = self.baseline_y - val * scaler
            command = f"M {x1},{self.baseline_y} {x1},{val_y} {x2},{val_y} {x2},{self.baseline_y}"
            self.add_path(command, attrib=self.series_style(series_name))

    def to_line(self, datapoints, side, x_type):
        scaler = self.get_scaler(side)
        x_vals = self.get_x_edges(x_type)

        points = []
        if x_type == "between":
            wrap_val = (datapoints[0] + datapoints[-1]) / 2
            wrap_y = self.baseline_y - wrap_val * scaler
            points.append(f"{self.draw_area.left},{wrap_y}")
        for val, x in zip(datapoints, x_vals):
            y = self.baseline_y - val * scaler
            points.append(f"{x},{y}")
        if x_type == "between":
            points.append(f"{self.draw_area.right},{wrap_y}")
        return points

    def to_stepped_line(self, datapoints, side):
        scaler = self.get_scaler(side)

        points = []
        for val, (x1, x2) in zip(datapoints, pairs(self.x_edges_with_outer())):
            y = self.baseline_y - val * scaler
            points.append(f"{x1},{y}")
            points.append(f"{x2},{y}")
        return points

    def line_from_xy(self, datapoints, side):
        scaler = self.get_scaler(side)
        points = []
        for x_fract, y_fract in datapoints:
            x = self.draw_area.left + x_fract * self.draw_area.width
            y = self.baseline_y - y_fract * scaler
            points.append(f"{x},{y}")
        return points

    def draw_line(self, series_name, points):
        commands = ["M"] + points
        self.add_path(commands, attrib=self.series_style(series_name))

    def draw_polygon(self, polygon_name, points):
        commands = ["M"] + points + ["Z"]
        self.add_path(commands, attrib=self.style["poly-" + polygon_name])


default_style = {
    "draw-area": {  # all virtual
        "width": 480,
        "height": 400,
        "margin-top": 30,
        "margin-bottom": 70,
        "margin-right": 70,
        "margin-left": 70
    },
    "background": {
        "stroke": "none",
        "fill": "#FFFFFF"
    },
    "border": {
        "stroke": "#000000",
        "stroke-width": 2,
        "fill": "none",
    },
    "subdivision": {
        "stroke": "#000000",
        "stroke-opacity": 0.5,
        "stroke-width": 1,
        "fill": "none"
    },
    "baseline": {
        "stroke": "#000000",
        "stroke-width": 2,
        "fill": "none"
    },
    "label-x": {
        "margin": 30,  # virtual
        "stroke": "none",
        "fill": "#000000",
        "font-size": "18px",
        "font-family": "sans-serif",
        "font-weight": 600
    },
    "unit-x": {
        "stroke": "none",
        "fill": "#000000",
        "font-size": "18px",
        "font-family": "sans-serif",
        "font-weight": 800
    },
    "label-left": {
        "margin": 13,  # virtual
        "stroke": "none",
        "fill": "#000000",
        "font-size": "16px",
        "font-family": "sans-serif",
        "font-weight": 600
    },
    "label-right": {
        "margin": 40,  # virtual
        "stroke": "none",
        "fill": "#000000",
        "font-size": "16px",
        "font-family": "sans-serif",
        "font-weight": 600
    },
    "unit-left": {
        "margin": 13,  # virtual
        "stroke": "none",
        "fill": "#000000",
        "font-size": "18px",
        "font-family": "sans-serif",
        "font-weight": 800
    },
    "unit-right": {
        "margin": 13,  # virtual
        "stroke": "none",
        "fill": "#000000",
        "font-size": "18px",
        "font-family": "sans-serif",
        "font-weight": 800
    },
    "legend-line": {
        "margin": 30,  # virtual
        "width": 15,  # virtual
        "stroke-width": "5",
        "stroke-linecap": "round",
        "fill": "none"
    },
    "legend-text": {
        "margin": 10,  # virtual
        "spacing": 23,  # virtual
        "stroke": "none",
        "fill": "#000000",
        "font-size": "18px",
        "font-family": "sans-serif",
        "font-weight": 600
    }
}

def merge_styles(old, new):
    merged = copy.deepcopy(old)
    for section in new:
        if section in old:
            for key in new[section]:
                merged[section][key] = new[section][key]
        else:
            merged[section] = new[section]
    return merged
