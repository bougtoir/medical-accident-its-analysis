# Reproducibility checklist

## Public source data

- hmmix 1000 Genomes and HGDP segment files: Zenodo record 14136628
- O2-defining `rs41302905 T` frequencies: Ensembl REST Variation endpoint
- Solomon Islands ABO*O02 frequencies: Ohashi et al. 2006, doi:10.1007/s10038-006-0375-8
- Ancient ABO-window summary: secondary extraction from public Iasi et al. 2024 outputs

## Rebuild order

Run from the project root:

```bash
python scripts/run_ajba_pipeline.py   --segments-1kg /path/to/hg38_1000g_segments.txt   --segments-hgdp /path/to/hg38_HGDP_segments.txt   --permutations 9999   --sensitivity-permutations 999
```

## Expected primary checks

- Individuals: 3,134
- Populations: 66
- Unique population pairs: 2,145
- Every population-window frequency is between 0 and 1
- Neanderthal raw distance r: -0.4971
- Denisovan raw distance r: -0.4617
- Neanderthal expanded descriptive R²: 0.5461
- Denisovan expanded descriptive R²: 0.5113
- QAP distance P: 0.0001 and 0.0002
- FDR q<0.10 non-admixed outliers: 0 and 0
- Neanderthal/Both segments in the 500-kb ABO interval: 834
- Strict ABO-overlapping Neanderthal/Both segments: 129
- Indigenous American window carriers: Pima 1/13, Maya 1/21, Colombian 0/7
- Strict ABO overlap among those carriers: Pima only

## Environment used for the package

- `pandas==2.2.3`
- `numpy==2.2.1`
- `scipy==1.14.1`
- `statsmodels==0.14.6`
- `matplotlib==3.10.0`
- `seaborn==0.13.2`
- `python-docx==1.2.0`
- `python-pptx==1.0.2`
- `Pillow==11.0.0`

## Interpretation guardrails

- Pairwise correlation does not prove identity by descent.
- Pairwise rows are dependent; inference uses population-label permutations.
- Expanded-model R² is descriptive and not a causal variance decomposition.
- Reference-genome similarity does not prove a specific migration route.
- Admixed American residuals are not treated as ancient-migration evidence.
- No positive-residual non-admixed pair survived FDR correction.
- Ancient and modern ABO-window calls were produced by different pipelines.
