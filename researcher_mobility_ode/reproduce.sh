#!/usr/bin/env bash
# Reproduce all results and the manuscript from OpenAlex data/cache.
set -e

python src/cohort_extraction.py
python src/ode_model.py
python src/ode_model_endogenous.py
python src/ode_model_endogenous.py --saturating --results-dir results/endogenous_saturating
python src/time_varying.py --cutoff 2010
python src/bootstrap_ci.py --n-boot 200
python src/policy_counterfactuals.py --packages
python scripts/build_full_manuscript.py
