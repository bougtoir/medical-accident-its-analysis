import os
import tempfile
from datetime import datetime

from anesthesia_record.vitals import load_vitals_csv


def _write(tmp, text):
    p = os.path.join(tmp, "v.csv")
    with open(p, "w", encoding="utf-8") as fh:
        fh.write(text)
    return p


def test_load_csv_basic():
    with tempfile.TemporaryDirectory() as tmp:
        p = _write(
            tmp,
            "Time,HR,SpO2\n"
            "2026-06-30T09:00:00,72,99\n"
            "2026-06-30T09:00:05,74,98\n"
            "2026-06-30T09:00:10,,97\n",
        )
        tbl = load_vitals_csv(p)
        assert set(tbl.parameter_names()) == {"HR", "SpO2"}
        hr = tbl.series("HR")
        assert hr.values == [72.0, 74.0, None]
        assert hr.times[0] == datetime(2026, 6, 30, 9, 0, 0)


def test_clock_offset_applied():
    with tempfile.TemporaryDirectory() as tmp:
        p = _write(tmp, "Time,HR\n2026-06-30T09:00:00,72\n")
        tbl = load_vitals_csv(p, clock_offset_sec=10)
        assert tbl.series("HR").times[0] == datetime(2026, 6, 30, 9, 0, 10)
