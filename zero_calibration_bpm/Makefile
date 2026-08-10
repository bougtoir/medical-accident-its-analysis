.PHONY: all data analyze figures docs clean

all:
	python3 scripts/build_all.py

data:
	python3 src/simulate.py

analyze: data
	python3 src/analyze.py

figures: analyze
	python3 src/figures.py

docs: analyze figures
	python3 scripts/create_bpm_docx_en.py
	python3 scripts/create_tables_docx_en.py
	python3 scripts/create_figures_pptx_en.py
	python3 scripts/create_tim_cover_letter.py

clean:
	rm -f data/*.csv results/*.csv results/*.json
	rm -f figures/*.png figures/ja/*.png figures/tiff/*.tif
	rm -f figures/pdf/*.pdf figures/submission/*.tif figures/submission/*.pdf
	rm -f manuscripts/*.docx manuscripts/*.pptx manuscripts/*.pdf
	rm -f cover_letter/*.docx
