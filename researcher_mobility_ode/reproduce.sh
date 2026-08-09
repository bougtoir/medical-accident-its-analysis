#!/usr/bin/env bash
# Reproduce all results and the manuscript from committed cohort data.
# Cohort extraction from OpenAlex is slow and requires API budget.
# Run it first with REEXTRACT=1 only when you want to refresh the cohort.
set -e
cd "$(dirname "$0")"

if [ -n "${REEXTRACT}" ]; then
    python src/cohort_extraction.py
fi

python src/ode_model.py
python src/ode_model_endogenous.py
python src/ode_model_endogenous.py --saturating --results-dir results/endogenous_saturating
python src/time_varying.py --cutoff 2010
python src/bootstrap_ci.py --n-boot 200
python src/policy_counterfactuals.py --packages
python scripts/build_full_manuscript.py
