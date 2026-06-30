"""バイタル取り込み: VSCapture/VitalRecorder の CSV 読み込みと時刻整合.

- VSCapture / VitalRecorder のエクスポート CSV を想定（1列目が時刻、残りがパラメータ）。
- モニタ時計と PC 時計のズレを clock_offset_sec で補正できる。
- `.vital` ファイルは vitaldb パッケージがあれば読み込む（任意依存）。
"""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional

_TIME_FORMATS = [
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%d %H:%M:%S",
    "%Y/%m/%d %H:%M:%S",
    "%Y-%m-%dT%H:%M:%S.%f",
    "%H:%M:%S",
]


def _parse_time(value: str) -> datetime:
    v = value.strip()
    for fmt in _TIME_FORMATS:
        try:
            return datetime.strptime(v, fmt)
        except ValueError:
            continue
    raise ValueError(f"時刻列を解釈できません: {value!r}")


@dataclass
class VitalSeries:
    """単一パラメータの時系列."""

    name: str
    times: list[datetime] = field(default_factory=list)
    values: list[Optional[float]] = field(default_factory=list)


@dataclass
class VitalsTable:
    parameters: dict[str, VitalSeries]
    time_column: str

    def series(self, name: str) -> VitalSeries:
        return self.parameters[name]

    def parameter_names(self) -> list[str]:
        return list(self.parameters)


def load_vitals_csv(
    path: str,
    time_column: Optional[str] = None,
    clock_offset_sec: float = 0.0,
    delimiter: str = ",",
) -> VitalsTable:
    """バイタル CSV を読み込み、各パラメータの時系列に変換.

    clock_offset_sec: モニタ時刻 → PC/基準時刻への補正秒数（+で未来方向にずらす）。
    """
    with open(path, encoding="utf-8-sig", newline="") as fh:
        reader = csv.reader(fh, delimiter=delimiter)
        header = next(reader, None)
        if not header:
            raise ValueError("CSV が空です")

        tcol = time_column or header[0]
        if tcol not in header:
            raise ValueError(f"時刻列 {tcol!r} が見つかりません: {header}")
        tidx = header.index(tcol)
        param_names = [h for i, h in enumerate(header) if i != tidx]
        series = {name: VitalSeries(name=name) for name in param_names}

        offset = timedelta(seconds=clock_offset_sec)
        for row in reader:
            if not row or len(row) <= tidx:
                continue
            try:
                t = _parse_time(row[tidx]) + offset
            except ValueError:
                continue
            for i, h in enumerate(header):
                if i == tidx:
                    continue
                raw = row[i].strip() if i < len(row) else ""
                val: Optional[float]
                try:
                    val = float(raw) if raw != "" else None
                except ValueError:
                    val = None
                series[h].times.append(t)
                series[h].values.append(val)

    return VitalsTable(parameters=series, time_column=tcol)


def load_vital_file(path: str, interval_sec: float = 1.0) -> VitalsTable:
    """VitalRecorder の .vital を読み込む（vitaldb 任意依存）."""
    try:
        import vitaldb  # type: ignore
    except ImportError as exc:  # pragma: no cover - 任意依存
        raise ImportError(
            ".vital の読み込みには vitaldb パッケージが必要です "
            "(pip install vitaldb)"
        ) from exc

    vf = vitaldb.VitalFile(path)
    track_names = vf.get_track_names()
    df = vf.to_pandas(track_names, interval_sec)
    base = datetime.fromtimestamp(vf.dtstart) if getattr(vf, "dtstart", 0) else datetime(1970, 1, 1)

    params: dict[str, VitalSeries] = {}
    for name in track_names:
        if name not in df.columns:
            continue
        s = VitalSeries(name=name)
        for i, v in enumerate(df[name].tolist()):
            s.times.append(base + timedelta(seconds=i * interval_sec))
            s.values.append(None if v != v else float(v))  # NaN -> None
        params[name] = s
    return VitalsTable(parameters=params, time_column="time")
