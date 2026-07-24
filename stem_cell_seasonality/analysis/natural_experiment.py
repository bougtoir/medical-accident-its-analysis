#!/usr/bin/env python3
"""
Natural Experiment: Academic Year Start as Instrument for Separating
Biological vs Institutional Seasonality in GEO PSC Data.

Hypothesis:
- If March peak is driven by academic calendar (year-end rush), then:
  * Japan/Korea (April start → year-end = Feb-Mar) should peak Feb-Mar
  * USA/UK/Germany (Sep-Oct start → year-end = Jun-Aug) should peak Jun-Aug
  * Australia (Jan-Feb start + Southern Hemisphere) should peak Nov-Dec
- If March peak is biological (photoperiod-driven):
  * Northern Hemisphere countries should ALL peak ~Mar regardless of academic year
  * Australia (SH) should show INVERTED pattern (peak ~Sep)

Design:
- Group 1 (April start): Japan, South Korea
- Group 2 (Sep/Oct start): USA, UK, Germany, China, France, Italy, Spain, etc.
- Group 3 (Jan/Feb start + SH): Australia, New Zealand, Brazil, South Africa
"""

import os

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output")

# Academic year groupings
MARCH_APRIL_START = {"Japan", "South Korea"}  # March/April academic year
SEPT_OCT_START_NH = {"USA", "United Kingdom", "Germany", "China", "France",
                     "Italy", "Spain", "Canada", "Netherlands", "Belgium",
                     "Switzerland", "Sweden", "Denmark", "Austria", "Finland",
                     "Norway", "Ireland", "Israel", "Singapore", "Taiwan",
                     "Poland", "Czech Republic", "Portugal", "Hong Kong"}
JAN_FEB_START_SH = {"Australia", "New Zealand", "Brazil", "South Africa",
                    "Argentina", "Chile"}

MONTH_LABELS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def load_data():
    """Load GEO metadata merged with country data."""
    geo = pd.read_csv(os.path.join(OUTPUT_DIR, "geo_psc_metadata.csv"))
    geo["date"] = pd.to_datetime(geo["date"])

    country_file = os.path.join(OUTPUT_DIR, "geo_country_full.csv")
    countries = pd.read_csv(country_file)
    country_map = dict(zip(countries["accession"], countries["country"]))
    geo["country"] = geo["accession"].map(country_map)

    print(f"Total GEO records: {len(geo)}")
    print(f"Records with country: {geo['country'].notna().sum()}")
    return geo


def assign_academic_group(country):
    """Assign academic year group based on country."""
    if not isinstance(country, str):
        return None
    c = country.strip()
    if c in MARCH_APRIL_START:
        return "Mar/Apr-start (JP/KR)"
    elif c in SEPT_OCT_START_NH:
        return "Sep/Oct-start (US/EU/CN)"
    elif c in JAN_FEB_START_SH:
        return "Jan/Feb-start (AU/NZ/BR, SH)"
    return None


def chi2_uniformity(counts_12):
    """Chi-square test for uniformity across 12 months."""
    observed = np.array([counts_12.get(m, 0) for m in range(1, 13)])
    expected = np.full(12, observed.sum() / 12)
    chi2, p = stats.chisquare(observed, expected)
    return chi2, p


def rayleigh_test(months):
    """Rayleigh test for circular uniformity (month as circular variable)."""
    theta = 2 * np.pi * (np.array(months) - 1) / 12
    n = len(theta)
    C = np.sum(np.cos(theta))
    S = np.sum(np.sin(theta))
    R = np.sqrt(C**2 + S**2) / n
    # Rayleigh statistic
    Z = n * R**2
    p = np.exp(-Z)  # approximation valid for large n
    # Mean direction (peak month)
    mean_angle = np.arctan2(S/n, C/n)
    if mean_angle < 0:
        mean_angle += 2 * np.pi
    peak_month = mean_angle / (2 * np.pi) * 12 + 1
    return R, Z, p, peak_month


def analyze_groups(geo):
    """Main analysis: compare monthly distributions across academic year groups."""
    geo["acad_group"] = geo["country"].apply(assign_academic_group)

    grouped = geo[geo["acad_group"].notna()].copy()
    print(f"\nRecords assigned to academic groups: {len(grouped)}")
    print(grouped["acad_group"].value_counts().to_string())
    print()

    results = {}
    for group_name, gdf in grouped.groupby("acad_group"):
        month_counts = gdf.groupby("month").size()
        n = len(gdf)

        chi2, p_chi2 = chi2_uniformity(month_counts)
        R, Z, p_ray, peak_month = rayleigh_test(gdf["month"].values)

        peak_m = month_counts.idxmax()
        trough_m = month_counts.idxmin()

        results[group_name] = {
            "n": n,
            "chi2": chi2,
            "p_chi2": p_chi2,
            "rayleigh_R": R,
            "rayleigh_Z": Z,
            "p_rayleigh": p_ray,
            "circular_peak": peak_month,
            "mode_month": peak_m,
            "trough_month": trough_m,
            "month_counts": month_counts,
        }

        print(f"── {group_name} (n={n}) ──")
        print(f"  χ² = {chi2:.1f}, p = {p_chi2:.4f}")
        print(f"  Rayleigh R = {R:.3f}, Z = {Z:.1f}, p = {p_ray:.4f}")
        print(f"  Peak month (mode): {MONTH_LABELS[peak_m-1]}")
        print(f"  Circular mean peak: {peak_month:.1f} ({MONTH_LABELS[int(peak_month-1) % 12]})")
        print(f"  Trough month: {MONTH_LABELS[trough_m-1]}")
        print()

    return results, grouped


def country_level_detail(geo):
    """Per-country breakdown for top countries."""
    countries_of_interest = ["Japan", "South Korea", "USA", "United Kingdom",
                            "Germany", "China", "Australia"]
    geo_filtered = geo[geo["country"].isin(countries_of_interest)].copy()

    print("\n── Per-country monthly peaks ──")
    country_stats = []
    for country in countries_of_interest:
        cdf = geo_filtered[geo_filtered["country"] == country]
        if len(cdf) < 10:
            continue
        month_counts = cdf.groupby("month").size()
        R, Z, p_ray, peak_month = rayleigh_test(cdf["month"].values)
        peak_m = month_counts.idxmax()
        country_stats.append({
            "country": country,
            "n": len(cdf),
            "mode_month": peak_m,
            "mode_label": MONTH_LABELS[peak_m-1],
            "circular_peak": peak_month,
            "rayleigh_R": R,
            "p_rayleigh": p_ray,
        })
        print(f"  {country:20s} (n={len(cdf):4d}): peak={MONTH_LABELS[peak_m-1]:3s}, "
              f"circular={peak_month:.1f}, R={R:.3f}, p={p_ray:.4f}")

    return pd.DataFrame(country_stats)


def generate_figure(results, geo, country_stats):
    """Generate comprehensive natural experiment figure."""
    fig = plt.figure(figsize=(16, 14))
    fig.suptitle("Natural Experiment: Academic Calendar vs Biological Seasonality\n"
                 "in GEO PSC Differentiation Datasets",
                 fontsize=14, fontweight='bold', y=0.98)

    # Panel A: Overlaid normalized monthly distributions by academic group
    ax1 = fig.add_subplot(2, 2, 1)
    colors = {"Mar/Apr-start (JP/KR)": "#E63946",
              "Sep/Oct-start (US/EU/CN)": "#457B9D",
              "Jan/Feb-start (AU/NZ/BR, SH)": "#2A9D8F"}
    markers = {"Mar/Apr-start (JP/KR)": "o",
               "Sep/Oct-start (US/EU/CN)": "s",
               "Jan/Feb-start (AU/NZ/BR, SH)": "D"}

    for group_name in sorted(results.keys()):
        r = results[group_name]
        mc = r["month_counts"]
        norm = mc / mc.sum()
        vals = [norm.get(m, 0) for m in range(1, 13)]
        ax1.plot(range(1, 13), vals, f'-{markers[group_name]}',
                color=colors[group_name], linewidth=2, markersize=7,
                label=f"{group_name} (n={r['n']})")

    ax1.axhline(1/12, color='gray', linestyle=':', linewidth=1, alpha=0.7,
               label="Uniform expectation")
    ax1.set_xlabel("Month", fontsize=10)
    ax1.set_ylabel("Proportion of datasets", fontsize=10)
    ax1.set_title("A. Monthly distribution by academic year group", fontsize=11, fontweight='bold')
    ax1.set_xticks(range(1, 13))
    ax1.set_xticklabels(MONTH_LABELS, fontsize=9)
    ax1.legend(fontsize=8, loc='upper right')
    ax1.set_ylim(0, None)

    # Panel B: Per-country bar chart (heatmap-style)
    ax2 = fig.add_subplot(2, 2, 2)
    countries_order = ["Japan", "South Korea", "USA", "United Kingdom",
                       "Germany", "China", "Australia"]
    acad_year_labels = ["Apr", "Mar", "Sep", "Sep", "Oct", "Sep", "Jan"]
    hemi_labels = ["NH", "NH", "NH", "NH", "NH", "NH", "SH"]

    heatmap_data = []
    for country in countries_order:
        cdf = geo[geo["country"] == country]
        if len(cdf) < 10:
            heatmap_data.append([0]*12)
            continue
        mc = cdf.groupby("month").size()
        norm = mc / mc.sum()
        heatmap_data.append([norm.get(m, 0) for m in range(1, 13)])

    heatmap_arr = np.array(heatmap_data)
    im = ax2.imshow(heatmap_arr, aspect='auto', cmap='YlOrRd', interpolation='nearest')
    ax2.set_xticks(range(12))
    ax2.set_xticklabels(MONTH_LABELS, fontsize=8)
    ax2.set_yticks(range(len(countries_order)))
    ylabels = [f"{c} ({a},{h})" for c, a, h in
               zip(countries_order, acad_year_labels, hemi_labels)]
    ax2.set_yticklabels(ylabels, fontsize=9)
    ax2.set_title("B. Monthly proportion heatmap by country\n"
                  "(academic year start, hemisphere)", fontsize=11, fontweight='bold')
    plt.colorbar(im, ax=ax2, label="Proportion", shrink=0.8)

    # Mark peak month for each country
    for i, row in enumerate(heatmap_data):
        if sum(row) > 0:
            peak_idx = np.argmax(row)
            ax2.plot(peak_idx, i, 'k*', markersize=12)

    # Panel C: Circular peak month comparison
    ax3 = fig.add_subplot(2, 2, 3, polar=True)
    for group_name in sorted(results.keys()):
        r = results[group_name]
        peak_rad = 2 * np.pi * (r["circular_peak"] - 1) / 12
        ax3.arrow(0, 0, peak_rad, r["rayleigh_R"] * 0.9,
                 head_width=0.1, head_length=0.03,
                 fc=colors[group_name], ec=colors[group_name], linewidth=2)
        ax3.annotate(f"{group_name.split('(')[1].rstrip(')')}\n(R={r['rayleigh_R']:.2f})",
                    xy=(peak_rad, r["rayleigh_R"]),
                    fontsize=7, ha='center', color=colors[group_name])

    ax3.set_theta_zero_location('N')  # January at top
    ax3.set_theta_direction(-1)  # Clockwise
    ax3.set_xticks(np.linspace(0, 2*np.pi, 12, endpoint=False))
    ax3.set_xticklabels(MONTH_LABELS, fontsize=8)
    ax3.set_ylim(0, 0.25)
    ax3.set_title("C. Circular mean direction (peak month)\n"
                  "by academic year group", fontsize=11, fontweight='bold', pad=20)

    # Panel D: Statistical summary table
    ax4 = fig.add_subplot(2, 2, 4)
    ax4.axis('off')

    # Interpretation text
    interpretation = []
    # Check if April-start and Sep-start have similar peaks
    apr_peak = results.get("Mar/Apr-start (JP/KR)", {}).get("circular_peak", 0)
    sep_peak = results.get("Sep/Oct-start (US/EU/CN)", {}).get("circular_peak", 0)
    sh_peak = results.get("Jan/Feb-start (AU/NZ/BR, SH)", {}).get("circular_peak", 0)

    # Determine interpretation (use circular distance for month comparison)
    diff_apr_sep = abs(apr_peak - sep_peak)
    circ_diff_apr_sep = min(diff_apr_sep, 12 - diff_apr_sep)
    if circ_diff_apr_sep < 2:
        interpretation.append("• JP/KR and US/EU peaks are SIMILAR (~same month)")
        interpretation.append("  → Inconsistent with pure academic-calendar hypothesis")
        interpretation.append("  → Suggests shared external driver (photoperiod?)")
    else:
        interpretation.append(f"• JP/KR peak ({apr_peak:.1f}) differs from US/EU ({sep_peak:.1f})")
        interpretation.append("  → Consistent with academic-calendar effect")

    if sh_peak > 0:
        diff_sh_nh = abs(sh_peak - apr_peak)
        circ_diff_sh = min(diff_sh_nh, 12 - diff_sh_nh)
        if circ_diff_sh > 3:
            interpretation.append(f"• SH peak ({sh_peak:.1f}) differs from NH ({apr_peak:.1f})")
            interpretation.append("  → Possible hemisphere effect (photoperiod)")
        else:
            interpretation.append(f"• SH peak ({sh_peak:.1f}) similar to NH ({apr_peak:.1f})")
            interpretation.append("  → No hemisphere inversion detected")

    # Table data
    table_data = []
    for gname in sorted(results.keys()):
        r = results[gname]
        sig = "***" if r["p_chi2"] < 0.001 else "**" if r["p_chi2"] < 0.01 else "*" if r["p_chi2"] < 0.05 else "ns"
        table_data.append([
            gname.split("(")[1].rstrip(")"),
            str(r["n"]),
            MONTH_LABELS[r["mode_month"]-1],
            f"{r['circular_peak']:.1f}",
            f"{r['rayleigh_R']:.3f}",
            f"{r['p_chi2']:.1e} {sig}",
        ])

    table = ax4.table(cellText=table_data,
                     colLabels=["Group", "n", "Peak\n(mode)", "Peak\n(circular)", "Rayleigh\nR", "χ² p-value"],
                     loc='upper center', cellLoc='center')
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1.2, 1.5)

    # Add interpretation below table
    interp_text = "\n".join(interpretation)
    ax4.text(0.5, 0.15, "Interpretation:\n" + interp_text,
            transform=ax4.transAxes, fontsize=9, va='top', ha='center',
            bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8),
            family='monospace')

    ax4.set_title("D. Statistical summary & interpretation", fontsize=11, fontweight='bold')

    plt.tight_layout(rect=[0, 0, 1, 0.95])

    fig_path = os.path.join(OUTPUT_DIR, "natural_experiment_figure.png")
    plt.savefig(fig_path, dpi=200, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"\nFigure saved: {fig_path}")
    return fig_path


def write_report(results, country_stats_df, geo):
    """Write analysis report."""
    report_path = os.path.join(OUTPUT_DIR, "natural_experiment_report.md")

    grouped = geo[geo["acad_group"].notna()]

    with open(report_path, "w") as f:
        f.write("# Natural Experiment: Academic Calendar vs Biological Seasonality\n\n")
        f.write("## Design\n\n")
        f.write("Using geographic variation in academic year start months as a natural\n")
        f.write("instrument to separate institutional from biological drivers of seasonality\n")
        f.write("in GEO PSC differentiation dataset submissions.\n\n")
        f.write("| Group | Countries | Academic Year Start | Hemisphere | n |\n")
        f.write("|-------|-----------|--------------------|-----------:|--:|\n")
        for gname in sorted(results.keys()):
            r = results[gname]
            if "Mar/Apr" in gname:
                countries_str = "Japan, South Korea"
                start = "Mar/Apr"
                hemi = "NH"
            elif "Sep" in gname:
                countries_str = "USA, UK, Germany, China, ..."
                start = "Sep/Oct"
                hemi = "NH"
            else:
                countries_str = "Australia, NZ, Brazil, ..."
                start = "Jan/Feb"
                hemi = "SH"
            f.write(f"| {gname} | {countries_str} | {start} | {hemi} | {r['n']} |\n")

        f.write("\n## Results\n\n")
        f.write("### Group-level Statistics\n\n")
        f.write("| Group | n | Peak (mode) | Circular peak | Rayleigh R | χ² | p |\n")
        f.write("|-------|---:|:---:|:---:|:---:|---:|---:|\n")
        for gname in sorted(results.keys()):
            r = results[gname]
            f.write(f"| {gname} | {r['n']} | {MONTH_LABELS[r['mode_month']-1]} | "
                    f"{r['circular_peak']:.1f} | {r['rayleigh_R']:.3f} | "
                    f"{r['chi2']:.1f} | {r['p_chi2']:.4f} |\n")

        f.write("\n### Per-Country Detail\n\n")
        f.write("| Country | Acad Start | Hemisphere | n | Peak (mode) | Circular peak | R |\n")
        f.write("|---------|:---:|:---:|---:|:---:|:---:|:---:|\n")
        acad_starts = {"Japan": "Apr", "South Korea": "Mar", "USA": "Sep",
                       "United Kingdom": "Sep", "Germany": "Oct", "China": "Sep",
                       "Australia": "Jan"}
        hemispheres = {"Japan": "NH", "South Korea": "NH", "USA": "NH",
                       "United Kingdom": "NH", "Germany": "NH", "China": "NH",
                       "Australia": "SH"}
        for _, row in country_stats_df.iterrows():
            c = row["country"]
            f.write(f"| {c} | {acad_starts.get(c, '?')} | {hemispheres.get(c, '?')} | "
                    f"{row['n']} | {row['mode_label']} | {row['circular_peak']:.1f} | "
                    f"{row['rayleigh_R']:.3f} |\n")

        f.write("\n## Interpretation\n\n")

        apr_peak = results.get("Mar/Apr-start (JP/KR)", {}).get("circular_peak", 0)
        sep_peak = results.get("Sep/Oct-start (US/EU/CN)", {}).get("circular_peak", 0)
        sh_peak = results.get("Jan/Feb-start (AU/NZ/BR, SH)", {}).get("circular_peak", 0)

        diff_apr_sep = abs(apr_peak - sep_peak)
        circ_diff = min(diff_apr_sep, 12 - diff_apr_sep)
        if circ_diff < 2:
            f.write("**Key finding**: Japan/Korea (March/April academic year) and USA/Europe "
                    "(September academic year) show similar peak months in GEO submissions. "
                    "This is **inconsistent with a pure academic-calendar explanation** and "
                    "suggests a shared external driver.\n\n")
        else:
            f.write(f"**Key finding**: Peak months differ between Mar/Apr-start ({apr_peak:.1f}) "
                    f"and Sep-start ({sep_peak:.1f}) groups. This pattern is "
                    f"**partially consistent with academic-calendar effects**.\n\n")

        if sh_peak > 0:
            diff_sh_nh = abs(apr_peak - sh_peak)
            circ_diff_sh = min(diff_sh_nh, 12 - diff_sh_nh)
            if circ_diff_sh > 3:
                f.write("The Southern Hemisphere group shows a shifted peak, potentially "
                        "consistent with hemisphere inversion (photoperiod hypothesis). "
                        "However, sample size is small and interpretation requires caution.\n\n")
            else:
                f.write("The Southern Hemisphere group does NOT show clear inversion of peak month. "
                        "This may reflect small sample size or dominant institutional effects.\n\n")

        f.write("### Limitations\n\n")
        f.write("1. GEO submission date ≠ experiment date (6–18 month lag)\n")
        f.write("2. Southern Hemisphere sample is very small\n")
        f.write("3. Multiple confounders (funding cycles, conference deadlines, etc.)\n")
        f.write("4. Rayleigh test assumes unimodal circular distribution\n")

    print(f"Report saved: {report_path}")
    return report_path


def main():
    geo = load_data()
    geo["acad_group"] = geo["country"].apply(assign_academic_group)

    results, grouped = analyze_groups(geo)
    country_stats_df = country_level_detail(geo)
    fig_path = generate_figure(results, geo, country_stats_df)
    report_path = write_report(results, country_stats_df, geo)

    print("\n" + "="*60)
    print("NATURAL EXPERIMENT ANALYSIS COMPLETE")
    print("="*60)


if __name__ == "__main__":
    main()
