# Reproduce the full rate-based re-analysis from raw official files to manuscript.
# Every reported number is regenerated from data_primary/ and results/.
PY=python3

.PHONY: all data analysis figures ssm_submission clean

all: data analysis figures

data:
	$(PY) data_primary/build_physicians.py
	$(PY) data_primary/build_litigation.py
	$(PY) data_primary/build_facilities.py
	$(PY) data_primary/build_senkoi_coverage.py

analysis: data
	$(PY) data_primary/build_reanalysis.py

figures: analysis
	$(PY) manuscript/build_figures_en.py

ssm_submission: figures
	$(PY) manuscript/build_social_science_medicine_submission.py

clean:
	rm -rf data_primary/__pycache__ manuscript/__pycache__
