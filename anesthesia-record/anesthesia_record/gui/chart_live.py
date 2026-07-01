"""リアルタイム用チャート描画: chart_erga のライブ表示版.

chart_erga.render_chart_erga をベースに、Figure への直接描画版。
ファイル保存ではなく Figure オブジェクトに描画してGUI上で表示する。
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional, Sequence

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.gridspec import GridSpec

from ..chart_common import _configure_japanese_font
from ..chart_erga import (
    DEFAULT_AXIS_SPECS,
    DEFAULT_VITAL_STYLES,
    DEFAULT_EVENT_ICONS,
    VitalAxisSpec,
    VitalPlotStyle,
    _AXIS_GROUP_ALIASES,
)
from ..drug_master import DrugMasterFile
from ..events import ClinicalEvent
from ..models import Delivery, MedEvent, OutputCategory, OutputEvent, Patient
from ..anesthesia_fee import AnesthesiaFeeConfig, compute_anesthesia_fee, AnesthesiaEvent
from ..units import consumed_amounts as _consumed_single
from .session import AnesthesiaSession


_configure_japanese_font()


def render_live_chart(
    fig: Figure,
    session: AnesthesiaSession,
    drug_master: DrugMasterFile,
    fee_config: Optional[AnesthesiaFeeConfig] = None,
) -> None:
    """セッションデータからリアルタイムチャートを描画.

    fig を clear して描画し直す。GUIの定期更新から呼ばれる。
    """
    if session.anesthesia_start is None:
        # まだ開始前
        ax = fig.add_subplot(111)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.text(0.5, 0.5, "麻酔記録 v0.2\n\n患者情報を入力して「麻酔開始」を押してください",
                ha="center", va="center", fontsize=14, color="#666")
        ax.axis("off")
        return

    t_start = session.anesthesia_start
    t_end = session.anesthesia_end or datetime.now()
    # 少し余裕を持たせる
    t_end_display = t_end + timedelta(minutes=2)
    elapsed_min = (t_end - t_start).total_seconds() / 60.0

    # レイアウト: ヘッダ / バイタル / 薬剤行 / 出血尿量 / コスト・イベント
    drug_rows = _get_drug_rows(session.med_events, drug_master)
    n_drug_rows = len(drug_rows)
    has_outputs = len(session.output_events) > 0

    # GridSpec 高さ比率
    heights = [0.4]  # ヘッダ
    heights.append(4.0)  # バイタル
    for _ in range(n_drug_rows):
        heights.append(0.12)  # 薬剤行
    if has_outputs:
        heights.append(0.8)  # 出血・尿量
    heights.append(0.5)  # コスト・イベント・時刻

    gs = GridSpec(len(heights), 1, figure=fig, height_ratios=heights, hspace=0.0)

    row_idx = 0

    # --- ヘッダ ---
    ax_header = fig.add_subplot(gs[row_idx])
    _render_header(ax_header, session, elapsed_min)
    row_idx += 1

    # --- バイタル ---
    ax_vitals = fig.add_subplot(gs[row_idx])
    _render_vitals(ax_vitals, session, t_start, t_end_display)
    row_idx += 1

    # --- 薬剤行 ---
    for i, (drug_id, events_for_drug) in enumerate(drug_rows.items()):
        ax_drug = fig.add_subplot(gs[row_idx], sharex=ax_vitals)
        _render_drug_row(ax_drug, drug_id, events_for_drug, drug_master, session.patient, t_start, t_end_display)
        row_idx += 1

    # --- 出血・尿量 ---
    if has_outputs:
        ax_out = fig.add_subplot(gs[row_idx], sharex=ax_vitals)
        _render_outputs(ax_out, session.output_events, t_start, t_end_display)
        row_idx += 1

    # --- コスト・イベント・時刻 ---
    ax_bottom = fig.add_subplot(gs[row_idx], sharex=ax_vitals)
    _render_bottom_bar(ax_bottom, session, t_start, t_end_display)

    fig.tight_layout(h_pad=0.0)


def _get_drug_rows(med_events: list[MedEvent], master: DrugMasterFile) -> dict[str, list[MedEvent]]:
    """薬剤IDごとにイベントをグループ化し、表示順にソート."""
    rows: dict[str, list[MedEvent]] = {}
    for m in med_events:
        rows.setdefault(m.drug_id, []).append(m)

    # display_order でソート
    def _sort_key(drug_id: str) -> tuple[int, str]:
        try:
            drug = master.get(drug_id)
        except KeyError:
            return (500, drug_id)
        if drug.display_order is not None:
            return (drug.display_order, drug_id)
        cat_order = {"iv_anesthetic": 0, "opioid": 1, "muscle_relaxant": 2,
                     "local_anesthetic": 3, "vasopressor": 4, "other": 5, "fluid": 9}
        return (cat_order.get(drug.category, 5) * 100, drug_id)

    sorted_ids = sorted(rows.keys(), key=_sort_key)
    return {k: rows[k] for k in sorted_ids}


def _render_header(ax, session: AnesthesiaSession, elapsed_min: float) -> None:
    ax.axis("off")
    parts = []
    if session.patient:
        p = session.patient
        parts.append(f"ID: {p.patient_id or '---'}  {p.age_years:.0f}歳  "
                     f"{'男' if p.sex.value == 'male' else '女'}  "
                     f"{p.weight_kg}kg  {p.height_cm}cm  ASA-PS {p.asa_ps or '?'}")
    if session.anesthesia_start:
        parts.append(f"麻酔開始: {session.anesthesia_start.strftime('%H:%M')}  "
                     f"経過: {int(elapsed_min)}分")
    if session.anesthesia_end:
        parts.append(f"  麻酔終了: {session.anesthesia_end.strftime('%H:%M')}")

    text = "  |  ".join(parts) if parts else "麻酔記録 v0.2"
    ax.text(0.01, 0.5, text, ha="left", va="center", fontsize=9, weight="bold",
            transform=ax.transAxes)

    # リアルタイム時刻
    now_str = datetime.now().strftime("%H:%M:%S")
    ax.text(0.99, 0.5, f"現在 {now_str}", ha="right", va="center", fontsize=8,
            color="#666", transform=ax.transAxes)


def _render_vitals(ax, session: AnesthesiaSession, t_start: datetime, t_end: datetime) -> None:
    """バイタルサイン描画."""
    ax.set_xlim(t_start, t_end)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    ax.xaxis.set_major_locator(mdates.MinuteLocator(interval=15))

    # グリッド: 15分ごと細線、1時間ごと太線
    ax.grid(True, which="major", linewidth=0.3, color="#ccc")
    # 1時間ごとの太線
    hour_start = t_start.replace(minute=0, second=0, microsecond=0)
    t = hour_start
    while t <= t_end:
        if t >= t_start:
            ax.axvline(t, color="#999", linewidth=0.8, zorder=1)
        t += timedelta(hours=1)

    # 左軸: HR/BP (0-200)
    ax.set_ylim(0, 200)
    ax.set_ylabel("HR / BP", fontsize=7)
    ax.tick_params(labelsize=6)

    if session.vitals is None:
        ax.text(0.5, 0.5, "バイタルデータ待機中...", ha="center", va="center",
                fontsize=10, color="#aaa", transform=ax.transAxes)
        return

    vitals = session.vitals
    style_map = DEFAULT_VITAL_STYLES

    # 左軸パラメータ描画
    for key in ("HR", "SBP", "DBP"):
        if key in vitals.parameters:
            series = vitals.parameters[key]
            style = style_map.get(key, VitalPlotStyle())
            times_filtered = []
            vals_filtered = []
            for t_val, v_val in zip(series.times, series.values):
                if v_val is not None and t_start <= t_val <= t_end:
                    times_filtered.append(t_val)
                    vals_filtered.append(v_val)
            if times_filtered:
                if style.marker:
                    ax.plot(times_filtered, vals_filtered, color=style.color,
                            marker=style.marker, markersize=3, linewidth=0.8,
                            linestyle=style.linestyle, zorder=3)
                else:
                    ax.plot(times_filtered, vals_filtered, color=style.color,
                            linewidth=0.8, linestyle=style.linestyle, zorder=3)

    # 右軸: SpO2 (90-100)
    ax2 = ax.twinx()
    ax2.set_ylim(90, 100)
    ax2.set_ylabel("SpO2", fontsize=7, color="#0f766e")
    ax2.tick_params(labelsize=6, colors="#0f766e")
    ax2.set_zorder(ax.get_zorder() - 1)
    ax2.patch.set_visible(False)

    for key in ("SpO2", "SPO2"):
        if key in vitals.parameters:
            series = vitals.parameters[key]
            style = style_map.get(key, VitalPlotStyle(color="#0f766e"))
            times_filtered = []
            vals_filtered = []
            for t_val, v_val in zip(series.times, series.values):
                if v_val is not None and t_start <= t_val <= t_end:
                    times_filtered.append(t_val)
                    vals_filtered.append(v_val)
            if times_filtered:
                ax2.plot(times_filtered, vals_filtered, color=style.color,
                         marker="o", markersize=2, linewidth=0.6, zorder=2)
            break

    # イベントマーカー
    for ev in session.events:
        if t_start <= ev.time <= t_end:
            icon = DEFAULT_EVENT_ICONS.get(ev.type, "#")
            ax.axvline(ev.time, color="#e11d48", linewidth=0.5, linestyle="--", alpha=0.5, zorder=2)
            ax.text(ev.time, 195, icon, ha="center", va="top", fontsize=7, color="#e11d48", zorder=5)


def _render_drug_row(
    ax, drug_id: str, events: list[MedEvent],
    master: DrugMasterFile, patient: Optional[Patient],
    t_start: datetime, t_end: datetime
) -> None:
    """単一薬剤行の描画."""
    ax.set_xlim(t_start, t_end)
    ax.set_ylim(0, 1)
    ax.axis("off")
    # 左にラベル
    try:
        drug = master.get(drug_id)
        name = drug.generic_name
        color = drug.color or "#222"
    except KeyError:
        drug = None
        name = drug_id
        color = "#222"

    ax.text(-0.01, 1.7, name, ha="right", va="center", fontsize=5.5,
            transform=ax.transAxes, color=color, weight="bold")

    # イベント描画
    for med in events:
        if med.delivery == Delivery.BOLUS and med.dose is not None:
            # ボーラス: 縦線 + 数値
            x = med.start_time
            ax.axvline(x, color=color, linewidth=0.8, ymin=0.1, ymax=0.9)
            ax.text(x, 0.3, f"{med.dose:.0f}", ha="center", va="center",
                    fontsize=5, color=color)
        elif med.delivery == Delivery.INFUSION:
            # 持続: 水平線
            x0 = med.start_time
            x1 = med.end_time or datetime.now()
            ax.plot([x0, x1], [0.5, 0.5], color=color, linewidth=1.5, solid_capstyle="butt")
            # 流量表示
            if med.rate is not None:
                ax.text(x0, 0.2, f"{med.rate:.1f}", ha="left", va="center",
                        fontsize=5, color=color)
            # 残量表示(輸液)
            if med.remaining_ml_start is not None:
                ax.text(x0, 0.2, f"{med.remaining_ml_start:.0f}ml", ha="left",
                        va="center", fontsize=5, color=color)
            if med.remaining_ml_end is not None:
                ax.text(x1, 0.2, f"{med.remaining_ml_end:.0f}ml", ha="right",
                        va="center", fontsize=5, color=color)
            # 終了マーカー
            if med.end_time is not None:
                ax.text(x1, 0.5, "//", ha="center", va="center",
                        fontsize=6, color=color, weight="bold")

    # 積算量(右端)
    if drug and patient:
        total_mg = 0.0
        for m in events:
            try:
                mg, _ = _consumed_single(drug, m, patient)
                total_mg += mg
            except (ValueError, TypeError):
                pass
        if total_mg > 0:
            ax.text(1.01, 0.5, f"{total_mg:.0f}", ha="left", va="center",
                    fontsize=5, color=color, transform=ax.transAxes)


def _render_outputs(ax, output_events: list[OutputEvent], t_start: datetime, t_end: datetime) -> None:
    """出血・尿量のボーリングスコア表示."""
    ax.set_xlim(t_start, t_end)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.text(-0.01, 0.5, "出血/尿量", ha="right", va="center", fontsize=6,
            transform=ax.transAxes, weight="bold")

    cat_colors = {
        OutputCategory.GAUZE: "#dc2626",
        OutputCategory.SUCTION: "#b91c1c",
        OutputCategory.URINE: "#ca8a04",
    }
    cat_labels = {
        OutputCategory.GAUZE: "ガーゼ",
        OutputCategory.SUCTION: "吸引",
        OutputCategory.URINE: "尿",
    }

    # カテゴリ別に積算
    cat_totals: dict[OutputCategory, float] = {}
    for oe in output_events:
        cat_totals[oe.category] = cat_totals.get(oe.category, 0) + oe.amount

    y_positions = {OutputCategory.GAUZE: 0.75, OutputCategory.SUCTION: 0.5, OutputCategory.URINE: 0.25}

    for oe in output_events:
        if t_start <= oe.time <= t_end:
            y = y_positions.get(oe.category, 0.5)
            color = cat_colors.get(oe.category, "#666")
            # 差分積算計算
            running = sum(o.amount for o in output_events
                         if o.category == oe.category and o.time <= oe.time)
            ax.text(oe.time, y, f"+{oe.amount:.0f}({running:.0f})",
                    ha="center", va="center", fontsize=5, color=color)

    # 右端に総量
    x_right = 1.01
    for cat, total in cat_totals.items():
        y = y_positions.get(cat, 0.5)
        color = cat_colors.get(cat, "#666")
        label = cat_labels.get(cat, "")
        ax.text(x_right, y, f"{label}: {total:.0f}", ha="left", va="center",
                fontsize=5, color=color, transform=ax.transAxes)


def _render_bottom_bar(ax, session: AnesthesiaSession, t_start: datetime, t_end: datetime) -> None:
    """下部バー: イベントアイコン + 時刻軸."""
    ax.set_xlim(t_start, t_end)
    ax.set_ylim(0, 1)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    ax.xaxis.set_major_locator(mdates.MinuteLocator(interval=15))
    ax.tick_params(axis="x", labelsize=6)
    ax.yaxis.set_visible(False)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)

    # イベント表示
    for ev in session.events:
        if t_start <= ev.time <= t_end:
            icon = DEFAULT_EVENT_ICONS.get(ev.type, "#")
            label = ev.label or ev.type
            ax.text(ev.time, 0.7, f"{icon}{label}", ha="center", va="center",
                    fontsize=5, rotation=45, color="#333")
