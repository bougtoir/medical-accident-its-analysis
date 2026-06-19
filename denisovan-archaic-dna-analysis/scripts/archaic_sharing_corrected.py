"""
Corrected analysis: Archaic introgression segment sharing between populations
with confounding factor adjustments.

Corrections applied:
1. Admixed population flagging and European ancestry proportion as covariate
2. Continental-pair indicator as covariate (shared demographic history proxy)
3. Multiple regression: sharing ~ geo_dist + admixture + same_continent
4. Partial correlation (controlling for admixture and continental grouping)
5. Permutation test for outlier significance
6. Bootstrap confidence intervals for key correlations

Input:  data/pairwise_sharing.csv (from archaic_sharing_analysis.py)
Output: data/pairwise_sharing_corrected.csv
        data/outlier_summary.csv
        data/correction_stats.txt
"""

import pandas as pd
import numpy as np
from scipy import stats
from scipy.spatial.distance import squareform
import statsmodels.api as sm
from itertools import combinations
import warnings
warnings.filterwarnings('ignore')

np.random.seed(42)

# ===== Load data =====
print("=" * 60)
print("Loading pairwise sharing data...")
print("=" * 60)

res = pd.read_csv('data/pairwise_sharing.csv')
print(f"Total pairs: {len(res)}")
print(f"Columns: {list(res.columns)}")

# ===== 1. Admixed population metadata =====
# Known admixture proportions (European ancestry fraction)
# Sources: 1000 Genomes Phase 3, Bryc et al. 2015, Moreno-Estrada et al. 2013
ADMIXED_EUR_FRAC = {
    'PUR': 0.64,   # Puerto Rico — ~64% European
    'CLM': 0.57,   # Colombia — ~57% European
    'MXL': 0.48,   # Mexican-American — ~48% European
    'PEL': 0.16,   # Peru — ~16% European
    'ACB': 0.04,   # African Caribbean — ~4% European
    'ASW': 0.20,   # African-American SW — ~20% European
}

# All populations with any known recent admixture (post-1500 CE)
ADMIXED_POPS = set(ADMIXED_EUR_FRAC.keys())

# Continental assignments for each population
CONTINENT_MAP = {
    # Europe
    'CEU': 'EUR', 'FIN': 'EUR', 'GBR': 'EUR', 'IBS': 'EUR', 'TSI': 'EUR',
    'French': 'EUR', 'Sardinian': 'EUR', 'Orcadian': 'EUR', 'Russian': 'EUR',
    'BergamoItalian': 'EUR', 'Tuscan': 'EUR', 'Basque': 'EUR', 'Adygei': 'EUR',
    # Middle East
    'Druze': 'WAS', 'Bedouin': 'WAS', 'Palestinian': 'WAS', 'Mozabite': 'WAS',
    # Central/South Asia
    'Brahui': 'SAS', 'Balochi': 'SAS', 'Hazara': 'SAS', 'Makrani': 'SAS',
    'Sindhi': 'SAS', 'Pathan': 'SAS', 'Kalash': 'SAS', 'Burusho': 'SAS',
    'Uygur': 'SAS', 'PJL': 'SAS', 'BEB': 'SAS', 'STU': 'SAS',
    'ITU': 'SAS', 'GIH': 'SAS',
    # East Asia
    'CHB': 'EAS', 'CHS': 'EAS', 'CDX': 'EAS', 'KHV': 'EAS', 'JPT': 'EAS',
    'Cambodian': 'EAS', 'Japanese': 'EAS', 'Han': 'EAS', 'Yakut': 'EAS',
    'Tujia': 'EAS', 'Yi': 'EAS', 'Miao': 'EAS', 'Oroqen': 'EAS',
    'Daur': 'EAS', 'Mongolian': 'EAS', 'Hezhen': 'EAS', 'Xibo': 'EAS',
    'NorthernHan': 'EAS', 'Dai': 'EAS', 'Lahu': 'EAS', 'She': 'EAS',
    'Naxi': 'EAS', 'Tu': 'EAS',
    # Americas
    'PUR': 'AMR', 'CLM': 'AMR', 'PEL': 'AMR', 'MXL': 'AMR',
    'Colombian': 'AMR', 'Surui': 'AMR', 'Maya': 'AMR',
    'Karitiana': 'AMR', 'Pima': 'AMR',
    # Oceania
    'Bougainville': 'OCE', 'PapuanSepik': 'OCE', 'PapuanHighlands': 'OCE',
}

# ===== 2. Add covariates =====
print("\n" + "=" * 60)
print("Adding covariates...")
print("=" * 60)

def get_admix_eur(pop):
    return ADMIXED_EUR_FRAC.get(pop, 0.0)

def is_admixed(pop):
    return 1 if pop in ADMIXED_POPS else 0

def get_continent(pop):
    return CONTINENT_MAP.get(pop, 'UNK')

res = res.copy()

# Admixture covariates
res['admix_eur_1'] = res['pop1'].apply(get_admix_eur)
res['admix_eur_2'] = res['pop2'].apply(get_admix_eur)
res['max_admix_eur'] = res[['admix_eur_1', 'admix_eur_2']].max(axis=1)
res['any_admixed'] = ((res['pop1'].apply(is_admixed)) |
                       (res['pop2'].apply(is_admixed))).astype(int)

# Continental covariates
res['continent1'] = res['pop1'].apply(get_continent)
res['continent2'] = res['pop2'].apply(get_continent)
res['same_continent'] = (res['continent1'] == res['continent2']).astype(int)

# Continental pair type (for interaction effects)
res['continent_pair'] = res.apply(
    lambda r: '-'.join(sorted([r['continent1'], r['continent2']])), axis=1)

print(f"Admixed pairs: {res['any_admixed'].sum()}")
print(f"Same-continent pairs: {res['same_continent'].sum()}")
print(f"Continental pair types: {res['continent_pair'].nunique()}")

# ===== 3. Multiple regression with covariates (Neanderthal) =====
print("\n" + "=" * 60)
print("Multiple regression: Neanderthal sharing ~ covariates")
print("=" * 60)

valid_n = res.dropna(subset=['nean_corr']).copy()

# Model: nean_corr ~ geo_dist + max_admix_eur + same_continent
X_n = valid_n[['geo_dist_km', 'max_admix_eur', 'same_continent']].copy()
X_n['geo_dist_km'] = X_n['geo_dist_km'] / 1000  # scale to thousands km
X_n = sm.add_constant(X_n)
y_n = valid_n['nean_corr']

model_n = sm.OLS(y_n, X_n).fit()
print(model_n.summary())

# Corrected residuals
valid_n['nean_resid_corrected'] = model_n.resid

# For comparison: uncorrected residuals (simple distance-only model)
X_simple = sm.add_constant(valid_n['geo_dist_km'] / 1000)
model_simple_n = sm.OLS(y_n, X_simple).fit()
valid_n['nean_resid_uncorrected'] = model_simple_n.resid

print(f"\nUncorrected model R²: {model_simple_n.rsquared:.4f}")
print(f"Corrected model R²:   {model_n.rsquared:.4f}")
print(f"Variance explained by confounders: {model_n.rsquared - model_simple_n.rsquared:.4f}")

# ===== 4. Multiple regression with covariates (Denisovan) =====
print("\n" + "=" * 60)
print("Multiple regression: Denisovan sharing ~ covariates")
print("=" * 60)

valid_d = res.dropna(subset=['deni_corr']).copy()

X_d = valid_d[['geo_dist_km', 'max_admix_eur', 'same_continent']].copy()
X_d['geo_dist_km'] = X_d['geo_dist_km'] / 1000
X_d = sm.add_constant(X_d)
y_d = valid_d['deni_corr']

model_d = sm.OLS(y_d, X_d).fit()
print(model_d.summary())

valid_d['deni_resid_corrected'] = model_d.resid

X_simple_d = sm.add_constant(valid_d['geo_dist_km'] / 1000)
model_simple_d = sm.OLS(y_d, X_simple_d).fit()
valid_d['deni_resid_uncorrected'] = model_simple_d.resid

print(f"\nUncorrected model R²: {model_simple_d.rsquared:.4f}")
print(f"Corrected model R²:   {model_d.rsquared:.4f}")
print(f"Variance explained by confounders: {model_d.rsquared - model_simple_d.rsquared:.4f}")

# ===== 5. Permutation test for outlier significance =====
print("\n" + "=" * 60)
print("Permutation test (10,000 iterations)...")
print("=" * 60)

N_PERM = 10000

def permutation_test_residuals(valid_df, corr_col, model_covariates_cols, n_perm=N_PERM):
    """
    Permutation test: shuffle the correlation values and refit the model.
    Build null distribution from ALL residuals across ALL permutations,
    then compute per-pair empirical p-values with FDR correction.
    """
    X = valid_df[model_covariates_cols].copy()
    X.iloc[:, 0] = X.iloc[:, 0] / 1000 if X.iloc[:, 0].max() > 100 else X.iloc[:, 0]
    X = sm.add_constant(X)
    y = valid_df[corr_col].values

    # Observed residuals
    model = sm.OLS(y, X).fit()
    obs_resid = model.resid.values

    # Null distribution: collect ALL residuals from permuted data
    null_resid_pool = np.zeros(n_perm)
    for i in range(n_perm):
        y_perm = np.random.permutation(y)
        model_perm = sm.OLS(y_perm, X).fit()
        # Sample one random residual per permutation for the null
        null_resid_pool[i] = np.random.choice(model_perm.resid.values)

    # Per-pair p-values: fraction of null residuals >= observed
    p_values = np.array([
        np.mean(null_resid_pool >= r) for r in obs_resid
    ])

    # FDR correction (Benjamini-Hochberg)
    from statsmodels.stats.multitest import multipletests
    reject, p_fdr, _, _ = multipletests(p_values, alpha=0.05, method='fdr_bh')

    return obs_resid, p_values, p_fdr, null_resid_pool

# Neanderthal permutation test
nean_resid, nean_pval, nean_fdr, nean_null = permutation_test_residuals(
    valid_n, 'nean_corr', ['geo_dist_km', 'max_admix_eur', 'same_continent'])
valid_n['nean_perm_pval'] = nean_pval
valid_n['nean_fdr_pval'] = nean_fdr
print(f"Neanderthal: {np.sum(nean_pval < 0.05)} pairs nominal p<0.05")
print(f"Neanderthal: {np.sum(nean_fdr < 0.05)} pairs FDR q<0.05")
print(f"Neanderthal: {np.sum(nean_fdr < 0.10)} pairs FDR q<0.10")

# Denisovan permutation test
deni_resid, deni_pval, deni_fdr, deni_null = permutation_test_residuals(
    valid_d, 'deni_corr', ['geo_dist_km', 'max_admix_eur', 'same_continent'])
valid_d['deni_perm_pval'] = deni_pval
valid_d['deni_fdr_pval'] = deni_fdr
print(f"Denisovan:   {np.sum(deni_pval < 0.05)} pairs nominal p<0.05")
print(f"Denisovan:   {np.sum(deni_fdr < 0.05)} pairs FDR q<0.05")
print(f"Denisovan:   {np.sum(deni_fdr < 0.10)} pairs FDR q<0.10")

# ===== 6. Bootstrap confidence intervals for key correlations =====
print("\n" + "=" * 60)
print("Bootstrap CIs for regression coefficients (5,000 iterations)...")
print("=" * 60)

N_BOOT = 5000

def bootstrap_regression_ci(valid_df, corr_col, covariate_cols, n_boot=N_BOOT):
    """Bootstrap CIs for regression coefficients."""
    X = valid_df[covariate_cols].copy()
    X.iloc[:, 0] = X.iloc[:, 0] / 1000 if X.iloc[:, 0].max() > 100 else X.iloc[:, 0]
    X = sm.add_constant(X)
    y = valid_df[corr_col].values
    n = len(y)

    boot_coefs = np.zeros((n_boot, X.shape[1]))
    boot_r2 = np.zeros(n_boot)

    for i in range(n_boot):
        idx = np.random.choice(n, n, replace=True)
        try:
            model_b = sm.OLS(y[idx], X.iloc[idx]).fit()
            boot_coefs[i] = model_b.params
            boot_r2[i] = model_b.rsquared
        except Exception:
            boot_coefs[i] = np.nan
            boot_r2[i] = np.nan

    ci_lower = np.nanpercentile(boot_coefs, 2.5, axis=0)
    ci_upper = np.nanpercentile(boot_coefs, 97.5, axis=0)

    col_names = ['const'] + list(covariate_cols)
    print(f"\n{'Coefficient':<20} {'Estimate':>10} {'95% CI Lower':>14} {'95% CI Upper':>14}")
    original_model = sm.OLS(y, X).fit()
    for j, name in enumerate(col_names):
        print(f"{name:<20} {original_model.params.iloc[j]:>10.4f} {ci_lower[j]:>14.4f} {ci_upper[j]:>14.4f}")

    print(f"{'R²':<20} {original_model.rsquared:>10.4f} "
          f"{np.nanpercentile(boot_r2, 2.5):>14.4f} {np.nanpercentile(boot_r2, 97.5):>14.4f}")

    return boot_coefs, boot_r2

cov_cols = ['geo_dist_km', 'max_admix_eur', 'same_continent']

print("\n--- Neanderthal ---")
nean_boot_coefs, nean_boot_r2 = bootstrap_regression_ci(valid_n, 'nean_corr', cov_cols)

print("\n--- Denisovan ---")
deni_boot_coefs, deni_boot_r2 = bootstrap_regression_ci(valid_d, 'deni_corr', cov_cols)

# ===== 7. Partial correlation (Neanderthal sharing ~ distance | confounders) =====
print("\n" + "=" * 60)
print("Partial correlations...")
print("=" * 60)

def partial_correlation(x, y, covariates):
    """Compute partial correlation of x and y controlling for covariates."""
    # Regress x on covariates
    X_cov = sm.add_constant(covariates)
    resid_x = sm.OLS(x, X_cov).fit().resid
    resid_y = sm.OLS(y, X_cov).fit().resid
    r, p = stats.pearsonr(resid_x, resid_y)
    return r, p

# Neanderthal: sharing ~ distance | admixture + continent
covariates_n = valid_n[['max_admix_eur', 'same_continent']].values
r_nean_partial, p_nean_partial = partial_correlation(
    valid_n['geo_dist_km'].values / 1000,
    valid_n['nean_corr'].values,
    covariates_n
)
r_nean_raw, p_nean_raw = stats.pearsonr(
    valid_n['geo_dist_km'].values / 1000, valid_n['nean_corr'].values)

print(f"Neanderthal sharing ~ distance:")
print(f"  Raw correlation:     r = {r_nean_raw:.4f}, p = {p_nean_raw:.2e}")
print(f"  Partial correlation: r = {r_nean_partial:.4f}, p = {p_nean_partial:.2e}")

# Denisovan
covariates_d = valid_d[['max_admix_eur', 'same_continent']].values
r_deni_partial, p_deni_partial = partial_correlation(
    valid_d['geo_dist_km'].values / 1000,
    valid_d['deni_corr'].values,
    covariates_d
)
r_deni_raw, p_deni_raw = stats.pearsonr(
    valid_d['geo_dist_km'].values / 1000, valid_d['deni_corr'].values)

print(f"\nDenisovan sharing ~ distance:")
print(f"  Raw correlation:     r = {r_deni_raw:.4f}, p = {p_deni_raw:.2e}")
print(f"  Partial correlation: r = {r_deni_partial:.4f}, p = {p_deni_partial:.2e}")

# ===== 8. Identify significant outliers after correction =====
print("\n" + "=" * 60)
print("Significant outlier pairs after confounding correction")
print("=" * 60)

# Neanderthal outliers: top corrected residuals with significance
print("\nTop 20 Neanderthal pairs by corrected residual (non-admixed):")
nean_clean = valid_n[valid_n['any_admixed'] == 0].copy()
nean_top = nean_clean.nlargest(20, 'nean_resid_corrected')
print(f"{'Pop1':<20} {'Pop2':<20} {'Region1':<15} {'Region2':<15} "
      f"{'Dist(km)':<10} {'Corr':<8} {'Resid':<8} {'p_nom':<8} {'q_FDR':<8}")
for _, row in nean_top.iterrows():
    print(f"{row['pop1']:<20} {row['pop2']:<20} {row['region1']:<15} {row['region2']:<15} "
          f"{row['geo_dist_km']:<10.0f} {row['nean_corr']:<8.3f} "
          f"{row['nean_resid_corrected']:<8.3f} {row['nean_perm_pval']:<8.4f} {row['nean_fdr_pval']:<8.4f}")

# Neanderthal outliers: FDR significant
nean_outliers = nean_clean[nean_clean['nean_fdr_pval'] < 0.10].sort_values(
    'nean_resid_corrected', ascending=False)
print(f"\nNeanderthal FDR q<0.10 outliers (non-admixed): {len(nean_outliers)}")

# Also show admixed pairs
print("\nTop 10 Neanderthal pairs by corrected residual (admixed):")
nean_admix_top = valid_n[valid_n['any_admixed'] == 1].nlargest(10, 'nean_resid_corrected')
for _, row in nean_admix_top.iterrows():
    print(f"{row['pop1']:<20} {row['pop2']:<20} {row['region1']:<15} {row['region2']:<15} "
          f"{row['geo_dist_km']:<10.0f} {row['nean_corr']:<8.3f} "
          f"{row['nean_resid_corrected']:<8.3f} {row['nean_perm_pval']:<8.4f} {row['nean_fdr_pval']:<8.4f}")

# Denisovan outliers
print("\nTop 20 Denisovan pairs by corrected residual (non-admixed):")
deni_clean = valid_d[valid_d['any_admixed'] == 0].copy()
deni_top = deni_clean.nlargest(20, 'deni_resid_corrected')
print(f"{'Pop1':<20} {'Pop2':<20} {'Region1':<15} {'Region2':<15} "
      f"{'Dist(km)':<10} {'Corr':<8} {'Resid':<8} {'p_nom':<8} {'q_FDR':<8}")
for _, row in deni_top.iterrows():
    print(f"{row['pop1']:<20} {row['pop2']:<20} {row['region1']:<15} {row['region2']:<15} "
          f"{row['geo_dist_km']:<10.0f} {row['deni_corr']:<8.3f} "
          f"{row['deni_resid_corrected']:<8.3f} {row['deni_perm_pval']:<8.4f} {row['deni_fdr_pval']:<8.4f}")

deni_outliers = deni_clean[deni_clean['deni_fdr_pval'] < 0.10].sort_values(
    'deni_resid_corrected', ascending=False)
print(f"\nDenisovan FDR q<0.10 outliers (non-admixed): {len(deni_outliers)}")

# ===== 9. Mantel test =====
print("\n" + "=" * 60)
print("Mantel test: geographic distance matrix ~ sharing matrix")
print("=" * 60)

def mantel_test(df, pop1_col, pop2_col, dist_col, corr_col, n_perm=9999):
    """Mantel test: permute population labels (rows/columns of matrix)."""
    # Build population list
    pops = sorted(set(df[pop1_col].tolist() + df[pop2_col].tolist()))
    pop_idx = {p: i for i, p in enumerate(pops)}
    n_pops = len(pops)

    # Build symmetric matrices
    dist_mat = np.zeros((n_pops, n_pops))
    corr_mat = np.zeros((n_pops, n_pops))
    for _, row in df.iterrows():
        i, j = pop_idx[row[pop1_col]], pop_idx[row[pop2_col]]
        dist_mat[i, j] = dist_mat[j, i] = row[dist_col]
        corr_mat[i, j] = corr_mat[j, i] = row[corr_col]

    # Extract upper triangle as vectors
    tri_idx = np.triu_indices(n_pops, k=1)
    dist_vec = dist_mat[tri_idx]
    corr_vec = corr_mat[tri_idx]

    obs_r, _ = stats.pearsonr(dist_vec, corr_vec)

    # Permutation: shuffle population labels (rows/columns together)
    count = 0
    for _ in range(n_perm):
        perm = np.random.permutation(n_pops)
        perm_corr = corr_mat[np.ix_(perm, perm)]
        perm_vec = perm_corr[tri_idx]
        perm_r, _ = stats.pearsonr(dist_vec, perm_vec)
        if abs(perm_r) >= abs(obs_r):
            count += 1
    p_val = (count + 1) / (n_perm + 1)
    return obs_r, p_val

# Use non-admixed pairs only
nean_for_mantel = valid_n[valid_n['any_admixed'] == 0]
r_mantel_n, p_mantel_n = mantel_test(
    nean_for_mantel, 'pop1', 'pop2', 'geo_dist_km', 'nean_corr',
    n_perm=9999
)
print(f"Neanderthal (non-admixed): Mantel r = {r_mantel_n:.4f}, p = {p_mantel_n:.4f}")

deni_for_mantel = valid_d[valid_d['any_admixed'] == 0]
r_mantel_d, p_mantel_d = mantel_test(
    deni_for_mantel, 'pop1', 'pop2', 'geo_dist_km', 'deni_corr',
    n_perm=9999
)
print(f"Denisovan (non-admixed):   Mantel r = {r_mantel_d:.4f}, p = {p_mantel_d:.4f}")

# ===== 10. Save corrected results =====
print("\n" + "=" * 60)
print("Saving corrected results...")
print("=" * 60)

# Merge corrected data back
out_n = valid_n[['pop1', 'pop2', 'region1', 'region2', 'nean_corr', 'geo_dist_km',
                 'max_admix_eur', 'any_admixed', 'same_continent', 'continent_pair',
                 'nean_resid_uncorrected', 'nean_resid_corrected',
                 'nean_perm_pval', 'nean_fdr_pval']].copy()
out_d = valid_d[['pop1', 'pop2', 'deni_corr',
                 'deni_resid_uncorrected', 'deni_resid_corrected',
                 'deni_perm_pval', 'deni_fdr_pval']].copy()

out_d_cols = out_d.copy()
out = out_n.merge(out_d_cols, on=['pop1', 'pop2'], how='left')
out.to_csv('data/pairwise_sharing_corrected.csv', index=False)
print(f"Saved corrected results: data/pairwise_sharing_corrected.csv ({len(out)} rows)")

# Save outlier summary
all_outliers = []
for _, row in nean_outliers.iterrows():
    all_outliers.append({
        'type': 'Neanderthal', 'pop1': row['pop1'], 'pop2': row['pop2'],
        'region1': row['region1'], 'region2': row['region2'],
        'geo_dist_km': row['geo_dist_km'], 'correlation': row['nean_corr'],
        'corrected_residual': row['nean_resid_corrected'],
        'perm_pvalue': row['nean_perm_pval'], 'admixed': row['any_admixed']
    })
for _, row in deni_outliers.iterrows():
    all_outliers.append({
        'type': 'Denisovan', 'pop1': row['pop1'], 'pop2': row['pop2'],
        'region1': row['region1'], 'region2': row['region2'],
        'geo_dist_km': row['geo_dist_km'], 'correlation': row['deni_corr'],
        'corrected_residual': row['deni_resid_corrected'],
        'perm_pvalue': row['deni_perm_pval'], 'admixed': row['any_admixed']
    })
outlier_df = pd.DataFrame(all_outliers)
outlier_df.to_csv('data/outlier_summary.csv', index=False)
print(f"Saved outlier summary: data/outlier_summary.csv ({len(outlier_df)} rows)")

# Save stats summary
with open('data/correction_stats.txt', 'w') as f:
    f.write("CONFOUNDING CORRECTION STATISTICS\n")
    f.write("=" * 60 + "\n\n")

    f.write("1. Model comparison (Neanderthal)\n")
    f.write(f"   Uncorrected R²: {model_simple_n.rsquared:.4f}\n")
    f.write(f"   Corrected R²:   {model_n.rsquared:.4f}\n")
    f.write(f"   Improvement:    {model_n.rsquared - model_simple_n.rsquared:.4f}\n\n")

    f.write("2. Model comparison (Denisovan)\n")
    f.write(f"   Uncorrected R²: {model_simple_d.rsquared:.4f}\n")
    f.write(f"   Corrected R²:   {model_d.rsquared:.4f}\n")
    f.write(f"   Improvement:    {model_d.rsquared - model_simple_d.rsquared:.4f}\n\n")

    f.write("3. Partial correlations (sharing ~ distance | confounders)\n")
    f.write(f"   Neanderthal: raw r={r_nean_raw:.4f}, partial r={r_nean_partial:.4f}\n")
    f.write(f"   Denisovan:   raw r={r_deni_raw:.4f}, partial r={r_deni_partial:.4f}\n\n")

    f.write("4. Mantel test (non-admixed pairs only)\n")
    f.write(f"   Neanderthal: r={r_mantel_n:.4f}, p={p_mantel_n:.4f}\n")
    f.write(f"   Denisovan:   r={r_mantel_d:.4f}, p={p_mantel_d:.4f}\n\n")

    f.write("5. Significant outlier counts (FDR q<0.10, non-admixed)\n")
    f.write(f"   Neanderthal: {len(nean_outliers)} pairs\n")
    f.write(f"   Denisovan:   {len(deni_outliers)} pairs\n")
    f.write(f"   Neanderthal nominal p<0.05: {np.sum(nean_clean['nean_perm_pval'] < 0.05)} pairs\n")
    f.write(f"   Denisovan nominal p<0.05:   {np.sum(deni_clean['deni_perm_pval'] < 0.05)} pairs\n\n")

    f.write("6. Regression coefficients (Neanderthal)\n")
    f.write(model_n.summary().as_text() + "\n\n")

    f.write("7. Regression coefficients (Denisovan)\n")
    f.write(model_d.summary().as_text() + "\n")

print("\nAll corrections complete!")
