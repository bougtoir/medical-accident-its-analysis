.PHONY: all clean
all:
	python3 scripts/digitize.py
	python3 scripts/fit_weibull.py
	python3 scripts/make_figures.py
	python3 scripts/make_manuscript.py

clean:
	rm -f data/*_ltfu_cif.csv results/*.csv results/SUMMARY.md figures/*.png \
	      manuscript/*.docx manuscript/*.pptx
