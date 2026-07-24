.PHONY: all search clean
# `all` is fully offline-reproducible: it reads the committed source figures and
# the committed results/scoping_search.csv (a captured search snapshot, since the
# live Europe PMC count changes over time). Run `make search` when online to
# refresh that snapshot.
all:
	python3 scripts/digitize.py
	python3 scripts/fit_weibull.py
	python3 scripts/make_figures.py
	python3 scripts/make_manuscript.py

search:
	python3 scripts/search_scoping.py

clean:
	rm -f data/*_ltfu_cif.csv results/weibull_fits.csv results/SUMMARY.md figures/*.png \
	      manuscript/*.docx manuscript/*.pptx
