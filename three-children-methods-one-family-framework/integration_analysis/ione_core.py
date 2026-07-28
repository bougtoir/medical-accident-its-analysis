"""
IONE core functions (vendored from bougtoir/ione-stratification-framework).

Incoherence-Oriented Neutralisation and Extraction: stratification methods
and coherence indicators. Functions copied verbatim from the IONE repo
(methods.py, real_data_analysis.py) so the ONISHI integration analysis is
self-contained and reproducible.
"""

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_predict, KFold
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import warnings

warnings.filterwarnings('ignore')


# ------------------------------------------------------------
# Stratification methods (decision-power based + feature based)
# ------------------------------------------------------------

def method_1a(X, Y, n_strata):
    """1A: predicted probability P(Y=1|X) quantile stratification."""
    model = LogisticRegression(max_iter=1000, C=1.0, solver='lbfgs')
    model.fit(X, Y)
    p_hat = model.predict_proba(X)[:, 1]
    return _quantile_stratify(p_hat, n_strata)


def method_1b(X, Y, n_strata):
    """1B: prediction residual |Y - p_hat| stratification."""
    model = LogisticRegression(max_iter=1000, C=1.0, solver='lbfgs')
    model.fit(X, Y)
    p_hat = model.predict_proba(X)[:, 1]
    residuals = np.abs(Y - p_hat)
    return _quantile_stratify(residuals, n_strata)


def method_1c(X, Y, n_strata):
    """1C: cross-validated decision-power score."""
    model = LogisticRegression(max_iter=1000, C=1.0, solver='lbfgs')
    cv = KFold(n_splits=5, shuffle=True, random_state=42)
    p_hat_cv = cross_val_predict(model, X, Y, cv=cv, method='predict_proba')[:, 1]
    return _quantile_stratify(p_hat_cv, n_strata)


def method_1d(X, Y, n_strata):
    """1D: RF tree-variance uncertainty stratification."""
    model = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42, n_jobs=-1)
    model.fit(X, Y)
    tree_preds = np.array([tree.predict_proba(X)[:, 1] for tree in model.estimators_])
    uncertainty = np.var(tree_preds, axis=0)
    return _quantile_stratify(uncertainty, n_strata)


def method_2a(X, Y, n_strata):
    """2A: PCA composite-score stratification (Y ignored)."""
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    pca = PCA(n_components=min(3, X.shape[1]))
    scores = pca.fit_transform(X_scaled)
    weights = pca.explained_variance_ratio_
    weights = weights / weights.sum()
    score = scores @ weights
    return _quantile_stratify(score, n_strata)


def method_2b(X, Y, n_strata):
    """2B: k-means clustering stratification (Y ignored)."""
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    km = KMeans(n_clusters=n_strata, n_init=10, random_state=42)
    return km.fit_predict(X_scaled)


def _quantile_stratify(scores, n_strata):
    quantiles = np.percentile(scores, np.linspace(0, 100, n_strata + 1)[1:-1])
    return np.digitize(scores, quantiles)


ALL_METHODS = {
    '1A_predicted_prob': method_1a,
    '1B_residual': method_1b,
    '1C_cv_decision': method_1c,
    '1D_ml_uncertainty': method_1d,
    '2A_pca': method_2a,
    '2B_clustering': method_2b,
}


# ------------------------------------------------------------
# Coherence indicators (no oracle labels required)
# ------------------------------------------------------------

def compute_c1(Y, strata):
    """C1 incoherence indicator: 1 - I^2 across strata effect estimates.

    High C1 (near 1) => strata effects are coherent (low heterogeneity).
    Low C1 => residual incoherence remains (hidden structure).
    """
    unique_strata = np.unique(strata)
    if len(unique_strata) < 2:
        return 1.0
    effects, variances = [], []
    for s in unique_strata:
        mask = strata == s
        n_s = mask.sum()
        if n_s < 2:
            continue
        y_s = Y[mask]
        effects.append(y_s.mean())
        variances.append(max(y_s.var(ddof=1) / n_s, 1e-10))
    if len(effects) < 2:
        return 1.0
    effects = np.array(effects)
    variances = np.array(variances)
    weights = 1.0 / variances
    pooled = np.sum(weights * effects) / np.sum(weights)
    Q = np.sum(weights * (effects - pooled) ** 2)
    df = len(effects) - 1
    I_sq = max((Q - df) / Q, 0.0) if Q > df else 0.0
    return float(1.0 - I_sq)


def compute_c2(X, Y, strata):
    """C2 residual-structure coherence: 1 - mean systematic residual correlation."""
    unique_strata = np.unique(strata)
    systematic_component = 0.0
    total_n = 0
    for s in unique_strata:
        mask = strata == s
        n_s = mask.sum()
        if n_s < 20 or len(np.unique(Y[mask])) < 2:
            continue
        X_s, Y_s = X[mask], Y[mask]
        try:
            model = LogisticRegression(max_iter=500, C=1.0, solver='lbfgs')
            model.fit(X_s, Y_s)
            p_hat = model.predict_proba(X_s)[:, 1]
            residuals = Y_s - p_hat
            sys_var = 0.0
            for j in range(X_s.shape[1]):
                if np.std(X_s[:, j]) > 0:
                    corr = np.corrcoef(X_s[:, j], residuals)[0, 1]
                    sys_var += corr ** 2
            sys_var /= max(X_s.shape[1], 1)
            systematic_component += sys_var * n_s
            total_n += n_s
        except Exception:
            continue
    if total_n == 0:
        return 1.0
    ratio = systematic_component / total_n
    return float(1.0 - min(ratio, 1.0))


def within_stratum_homogeneity_W(Y, strata):
    """W indicator: within-stratum outcome homogeneity.

    W = 1 - (weighted mean within-stratum variance / overall variance).
    Near 1 => strata are internally homogeneous in the outcome.
    """
    overall_var = np.var(Y, ddof=1)
    if overall_var <= 0:
        return 1.0
    n = len(Y)
    within = 0.0
    for s in np.unique(strata):
        mask = strata == s
        n_s = mask.sum()
        if n_s < 2:
            continue
        within += (n_s / n) * np.var(Y[mask], ddof=1)
    return float(1.0 - min(within / overall_var, 1.0))


def stratum_effect_logor(treat, Y, strata, cc=0.5):
    """Per-stratum treatment log-OR (treat vs control) on binary Y.

    Returns list of dicts with stratum, n, event_rate, logOR, se.
    """
    out = []
    for s in np.unique(strata):
        mask = strata == s
        t = treat[mask]
        y = Y[mask]
        a = np.sum((t == 1) & (y == 1)) + cc
        b = np.sum((t == 1) & (y == 0)) + cc
        c = np.sum((t == 0) & (y == 1)) + cc
        d = np.sum((t == 0) & (y == 0)) + cc
        logor = np.log(a * d / (b * c))
        se = np.sqrt(1 / a + 1 / b + 1 / c + 1 / d)
        out.append({
            'stratum': int(s),
            'n': int(mask.sum()),
            'event_rate': float(y.mean()),
            'logOR': float(logor),
            'se': float(se),
        })
    return out
