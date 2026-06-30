from datetime import datetime, timedelta
from pathlib import Path
from anesthesia_record.chart_erga import render_chart_erga
from anesthesia_record.cost import compute_cost
from anesthesia_record.drug_master import load_drug_master
from anesthesia_record.events import EventLog
from anesthesia_record.models import Delivery, MedEvent, Patient, Sex
from anesthesia_record import pkpd
from anesthesia_record.vitals import VitalSeries, VitalsTable

DATA = Path(__file__).resolve().parents[1] / "data" / "drug_master.yaml"


def _synthetic_vitals(t0: datetime, minutes: int) -> VitalsTable:
    hr = VitalSeries("HR")
    sbp = VitalSeries("SBP")
    dbp = VitalSeries("DBP")
    spo2 = VitalSeries("SpO2")
    temp = VitalSeries("Temp")
    for i in range(minutes * 6):
        t = t0 + timedelta(seconds=10 * i)
        m = i / 6.0
        hr.times.append(t)
        hr.values.append(72 + 6 * __import__("math").sin(m / 4.5))
        sbp.times.append(t)
        sbp.values.append(120 + 10 * __import__("math").sin(m / 6.5 + 0.4))
        dbp.times.append(t)
        dbp.values.append(70 + 8 * __import__("math").sin(m / 7.0 + 0.8))
        spo2.times.append(t)
        spo2.values.append(99 - 0.2 * __import__("math").sin(m / 5.0))
        temp.times.append(t)
        temp.values.append(36.5 + 0.1 * __import__("math").sin(m / 8.0))
    return VitalsTable(
        parameters={"HR": hr, "SBP": sbp, "DBP": dbp, "SpO2": spo2, "Temp": temp},
        time_column="Time",
    )


def test_render_chart_erga_creates_png(tmp_path):
    master = load_drug_master(DATA)
    patient = Patient(age_years=45, sex=Sex.MALE, weight_kg=65, height_cm=172, asa_ps=2, patient_id="A-001")
    t0 = datetime(2026, 6, 30, 9, 0, 0)
    clinical = EventLog()
    clinical.add(t0, "anesthesia_start", icon="▲")
    clinical.add(t0 + timedelta(minutes=3), "intubation")
    clinical.add(t0 + timedelta(minutes=12), "incision")
    clinical.add(t0 + timedelta(minutes=28), "surgery_end")

    events = [
        MedEvent("fentanyl_0_1mg", t0, Delivery.BOLUS, dose=100, dose_unit="ug"),
        MedEvent("propofol_1pct", t0 + timedelta(seconds=30), Delivery.BOLUS, dose=130, dose_unit="mg"),
        MedEvent("remifentanil_2mg", t0 + timedelta(minutes=2), Delivery.INFUSION, rate=0.2, rate_unit="ug/kg/min", end_time=t0 + timedelta(minutes=30)),
        MedEvent("propofol_1pct", t0 + timedelta(minutes=2), Delivery.INFUSION, rate=6, rate_unit="mg/kg/h", end_time=t0 + timedelta(minutes=30)),
    ]

    ce_results = {}
    for drug_id in ("propofol_1pct", "remifentanil_2mg"):
        drug = master.get(drug_id)
        ce_results[drug_id] = pkpd.simulate(drug, patient, events, t0, duration_min=15, dt_s=5.0)

    out = render_chart_erga(
        _synthetic_vitals(t0, 30),
        events,
        master,
        str(tmp_path / "erga.png"),
        patient=patient,
        clinical_events=clinical.sorted(),
        cost_report=compute_cost(events, master, patient),
        ce_results=ce_results,
        ce_t0=t0,
        show_floating_latest=True,
        latest_panel_loc="upper left",
        event_icon_map={"incision": "◆"},
    )

    assert out.endswith("erga.png")
    path = tmp_path / "erga.png"
    assert path.exists()
    assert path.stat().st_size > 0
