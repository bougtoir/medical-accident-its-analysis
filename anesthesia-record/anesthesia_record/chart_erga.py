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


DEFAULT_VITAL_STYLES: dict[str, VitalPlotStyle] = {
    "HR": VitalPlotStyle(kind="line", color="#a31621", marker="o"),
    "PULSE": VitalPlotStyle(kind="line", color="#a31621", marker="o"),
    "SBP": VitalPlotStyle(kind="symbol", color="#c1121f", marker="v"),
    "ABP_SYS": VitalPlotStyle(kind="symbol", color="#c1121f", marker="v"),
    "SYS": VitalPlotStyle(kind="symbol", color="#c1121f", marker="v"),
    "DBP": VitalPlotStyle(kind="symbol", color="#1d4ed8", marker="^"),
    "ABP_DIA": VitalPlotStyle(kind="symbol", color="#1d4ed8", marker="^"),
    "DIA": VitalPlotStyle(kind="symbol", color="#1d4ed8", marker="^"),
    "SPO2": VitalPlotStyle(kind="line", color="#0f766e", marker="o", axis="right"),
    "BIS": VitalPlotStyle(kind="line", color="#7c3aed", marker="o", axis="right"),
    "ETCO2": VitalPlotStyle(kind="line", color="#0f766e", marker="o"),
    "TEMP": VitalPlotStyle(kind="line", color="#d97706", marker="o"),
    "TEMP1": VitalPlotStyle(kind="line", color="#d97706", marker="o"),
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

    ordered_events = _sorted_events(events)
    clinical_sorted = list(clinical_events or [])
    clinical_sorted.sort(key=lambda e: e.time)
    bounds = _infer_bounds(vitals, ordered_events, clinical_sorted, ce_results, ce_t0)
    drug_rows = _drug_rows(ordered_events, master)

    bands: list[tuple[float, Callable[[object], None]]] = []
    bands.append(
        (
            2.5,
            lambda ax: _render_vitals(
                ax,
                vitals,
                style_map,
                icon_map,
                clinical_sorted,
                show_floating_latest,
                latest_panel_loc,
                latest_stale_threshold_min,
                bounds,
            ),
        )
    )
    for lane in drug_rows:
        bands.append((0.36, lambda ax, lane=lane: _render_drug_lane(ax, lane, master, bounds)))
    if clinical_sorted:
        bands.append((0.85, lambda ax: _render_clinical_band(ax, clinical_sorted, bounds)))
    if fluids is not None:
        bands.append((0.7, lambda ax: _render_fluids(ax, fluids)))
    if cost_report is not None:
        bands.append((0.8, lambda ax: _render_cost(ax, cost_report)))
    if ce_results:
        bands.append((1.1, lambda ax: _render_ce(ax, ce_results, master, ce_t0)))

    total_units = 0.62 + sum(height for height, _ in bands)
    fig_height = max(8.27, total_units * 1.15 + 0.8)
    fig = plt.figure(figsize=(11.69, fig_height))
    gs = fig.add_gridspec(1 + len(bands), 1, height_ratios=[0.62] + [height for height, _ in bands])

    ax_header = fig.add_subplot(gs[0, 0])
    _render_header(ax_header, patient, header_meta, title, bounds)

    ax_v = fig.add_subplot(gs[1, 0])
    bands[0][1](ax_v)
    for idx, (_, render) in enumerate(bands[1:], start=2):
        ax = fig.add_subplot(gs[idx, 0], sharex=ax_v)
        render(ax)

    for ax in fig.axes:
        if ax is ax_header:
            continue
        try:
            if ax.get_subplotspec().is_last_row():
                continue
        except Exception:
            pass
        if ax.get_shared_x_axes().joined(ax, ax_v):
            ax.tick_params(labelbottom=False)

    fig.subplots_adjust(
        left=0.13, right=0.9, top=0.98, bottom=0.05, hspace=0.55
    )
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
        label = drug.generic_name
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


def _render_drug_lane(
    ax,
    lane: "DrugLane",
    master: DrugMasterFile,
    bounds: tuple[datetime, datetime],
) -> None:
    ax.set_xlim(bounds[0], bounds[1])
    ax.set_ylim(0, 1)
    ax.set_yticks([])
    ax.grid(True, axis="x", ls=":", alpha=0.25)
    for sp in ("top", "right", "left"):
        ax.spines[sp].set_visible(False)
    ax.set_ylabel(lane.label, rotation=0, ha="right", va="center", fontsize=7)
    ax.tick_params(axis="x", labelbottom=False)
    for ev in lane.events:
        if ev.delivery is Delivery.INFUSION:
            end = ev.end_time or bounds[1]
            ax.hlines(0.5, ev.start_time, end, color="#444444", lw=1.4)
            rate = "" if ev.rate is None else f"{ev.rate:g}{ev.rate_unit or ''}"
            ax.text(
                ev.start_time, 0.62, rate, ha="left", va="bottom",
                fontsize=7, color="#111111",
            )
        else:
            dose = "" if ev.dose is None else f"{ev.dose:g}{ev.dose_unit or ''}"
            ax.plot([ev.start_time], [0.5], marker="v", ms=4, color="#444444")
            ax.text(
                ev.start_time, 0.62, dose, ha="center", va="bottom",
                fontsize=7, color="#111111",
            )
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))


def _infer_bounds(
    vitals: VitalsTable,
    events: Sequence[MedEvent],
    clinical_events: Sequence[ClinicalEvent],
    ce_results: Optional[dict[str, CeResult]],
    ce_t0: Optional[datetime],
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
    if ce_results and ce_t0 is not None:
        for res in ce_results.values():
            if res.times_min:
                times.append(ce_t0 + timedelta(minutes=min(res.times_min)))
                times.append(ce_t0 + timedelta(minutes=max(res.times_min)))
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
    lines = [title, f"日付: {start:%Y-%m-%d}"]
    if patient is not None:
        fields = [
            ("ID", patient.patient_id),
            ("年齢", f"{patient.age_years:g}歳"),
            ("性別", "男" if patient.sex.value == "male" else "女"),
            ("体重", f"{patient.weight_kg:g} kg"),
            ("身長", f"{patient.height_cm:g} cm"),
            ("ASA", None if patient.asa_ps is None else f"{patient.asa_ps}"),
        ]
        for key, value in fields:
            if value is not None:
                lines.append(f"{key}: {value}")
    if header_meta:
        for key in (
            "name",
            "dept",
            "diagnosis",
            "procedure",
            "blood_type",
            "position",
            "anesthesia_method",
        ):
            value = header_meta.get(key)
            if value:
                lines.append(f"{_jp_header_key(key)}: {value}")
    ax.text(
        0.01, 0.92, "\n".join(lines), ha="left", va="top", fontsize=9,
        transform=ax.transAxes,
    )


def _jp_header_key(key: str) -> str:
    return {
        "name": "氏名",
        "dept": "診療科",
        "diagnosis": "診断",
        "procedure": "術式",
        "blood_type": "血液型",
        "position": "体位",
        "anesthesia_method": "麻酔法",
    }.get(key, key)


def _render_vitals(
    ax,
    vitals: VitalsTable,
    style_map: Mapping[str, VitalPlotStyle],
    icon_map: Mapping[str, str],
    clinical_events: Sequence[ClinicalEvent],
    show_floating_latest: bool,
    latest_panel_loc: str,
    latest_stale_threshold_min: float,
    bounds: tuple[datetime, datetime],
) -> None:
    ax.set_xlim(bounds[0], bounds[1])
    ax.grid(True, ls=":", alpha=0.45)
    ax.spines["top"].set_visible(False)
    right = ax.twinx()
    right.spines["top"].set_visible(False)
    right_params: list[str] = []
    for name, series in vitals.parameters.items():
        style = _pick_vital_style(name, style_map)
        target = right if style.axis == "right" else ax
        if style.axis == "right":
            right_params.append(name)
        _plot_vital_series(target, name, series, style)
    _render_event_icons(ax, clinical_events, icon_map)
    if show_floating_latest:
        _render_latest_panel(
            ax,
            vitals,
            style_map,
            latest_panel_loc,
            latest_stale_threshold_min,
        )
    ax.set_ylabel("バイタル")
    if right_params:
        right.set_ylabel("/".join(right_params))
    right.tick_params(axis="y", labelsize=8)
    ax.tick_params(axis="y", labelsize=8)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    ax.tick_params(axis="x", labelbottom=False)
    handles, labels = ax.get_legend_handles_labels()
    r_handles, r_labels = right.get_legend_handles_labels()
    if handles or r_handles:
        ax.legend(
            handles + r_handles,
            labels + r_labels,
            loc="upper left",
            fontsize=8,
            ncol=2,
        )


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
            return value, time
    return None, None


def _latest_reference_time(vitals: VitalsTable) -> Optional[datetime]:
    latest: Optional[datetime] = None
    for series in vitals.parameters.values():
        if series.times:
            t = max(series.times)
            if latest is None or t > latest:
                latest = t
    return latest


def _render_latest_panel(
    ax,
    vitals: VitalsTable,
    style_map: Mapping[str, VitalPlotStyle],
    latest_panel_loc: str,
    latest_stale_threshold_min: float,
) -> None:
    x, y, ha, va = _LATEST_PANEL_LOCATIONS.get(
        latest_panel_loc, _LATEST_PANEL_LOCATIONS["upper right"]
    )
    ref_time = _latest_reference_time(vitals)
    threshold = timedelta(minutes=latest_stale_threshold_min)
    entries: list[tuple[str, str, str]] = []

    bp_sys = _latest_point_for(vitals, ("SBP", "ABP_SYS", "SYS"))
    bp_dia = _latest_point_for(vitals, ("DBP", "ABP_DIA", "DIA"))
    if bp_sys[0] is not None and bp_dia[0] is not None:
        bp_time = max(t for t in (bp_sys[1], bp_dia[1]) if t is not None)
        color = _series_color(vitals, style_map, ("SBP", "ABP_SYS", "SYS"))
        if _is_stale(bp_time, ref_time, threshold):
            color = _dim_color(color)
        entries.append(("BP", f"{bp_sys[0]:g}/{bp_dia[0]:g}", color))

    for key_group in (("HR", "PULSE"), ("SPO2",), ("BIS",), ("ETCO2",), ("TEMP", "TEMP1")):
        latest, latest_time = _latest_point_for(vitals, key_group)
        if latest is None or latest_time is None:
            continue
        label = _panel_label(key_group)
        color = _series_color(vitals, style_map, key_group)
        if _is_stale(latest_time, ref_time, threshold):
            color = _dim_color(color)
        entries.append((label, f"{latest:g}", color))

    if not entries:
        return

    line_step = 0.1
    if va == "top":
        y0 = y
        dy = -line_step
        text_va = "top"
    else:
        y0 = y
        dy = line_step
        text_va = "bottom"

    for idx, (label, value, color) in enumerate(entries):
        ax.text(
            x,
            y0 + idx * dy,
            f"{label} {value}",
            transform=ax.transAxes,
            ha=ha,
            va=text_va,
            fontsize=7,
            color=color,
            bbox={
                "boxstyle": "round,pad=0.18",
                "facecolor": "white",
                "alpha": 0.82,
                "edgecolor": color,
            },
        )


def _latest_point_for(
    vitals: VitalsTable,
    key_group: tuple[str, ...],
) -> tuple[Optional[float], Optional[datetime]]:
    for key in key_group:
        series = _get_series_ci(vitals, key)
        if series is None:
            continue
        value, time = _latest_non_missing_point(series)
        if value is not None and time is not None:
            return value, time
    return None, None


def _get_series_ci(vitals: VitalsTable, name: str):
    series = vitals.parameters.get(name)
    if series is not None:
        return series
    target = _normalize_vital_name(name)
    for cand, series in vitals.parameters.items():
        if _normalize_vital_name(cand) == target:
            return series
    return None


def _is_stale(
    value_time: Optional[datetime],
    reference_time: Optional[datetime],
    threshold: timedelta,
) -> bool:
    if value_time is None or reference_time is None:
        return False
    return reference_time - value_time > threshold


def _dim_color(color: str) -> str:
    r, g, b = mcolors.to_rgb(color)
    blended = (
        1.0 - (1.0 - r) * 0.45,
        1.0 - (1.0 - g) * 0.45,
        1.0 - (1.0 - b) * 0.45,
    )
    return mcolors.to_hex(blended)


def _panel_label(key_group: tuple[str, ...]) -> str:
    return {
        ("HR", "PULSE"): "HR",
        ("SPO2",): "SpO2",
        ("BIS",): "BIS",
        ("ETCO2",): "EtCO2",
        ("TEMP", "TEMP1"): "Temp",
    }[key_group]


def _series_color(
    vitals: VitalsTable,
    style_map: Mapping[str, VitalPlotStyle],
    key_group: tuple[str, ...],
) -> str:
    for key in key_group:
        style = _pick_vital_style(key, style_map)
        if style.axis in {"left", "right"}:
            return style.color
    return "#2f2f2f"


def _pick_vital_style(name: str, style_map: Mapping[str, VitalPlotStyle]) -> VitalPlotStyle:
    key = _normalize_vital_name(name)
    if name in style_map:
        return style_map[name]
    for candidate, style in style_map.items():
        if _normalize_vital_name(candidate) == key:
            return style
    return VitalPlotStyle()


def _normalize_vital_name(name: str) -> str:
    return "".join(ch for ch in name.upper() if ch.isalnum())


def _plot_vital_series(ax, name: str, series, style: VitalPlotStyle) -> None:
    xs = [t for t, v in zip(series.times, series.values) if v is not None]
    ys = [v for v in series.values if v is not None]
    if not xs:
        return
    label = name
    if style.kind == "symbol":
        ax.scatter(xs, ys, s=18, marker=style.marker or "o", color=style.color, label=label)
        return
    ax.plot(
        xs,
        ys,
        linestyle=style.linestyle,
        marker=style.marker,
        ms=3,
        lw=0.9,
        color=style.color,
        label=label,
    )


def _render_clinical_band(
    ax,
    events: Sequence[ClinicalEvent],
    bounds: tuple[datetime, datetime],
) -> None:
    ax.axis("off")
    sub = GridSpecFromSubplotSpec(
        1,
        2,
        subplot_spec=ax.get_subplotspec(),
        width_ratios=[3.5, 1.6],
    )
    ax_strip = ax.figure.add_subplot(sub[0, 0])
    ax_log = ax.figure.add_subplot(sub[0, 1])
    _render_clinical_strip(ax_strip, events, bounds)
    _render_event_log(ax_log, events)


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
    ax.text(
        0.01, 0.9, "\n".join(lines), ha="left", va="top", fontsize=8,
        transform=ax.transAxes,
    )


def _render_cost(ax, cost_report: CostReport) -> None:
    ax.axis("off")
    lines = ["COST"]
    for item in cost_report.items:
        price = "N/A" if item.cost is None else f"{item.cost:.0f} 円"
        lines.append(f"{item.generic_name}: {price}")
    lines.append(f"Total: {cost_report.total:.0f} 円")
    ax.text(
        0.01, 0.9, "\n".join(lines), ha="left", va="top", fontsize=8,
        transform=ax.transAxes,
    )


def _render_ce(
    ax,
    ce_results: dict[str, CeResult],
    master: DrugMasterFile,
    ce_t0: Optional[datetime],
) -> None:
    ax.grid(True, ls=":", alpha=0.45)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    if ce_t0 is None:
        ax.axis("off")
        return
    for drug_id, res in ce_results.items():
        xs = [ce_t0 + timedelta(minutes=m) for m in res.times_min]
        label = f"{master.get(drug_id).generic_name} Ce ({res.conc_unit})"
        ax.plot(xs, res.ce, lw=0.9, label=label)
    ax.set_ylabel("Ce")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    ax.legend(loc="upper right", fontsize=8)
