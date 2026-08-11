# Reproduce the full rate-based re-analysis from raw official files to manuscript.
# Every reported number is regenerated from data_primary/ and results/.
PY=python3

.PHONY: all data analysis manuscript clean

all: data analysis manuscript

data:
	$(PY) data_primary/build_physicians.py
	$(PY) data_primary/build_litigation.py
	$(PY) data_primary/build_facilities.py

analysis: data
	$(PY) data_primary/build_reanalysis.py

manuscript: analysis
	$(PY) manuscript/build_figures_en.py
	$(PY) manuscript/build_manuscript_en.py
	$(PY) manuscript/build_package_en.py

hp_submission: manuscript
	$(PY) manuscript/build_hp_submission.py

ha_submission: manuscript
	$(PY) manuscript/build_healthcare_analytics_submission.py

clean:
	rm -rf data_primary/__pycache__ manuscript/__pycache__
