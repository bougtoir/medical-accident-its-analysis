"""院内様式の麻酔記録チャート出力."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Callable, Mapping, Optional, Sequence

import matplotlib

matplotlib.use("Agg")
import matplotlib.colors as mcolors  # noqa: E402
import matplotlib.dates as mdates  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.gridspec import GridSpecFromSubplotSpec  # noqa: E402

from .chart_common import _configure_japanese_font  # noqa: E402
from .cost import CostReport  # noqa: E402
from .drug_master import DrugMasterFile  # noqa: E402
from .events import ClinicalEvent, DEFAULT_EVENT_ICONS  # noqa: E402
from .models import Delivery, MedEvent, Patient  # noqa: E402
from .pkpd import CeResult  # noqa: E402
from .vitals import VitalsTable  # noqa: E402


_configure_japanese_font()


@dataclass(frozen=True)
class VitalPlotStyle:
    """バイタル描画の指定."""

    kind: str = "line"
    color: str = "#2f2f2f"
    marker: Optional[str] = None
    linestyle: str = "-"
    axis: str = "left"


@dataclass(frozen=True)
class VitalAxisSpec:
    """軸スケール・表示位置の指定."""

    key: str
    label: str
    color: str
    ymin: Optional[float] = None
    ymax: Optional[float] = None
    ticks: Optional[Sequence[float]] = None
    side: str = "left"


@dataclass
class FluidBalanceItem:
    """IN/OUT の1項目."""

    label: str
    volume_ml: float


@dataclass
class FluidBalanceSummary:
    """流量収支の事前集計."""

    in_items: list[FluidBalanceItem] = field(default_factory=list)
    out_items: list[FluidBalanceItem] = field(default_factory=list)
    balance_ml: Optional[float] = None


@dataclass(frozen=True)
class BandSpec:
    height: float
    render: Callable[[object], None]
    sharex: bool = True


DEFAULT_VITAL_STYLES: dict[str, VitalPlotStyle] = {
    "HR": VitalPlotStyle(kind="line", color="#a31621", marker="o"),
    "PULSE": VitalPlotStyle(kind="line", color="#a31621", marker="o"),
    "SBP": VitalPlotStyle(kind="symbol", color="#c1121f", marker="v"),
    "NIBP_SYS": VitalPlotStyle(kind="symbol", color="#c1121f", marker="v"),
    "NIBP_SBP": VitalPlotStyle(kind="symbol", color="#c1121f", marker="v"),
    "ABP_SYS": VitalPlotStyle(kind="symbol", color="#c1121f", marker="v"),
    "SYS": VitalPlotStyle(kind="symbol", color="#c1121f", marker="v"),
    "DBP": VitalPlotStyle(kind="symbol", color="#1d4ed8", marker="^"),
    "NIBP_DIA": VitalPlotStyle(kind="symbol", color="#1d4ed8", marker="^"),
    "NIBP_DBP": VitalPlotStyle(kind="symbol", color="#1d4ed8", marker="^"),
    "ABP_DIA": VitalPlotStyle(kind="symbol", color="#1d4ed8", marker="^"),
    "DIA": VitalPlotStyle(kind="symbol", color="#1d4ed8", marker="^"),
    "SPO2": VitalPlotStyle(kind="line", color="#0f766e", marker="o", axis="right"),
    "SpO2": VitalPlotStyle(kind="line", color="#0f766e", marker="o", axis="right"),
    "ETCO2": VitalPlotStyle(kind="line", color="#2563eb", marker="o", axis="right"),
    "EtCO2": VitalPlotStyle(kind="line", color="#2563eb", marker="o", axis="right"),
    "BIS": VitalPlotStyle(kind="line", color="#7c3aed", marker="o", axis="right"),
    "TEMP": VitalPlotStyle(kind="line", color="#d97706", marker="o", axis="right"),
    "Temp": VitalPlotStyle(kind="line", color="#d97706", marker="o", axis="right"),
    "TEMP1": VitalPlotStyle(kind="line", color="#d97706", marker="o", axis="right"),
}

DEFAULT_AXIS_SPECS: list[VitalAxisSpec] = [
    VitalAxisSpec(
        key="BP_HR",
        label="HR / BP",
        color="#4b5563",
        ymin=0,
        ymax=200,
        ticks=[0, 50, 100, 150, 200],
        side="left",
    ),
    VitalAxisSpec(
        key="SPO2",
        label="SpO2",
        color="#0f766e",
        ymin=90,
        ymax=100,
        ticks=[90, 92, 94, 96, 98, 100],
        side="right",
    ),
    VitalAxisSpec(
        key="ETCO2",
        label="EtCO2",
        color="#2563eb",
        ymin=0,
        ymax=60,
        ticks=[0, 10, 20, 30, 40, 50, 60],
        side="right",
    ),
    VitalAxisSpec(
        key="BIS",
        label="BIS",
        color="#7c3aed",
        ymin=0,
        ymax=100,
        ticks=[0, 20, 40, 60, 80, 100],
        side="right",
    ),
    VitalAxisSpec(
        key="TEMP",
        label="Temp",
        color="#d97706",
        ymin=34,
        ymax=40,
        ticks=[34, 35, 36, 37, 38, 39, 40],
        side="right",
    ),
]

_AXIS_GROUP_ALIASES: dict[str, tuple[str, ...]] = {
    "BP_HR": (
        "HR",
        "PULSE",
        "SBP",
        "NIBP_SYS",
        "NIBP_SBP",
        "ABP_SYS",
        "SYS",
        "DBP",
        "NIBP_DIA",
        "NIBP_DBP",
        "ABP_DIA",
        "DIA",
    ),
    "SPO2": ("SPO2", "SpO2", "PLETH_SPO2"),
    "ETCO2": ("ETCO2", "EtCO2", "etCO2", "CO2_ET"),
    "BIS": ("BIS",),
    "TEMP": ("TEMP", "Temp", "TEMP1", "Temperature"),
}

_LATEST_PANEL_LOCATIONS = {
    "upper right": (0.99, 0.98, "right", "top"),
    "upper left": (0.01, 0.98, "left", "top"),
    "lower right": (0.99, 0.02, "right", "bottom"),
    "lower left": (0.01, 0.02, "left", "bottom"),
}


def render_chart_erga(
    vitals: VitalsTable,
    events: Sequence[MedEvent],
    master: DrugMasterFile,
    out_path: str,
    patient: Optional[Patient] = None,
    header_meta: Optional[Mapping[str, str]] = None,
    clinical_events: Optional[Sequence[ClinicalEvent]] = None,
    fluids: Optional[FluidBalanceSummary] = None,
    cost_report: Optional[CostReport] = None,
    ce_results: Optional[dict[str, CeResult]] = None,
    ce_t0: Optional[datetime] = None,
    show_floating_latest: bool = False,
    latest_panel_loc: str = "upper right",
    latest_stale_threshold_min: float = 5.0,
    axis_specs: Optional[Sequence[VitalAxisSpec]] = None,
    window: Optional[tuple[datetime, datetime]] = None,
    window_minutes: Optional[float] = None,
    tick_interval_min: Optional[float] = None,
    ce_window: Optional[tuple[datetime, datetime]] = None,
    ce_horizon_min: float = 60.0,
    event_icon_map: Optional[Mapping[str, str]] = None,
    vital_style_map: Optional[Mapping[str, VitalPlotStyle]] = None,
    title: str = "麻酔記録",
) -> str:
    """院内様式の印刷チャートを描画して保存する."""

    style_map = dict(DEFAULT_VITAL_STYLES)
    if vital_style_map:
        style_map.update(vital_style_map)
    icon_map = dict(DEFAULT_EVENT_ICONS)
    if event_icon_map:
        icon_map.update(event_icon_map)

    axis_spec_list = list(axis_specs or DEFAULT_AXIS_SPECS)
    axis_spec_map = {spec.key: spec for spec in axis_spec_list}
    main_window = _resolve_main_window(vitals, events, clinical_events, window, window_minutes)
    ce_window_resolved = _resolve_ce_window(main_window, ce_window, ce_horizon_min)
    ordered_events = _sorted_events(events)
    clinical_sorted = sorted(list(clinical_events or []), key=lambda e: e.time)
    drug_rows = _drug_rows(ordered_events, master)

    bands: list[BandSpec] = [
        BandSpec(
            0.62,
            lambda ax: _render_header(ax, patient, header_meta, title, main_window),
            sharex=False,
        ),
        BandSpec(
            2.45,
            lambda ax: _render_vitals(
                ax,
                vitals,
                style_map,
                axis_spec_list,
                axis_spec_map,
                icon_map,
                clinical_sorted,
                show_floating_latest,
                latest_panel_loc,
                latest_stale_threshold_min,
                main_window,
                tick_interval_min,
            ),
        ),
    ]
    for lane in drug_rows:
        bands.append(BandSpec(0.36, lambda ax, lane=lane: _render_drug_lane(ax, lane, master, main_window)))
    if clinical_sorted:
        bands.append(BandSpec(0.88, lambda ax: _render_events_band(ax, clinical_sorted, main_window)))
    if fluids is not None:
        bands.append(BandSpec(0.7, lambda ax: _render_fluids(ax, fluids), sharex=False))
    if cost_report is not None:
        bands.append(BandSpec(0.8, lambda ax: _render_cost(ax, cost_report), sharex=False))
    if ce_results:
        bands.append(
            BandSpec(
                1.15,
                lambda ax: _render_ce(ax, ce_results, master, ce_t0, main_window, ce_window_resolved, tick_interval_min),
                sharex=False,
            )
        )

    fig = plt.figure(figsize=(11.69, 8.27))
    right_margin = max(0.68, 0.96 - 0.08 * sum(1 for spec in axis_spec_list if spec.side == "right"))
    fig.subplots_adjust(left=0.05, right=right_margin, top=0.97, bottom=0.04)
    gs = fig.add_gridspec(len(bands), 1, height_ratios=[b.height for b in bands])

    axes: list[object] = []
    ax_main = None
    last_shared_index = max((i for i, b in enumerate(bands) if b.sharex), default=0)
    for idx, band in enumerate(bands):
        if idx == 0:
            ax = fig.add_subplot(gs[idx, 0])
        elif band.sharex and ax_main is not None:
            ax = fig.add_subplot(gs[idx, 0], sharex=ax_main)
        else:
            ax = fig.add_subplot(gs[idx, 0])
        if idx == 1:
            ax_main = ax
        band.render(ax)
        if band.sharex and idx < last_shared_index:
            ax.tick_params(labelbottom=False)
        axes.append(ax)

    if ax_main is not None:
        _apply_tick_interval(ax_main, tick_interval_min)
    if ce_results:
        ce_ax = axes[-1]
        _apply_tick_interval(ce_ax, tick_interval_min)

    fig.tight_layout(h_pad=0.35)
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    return out_path


def _sorted_events(events: Sequence[MedEvent]) -> list[MedEvent]:
    out = list(events)
    out.sort(key=lambda e: (e.start_time, e.drug_id, e.delivery.value))
    return out


@dataclass
class DrugLane:
    drug_id: str
    label: str
    events: list[MedEvent]
    has_infusion: bool
    first_time: datetime


def _drug_rows(events: Sequence[MedEvent], master: DrugMasterFile) -> list[DrugLane]:
    grouped: dict[str, list[MedEvent]] = {}
    for ev in events:
        grouped.setdefault(ev.drug_id, []).append(ev)
    rows: list[DrugLane] = []
    for drug_id, evs in grouped.items():
        drug = master.get(drug_id)
        label = f"{drug.generic_name} ({drug.container_volume_ml:g}mL/{drug.concentration:g}{drug.strength_unit})"
        rows.append(
            DrugLane(
                drug_id=drug_id,
                label=label,
                events=sorted(evs, key=lambda e: (e.start_time, e.delivery.value)),
                has_infusion=any(ev.delivery is Delivery.INFUSION for ev in evs),
                first_time=min(ev.start_time for ev in evs),
            )
        )
    rows.sort(key=lambda lane: (not lane.has_infusion, lane.first_time, lane.label))
    return rows


def _resolve_main_window(
    vitals: VitalsTable,
    events: Sequence[MedEvent],
    clinical_events: Optional[Sequence[ClinicalEvent]],
    window: Optional[tuple[datetime, datetime]],
    window_minutes: Optional[float],
) -> tuple[datetime, datetime]:
    base_start, base_end = _infer_bounds(vitals, events, clinical_events or [])
    if window is not None:
        return window
    if window_minutes is not None:
        end = base_end
        start = end - timedelta(minutes=window_minutes)
        if start >= end:
            start = end - timedelta(minutes=1)
        return start, end
    return base_start, base_end


def _resolve_ce_window(
    main_window: tuple[datetime, datetime],
    ce_window: Optional[tuple[datetime, datetime]],
    ce_horizon_min: float,
) -> tuple[datetime, datetime]:
    if ce_window is not None:
        return ce_window
    start, end = main_window
    return start, end + timedelta(minutes=ce_horizon_min)


def _infer_bounds(
    vitals: VitalsTable,
    events: Sequence[MedEvent],
    clinical_events: Sequence[ClinicalEvent],
) -> tuple[datetime, datetime]:
    times: list[datetime] = []
    for series in vitals.parameters.values():
        times.extend(series.times)
    for ev in events:
        times.append(ev.start_time)
        if ev.end_time is not None:
            times.append(ev.end_time)
    for ev in clinical_events:
        times.append(ev.time)
    if not times:
        now = datetime.now()
        return now, now + timedelta(minutes=1)
    start = min(times)
    end = max(times)
    if end <= start:
        end = start + timedelta(minutes=1)
    return start, end


def _render_header(
    ax,
    patient: Optional[Patient],
    header_meta: Optional[Mapping[str, str]],
    title: str,
    bounds: tuple[datetime, datetime],
) -> None:
    ax.axis("off")
    start, _ = bounds
    values: list[str] = [title, start.strftime("%Y-%m-%d")]
    if patient is not None:
        if patient.patient_id:
            values.append(str(patient.patient_id))
        if patient.age_years is not None:
            values.append(f"{patient.age_years:g}歳")
        if patient.sex is not None:
            values.append("男" if patient.sex.value == "male" else "女")
        if patient.weight_kg is not None:
            values.append(f"{patient.weight_kg:g} kg")
        if patient.height_cm is not None:
            values.append(f"{patient.height_cm:g} cm")
        if patient.asa_ps is not None:
            values.append(f"ASA {patient.asa_ps}")
    if header_meta:
        for key in ("name", "dept", "diagnosis", "procedure", "blood_type", "position", "anesthesia_method"):
            value = header_meta.get(key)
            if value:
                values.append(value)
    lines = _wrap_values(values, max_items_per_line=6)
    ax.text(0.01, 0.92, "\n".join(lines), ha="left", va="top", fontsize=9, transform=ax.transAxes)


def _wrap_values(values: Sequence[str], max_items_per_line: int) -> list[str]:
    if not values:
        return [""]
    lines: list[str] = []
    for i in range(0, len(values), max_items_per_line):
        lines.append("  ".join(values[i : i + max_items_per_line]))
    return lines


def _render_vitals(
    ax,
    vitals: VitalsTable,
    style_map: Mapping[str, VitalPlotStyle],
    axis_specs: Sequence[VitalAxisSpec],
    axis_spec_map: Mapping[str, VitalAxisSpec],
    icon_map: Mapping[str, str],
    clinical_events: Sequence[ClinicalEvent],
    show_floating_latest: bool,
    latest_panel_loc: str,
    latest_stale_threshold_min: float,
    bounds: tuple[datetime, datetime],
    tick_interval_min: Optional[float],
) -> None:
    ax.set_xlim(bounds[0], bounds[1])
    ax.grid(True, ls=":", alpha=0.45)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(True)
    ax.set_ylabel(axis_spec_map.get("BP_HR", DEFAULT_AXIS_SPECS[0]).label)
    _apply_axis_style(ax, axis_spec_map.get("BP_HR", DEFAULT_AXIS_SPECS[0]), main=True)

    series_groups = _group_series_by_axis(vitals, axis_specs)
    right_keys = [spec.key for spec in axis_specs if spec.side == "right" and spec.key in series_groups]
    for offset, key in enumerate(right_keys, start=1):
        spec = axis_spec_map[key]
        twin = ax.twinx()
        twin.spines["right"].set_position(("outward", 48 * offset))
        _apply_axis_style(twin, spec, main=False)
        _plot_axis_group(twin, key, series_groups[key], style_map)

    if "BP_HR" in series_groups:
        _plot_axis_group(ax, "BP_HR", series_groups["BP_HR"], style_map)
    for key, items in series_groups.items():
        if key in {"BP_HR", *right_keys}:
            continue
        _plot_axis_group(ax, key, items, style_map)

    _render_event_icons(ax, clinical_events, icon_map)
    if show_floating_latest:
        _render_latest_panel(ax, vitals, style_map, latest_panel_loc, latest_stale_threshold_min)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    if tick_interval_min is not None:
        _apply_tick_interval(ax, tick_interval_min)


def _group_series_by_axis(
    vitals: VitalsTable,
    axis_specs: Sequence[VitalAxisSpec],
) -> dict[str, list[tuple[str, object]]]:
    groups: dict[str, list[tuple[str, object]]] = {}
    for name, series in vitals.parameters.items():
        key = _axis_key_for_series(name, axis_specs)
        if key is None:
            key = "__main__"
        groups.setdefault(key, []).append((name, series))
    return groups


def _axis_key_for_series(name: str, axis_specs: Sequence[VitalAxisSpec]) -> Optional[str]:
    norm = _normalize(name)
    for spec in axis_specs:
        if _normalize(spec.key) == norm or _normalize(spec.label) == norm:
            return spec.key
    for key, aliases in _AXIS_GROUP_ALIASES.items():
        for alias in aliases:
            if _normalize(alias) == norm:
                return key
    return None


def _apply_axis_style(ax, spec: VitalAxisSpec, main: bool) -> None:
    color = spec.color
    side = spec.side
    if main:
        spine = ax.spines["left"]
    else:
        spine = ax.spines["right"]
    spine.set_color(color)
    ax.yaxis.label.set_color(color)
    ax.tick_params(axis="y", colors=color, labelsize=8)
    if spec.ymin is not None or spec.ymax is not None:
        ax.set_ylim(spec.ymin, spec.ymax)
    if spec.ticks is not None:
        ax.set_yticks(list(spec.ticks))
    if not main:
        ax.spines["left"].set_visible(False)
    ax.set_ylabel(spec.label)
    if side == "left":
        ax.yaxis.tick_left()
        ax.yaxis.set_label_position("left")
    else:
        ax.yaxis.tick_right()
        ax.yaxis.set_label_position("right")


def _plot_axis_group(
    ax,
    axis_key: str,
    items: Sequence[tuple[str, object]],
    style_map: Mapping[str, VitalPlotStyle],
) -> None:
    all_values: list[float] = []
    for name, series in items:
        style = _pick_vital_style(name, style_map)
        xs = [t for t, v in zip(series.times, series.values) if v is not None]
        ys = [float(v) for v in series.values if v is not None]
        all_values.extend(ys)
        if not xs:
            continue
        if style.kind == "symbol":
            ax.scatter(xs, ys, s=18, marker=style.marker or "o", color=style.color, label=name)
        else:
            ax.plot(xs, ys, linestyle=style.linestyle, marker=style.marker, ms=3, lw=0.9, color=style.color, label=name)
    if axis_key == "__main__" and all_values:
        ymin, ymax = min(all_values), max(all_values)
        if ymin == ymax:
            ymin -= 1
            ymax += 1
        pad = max((ymax - ymin) * 0.1, 1.0)
        ax.set_ylim(ymin - pad, ymax + pad)


def _render_event_icons(
    ax,
    events: Sequence[ClinicalEvent],
    icon_map: Mapping[str, str],
) -> None:
    for ev in events:
        icon = ev.icon or icon_map.get(ev.type, DEFAULT_EVENT_ICONS.get(ev.type, "◆"))
        ax.text(
            ev.time,
            0.01,
            icon,
            transform=ax.get_xaxis_transform(),
            ha="center",
            va="bottom",
            fontsize=8,
            color="#222222",
            clip_on=True,
        )


def _latest_non_missing_point(series) -> tuple[Optional[float], Optional[datetime]]:
    for time, value in reversed(list(zip(series.times, series.values))):
        if value is not None:
            return float(value), time
    return None, None


def _latest_reference_time(vitals: VitalsTable) -> Optional[datetime]:
    latest: Optional[datetime] = None
    for series in vitals.parameters.values():
        if series.times:
            series_latest = max(series.times)
            if latest is None or series_latest > latest:
                latest = series_latest
    return latest


def _render_latest_panel(
    ax,
    vitals: VitalsTable,
    style_map: Mapping[str, VitalPlotStyle],
    latest_panel_loc: str,
    latest_stale_threshold_min: float,
) -> None:
    x, y, ha, va = _LATEST_PANEL_LOCATIONS.get(latest_panel_loc, _LATEST_PANEL_LOCATIONS["upper right"])
    ref_time = _latest_reference_time(vitals)
    threshold = timedelta(minutes=latest_stale_threshold_min)
    entries: list[tuple[str, str, str]] = []

    bp_sys = _latest_point_for(vitals, ("SBP", "NIBP_SYS", "NIBP_SBP", "ABP_SYS", "SYS"))
    bp_dia = _latest_point_for(vitals, ("DBP", "NIBP_DIA", "NIBP_DBP", "ABP_DIA", "DIA"))
    if bp_sys[0] is not None and bp_dia[0] is not None:
        bp_time = max(t for t in (bp_sys[1], bp_dia[1]) if t is not None)
        color = _series_color_for_group(vitals, style_map, ("SBP", "NIBP_SYS", "NIBP_SBP", "ABP_SYS", "SYS"))
        if _is_stale(bp_time, ref_time, threshold):
            color = _dim_color(color)
        entries.append(("BP", f"{int(round(bp_sys[0]))}/{int(round(bp_dia[0]))}", color))

    for key_group in (("HR", "PULSE"), ("SPO2", "SpO2"), ("ETCO2", "EtCO2"), ("BIS",), ("TEMP", "TEMP1")):
        latest, latest_time = _latest_point_for(vitals, key_group)
        if latest is None or latest_time is None:
            continue
        color = _series_color_for_group(vitals, style_map, key_group)
        if _is_stale(latest_time, ref_time, threshold):
            color = _dim_color(color)
        label = _latest_panel_label(key_group)
        entries.append((label, _format_latest_panel_value(label, latest), color))

    if not entries:
        return

    width = 0.31
    height = min(0.40, max(0.18, 0.07 * len(entries) + 0.08))
    pad = 0.02
    if ha == "right":
        left = x - width - pad
    else:
        left = x + pad
    if va == "top":
        bottom = y - height - pad
    else:
        bottom = y + pad
    left = min(max(left, 0.01), 0.99 - width)
    bottom = min(max(bottom, 0.01), 0.99 - height)
    inset = ax.inset_axes([left, bottom, width, height], transform=ax.transAxes, zorder=20)
    inset.set_xticks([])
    inset.set_yticks([])
    inset.tick_params(left=False, bottom=False, labelleft=False, labelbottom=False)
    for spine in inset.spines.values():
        spine.set_visible(True)
    inset.set_facecolor("white")
    inset.patch.set_edgecolor("#999999")
    inset.patch.set_alpha(0.98)
    inset.patch.set_linewidth(1.0)
    line_step = 0.86 / max(len(entries), 1)
    for idx, (_, value, color) in enumerate(entries):
        inset.text(
            0.08,
            0.92 - idx * line_step,
            value,
            ha="left",
            va="top",
            fontsize=12,
            color=color,
        )


def _latest_point_for(
    vitals: VitalsTable,
    key_group: tuple[str, ...],
) -> tuple[Optional[float], Optional[datetime]]:
    for key in key_group:
        series = _get_series_case_insensitive(vitals, key)
        if series is None:
            continue
        value, time = _latest_non_missing_point(series)
        if value is not None and time is not None:
            return value, time
    return None, None


def _series_color_for_group(
    vitals: VitalsTable,
    style_map: Mapping[str, VitalPlotStyle],
    key_group: tuple[str, ...],
) -> str:
    for key in key_group:
        series = _get_series_case_insensitive(vitals, key)
        if series is not None:
            style = _pick_vital_style(key, style_map)
            return style.color
    return "#2f2f2f"


def _latest_panel_label(key_group: tuple[str, ...]) -> str:
    normalized = tuple(_normalize(key) for key in key_group)
    return {
        ("HR", "PULSE"): "HR",
        ("SPO2", "SPO2"): "SpO2",
        ("ETCO2", "ETCO2"): "EtCO2",
        ("BIS",): "BIS",
        ("TEMP", "TEMP1"): "Temp",
    }[normalized]


def _format_latest_panel_value(label: str, value: float) -> str:
    if label == "Temp":
        return f"{value:.1f}"
    return f"{int(round(value))}"


def _get_series_case_insensitive(vitals: VitalsTable, key: str):
    target = _normalize(key)
    for name, series in vitals.parameters.items():
        if _normalize(name) == target:
            return series
    return None


def _is_stale(value_time: Optional[datetime], reference_time: Optional[datetime], threshold: timedelta) -> bool:
    if value_time is None or reference_time is None:
        return False
    return reference_time - value_time > threshold


def _dim_color(color: str) -> str:
    r, g, b = mcolors.to_rgb(color)
    blended = (1.0 - (1.0 - r) * 0.45, 1.0 - (1.0 - g) * 0.45, 1.0 - (1.0 - b) * 0.45)
    return mcolors.to_hex(blended)


def _pick_vital_style(name: str, style_map: Mapping[str, VitalPlotStyle]) -> VitalPlotStyle:
    key = _normalize(name)
    if name in style_map:
        return style_map[name]
    for candidate, style in style_map.items():
        if _normalize(candidate) == key:
            return style
    return VitalPlotStyle()


def _normalize(name: str) -> str:
    return "".join(ch for ch in name.upper() if ch.isalnum())


def _apply_tick_interval(ax, tick_interval_min: Optional[float]) -> None:
    if tick_interval_min is None:
        return
    interval = max(1, int(round(tick_interval_min)))
    locator = mdates.MinuteLocator(interval=interval)
    ax.xaxis.set_major_locator(locator)


def _render_drug_lane(
    ax,
    lane: DrugLane,
    master: DrugMasterFile,
    bounds: tuple[datetime, datetime],
) -> None:
    ax.set_xlim(bounds[0], bounds[1])
    ax.set_ylim(0, 1)
    ax.set_yticks([])
    ax.grid(True, axis="x", ls=":", alpha=0.25)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.text(0.01, 0.5, lane.label, ha="left", va="center", fontsize=8, transform=ax.transAxes)
    for ev in lane.events:
        if ev.delivery is Delivery.BOLUS:
            label = _format_dose_event(ev)
            ax.annotate(
                label,
                xy=(ev.start_time, 0.78),
                xycoords=("data", "axes fraction"),
                ha="center",
                va="bottom",
                fontsize=8,
                color="#222222",
                bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.85, "pad": 0.2},
            )
            ax.axvline(ev.start_time, ymin=0.18, ymax=0.86, color="#222222", lw=0.6, alpha=0.45)
        else:
            end_time = ev.end_time or bounds[1]
            ax.hlines(0.55, ev.start_time, end_time, color="#222222", lw=1.4, alpha=0.7)
            ax.text(
                (ev.start_time + (end_time - ev.start_time) / 2),
                0.78,
                _format_rate_event(ev, master),
                ha="center",
                va="bottom",
                fontsize=7.5,
                color="#222222",
                bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.85, "pad": 0.2},
            )
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))


def _format_dose_event(ev: MedEvent) -> str:
    parts = []
    if ev.dose is not None:
        parts.append(f"{ev.dose:g}")
        if ev.dose_unit:
            parts[-1] += ev.dose_unit
    return "".join(parts) if parts else ""


def _format_rate_event(ev: MedEvent, master: DrugMasterFile) -> str:
    if ev.rate is None:
        return ""
    txt = f"{ev.rate:g}"
    if ev.rate_unit:
        txt += ev.rate_unit
    return txt


def _render_events_band(
    ax,
    events: Sequence[ClinicalEvent],
    bounds: tuple[datetime, datetime],
) -> None:
    ax.axis("off")
    sub = GridSpecFromSubplotSpec(1, 2, subplot_spec=ax.get_subplotspec(), width_ratios=[3.5, 1.6])
    strip = ax.figure.add_subplot(sub[0, 0])
    log = ax.figure.add_subplot(sub[0, 1])
    _render_clinical_strip(strip, events, bounds)
    _render_event_log(log, events)


def _render_clinical_strip(
    ax,
    events: Sequence[ClinicalEvent],
    bounds: tuple[datetime, datetime],
) -> None:
    ax.set_xlim(bounds[0], bounds[1])
    ax.set_ylim(0, 1)
    ax.set_yticks([])
    ax.grid(True, axis="x", ls=":", alpha=0.25)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.set_ylabel("イベント", fontsize=8)
    for idx, ev in enumerate(events, start=1):
        ax.axvline(ev.time, color="#222222", lw=0.8, alpha=0.65)
        ax.text(ev.time, 0.18, str(idx), ha="center", va="bottom", fontsize=7, color="#111111")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    ax.tick_params(axis="x", labelsize=8)


def _render_event_log(ax, events: Sequence[ClinicalEvent]) -> None:
    ax.axis("off")
    lines = [f"{idx}. {ev.time:%H:%M} {ev.display_label}" for idx, ev in enumerate(events, start=1)]
    ax.text(0.0, 1.0, "\n".join(lines) if lines else " ", ha="left", va="top", fontsize=7.5)


def _render_fluids(ax, fluids: FluidBalanceSummary) -> None:
    ax.axis("off")
    lines = ["IN/OUT"]
    if fluids.in_items:
        lines.append("IN")
        for item in fluids.in_items:
            lines.append(f"  {item.label}: {item.volume_ml:g} mL")
    if fluids.out_items:
        lines.append("OUT")
        for item in fluids.out_items:
            lines.append(f"  {item.label}: {item.volume_ml:g} mL")
    if fluids.balance_ml is not None:
        lines.append(f"Balance: {fluids.balance_ml:g} mL")
    ax.text(0.01, 0.9, "\n".join(lines), ha="left", va="top", fontsize=8, transform=ax.transAxes)


def _render_cost(ax, cost_report: CostReport) -> None:
    ax.axis("off")
    lines = ["COST"]
    for item in cost_report.items:
        price = "N/A" if item.cost is None else f"{item.cost:.0f} 円"
        lines.append(f"{item.generic_name}: {price}")
    lines.append(f"Total: {cost_report.total:.0f} 円")
    ax.text(0.01, 0.9, "\n".join(lines), ha="left", va="top", fontsize=8, transform=ax.transAxes)


def _render_ce(
    ax,
    ce_results: dict[str, CeResult],
    master: DrugMasterFile,
    ce_t0: Optional[datetime],
    main_window: tuple[datetime, datetime],
    ce_window: tuple[datetime, datetime],
    tick_interval_min: Optional[float],
) -> None:
    ax.grid(True, ls=":", alpha=0.45)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    if ce_t0 is None:
        ax.axis("off")
        return
    ax.set_xlim(ce_window)
    if tick_interval_min is not None:
        _apply_tick_interval(ax, tick_interval_min)
    end_main = main_window[1]
    ax.axvline(end_main, color="#666666", ls="--", lw=0.8)
    ax.text(end_main, 0.97, "実測/予測", transform=ax.get_xaxis_transform(), ha="center", va="top", fontsize=7, color="#444444")
    for drug_id, res in ce_results.items():
        xs = [ce_t0 + timedelta(minutes=m) for m in res.times_min]
        label = f"{master.get(drug_id).generic_name} Ce ({res.conc_unit})"
        ax.plot(xs, res.ce, lw=0.9, label=label)
    ax.set_ylabel("Ce")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    ax.legend(loc="upper right", fontsize=8)
