"""
Prototype analysis: Archaic introgression segment sharing between populations
vs geographic distance — detecting long-distance human movement signals.

Approach:
1. Bin the genome into 500kb windows
2. For each population, compute frequency of archaic introgression in each bin
3. Calculate pairwise correlation of introgression profiles between populations
4. Compare to geographic distance
5. Identify outlier pairs (unexpectedly high sharing given distance)
"""

import pandas as pd
import numpy as np
from collections import defaultdict
from itertools import combinations
import warnings
warnings.filterwarnings('ignore')

print("=" * 60)
print("Loading data...")
print("=" * 60)

# Load both datasets
cols_needed = ['name', 'pop', 'region', 'chrom', 'start', 'end', 'mean_prob', 'ND_type']

df_1kg = pd.read_csv('hg38_1000g_segments.txt', sep='\t', usecols=cols_needed)
df_hgdp = pd.read_csv('hg38_HGDP_segments.txt', sep='\t', usecols=cols_needed)

# Combine
df = pd.concat([df_1kg, df_hgdp], ignore_index=True)
print(f"Total segments: {len(df):,}")
print(f"Total individuals: {df['name'].nunique()}")
print(f"Total populations: {df['pop'].nunique()}")

# Filter: high-confidence archaic segments only
df = df[df['mean_prob'] >= 0.8].copy()
print(f"After prob >= 0.8 filter: {len(df):,}")

# Separate Neanderthal and Denisovan
df_nean = df[df['ND_type'].isin(['Neanderthal', 'Both'])].copy()
df_deni = df[df['ND_type'].isin(['Denisova', 'Both'])].copy()
print(f"Neanderthal segments: {len(df_nean):,}")
print(f"Denisovan segments: {len(df_deni):,}")

# ===== Bin the genome =====
BIN_SIZE = 500_000  # 500kb bins

# Chromosome sizes (hg38 approximate)
chrom_sizes = {
    'chr1': 248956422, 'chr2': 242193529, 'chr3': 198295559,
    'chr4': 190214555, 'chr5': 181538259, 'chr6': 170805979,
    'chr7': 159345973, 'chr8': 145138636, 'chr9': 138394717,
    'chr10': 133797422, 'chr11': 135086622, 'chr12': 133275309,
    'chr13': 114364328, 'chr14': 107043718, 'chr15': 101991189,
    'chr16': 90338345, 'chr17': 83257441, 'chr18': 80373285,
    'chr19': 58617616, 'chr20': 64444167, 'chr21': 46709983,
    'chr22': 50818468,
}

# Create bin index
bin_labels = []
for chrom in sorted(chrom_sizes.keys(), key=lambda x: int(x.replace('chr',''))):
    n_bins = chrom_sizes[chrom] // BIN_SIZE + 1
    for i in range(n_bins):
        bin_labels.append((chrom, i * BIN_SIZE))
total_bins = len(bin_labels)
print(f"Total genomic bins ({BIN_SIZE//1000}kb): {total_bins}")

# Create bin lookup
bin_to_idx = {b: i for i, b in enumerate(bin_labels)}

def segments_to_bin_vector(seg_df, pop_name, individuals_in_pop):
    """Convert segments for a population to a frequency vector across bins."""
    vec = np.zeros(total_bins, dtype=np.float32)
    n_ind = len(individuals_in_pop)
    if n_ind == 0:
        return vec
    
    for _, row in seg_df.iterrows():
        chrom = row['chrom']
        if chrom not in chrom_sizes:
            continue
        start_bin = row['start'] // BIN_SIZE
        end_bin = row['end'] // BIN_SIZE
        for b in range(start_bin, end_bin + 1):
            key = (chrom, b * BIN_SIZE)
            if key in bin_to_idx:
                vec[bin_to_idx[key]] += 1
    
    # Normalize by number of individuals * 2 (diploid)
    vec /= (n_ind * 2)
    return vec

print("\n" + "=" * 60)
print("Computing population-level introgression profiles...")
print("=" * 60)

# Get population list with enough individuals
pop_ind_counts = df.groupby('pop')['name'].nunique()
valid_pops = pop_ind_counts[pop_ind_counts >= 7].index.tolist()
print(f"Populations with >= 7 individuals: {len(valid_pops)}")

# For speed: use vectorized binning instead of row iteration
def fast_segments_to_bins(seg_df, n_individuals):
    """Vectorized bin computation."""
    vec = np.zeros(total_bins, dtype=np.float64)
    if n_individuals == 0 or len(seg_df) == 0:
        return vec
    
    for chrom in seg_df['chrom'].unique():
        if chrom not in chrom_sizes:
            continue
        chrom_segs = seg_df[seg_df['chrom'] == chrom]
        chrom_offset = bin_to_idx.get((chrom, 0))
        if chrom_offset is None:
            continue
        max_bin_in_chrom = chrom_sizes[chrom] // BIN_SIZE
        
        starts = (chrom_segs['start'].values // BIN_SIZE).astype(int)
        ends = (chrom_segs['end'].values // BIN_SIZE).astype(int)
        
        for s, e in zip(starts, ends):
            for b in range(s, min(e + 1, max_bin_in_chrom + 1)):
                idx = chrom_offset + b
                if idx < total_bins:
                    vec[idx] += 1
    
    vec /= (n_individuals * 2)
    return vec

# Compute profiles for Neanderthal
nean_profiles = {}
deni_profiles = {}
pop_regions = {}
pop_sizes = {}

for pop in valid_pops:
    pop_data = df[df['pop'] == pop]
    n_ind = pop_data['name'].nunique()
    region = pop_data['region'].iloc[0]
    pop_regions[pop] = region
    pop_sizes[pop] = n_ind
    
    # Neanderthal profile
    pop_nean = df_nean[df_nean['pop'] == pop]
    nean_profiles[pop] = fast_segments_to_bins(pop_nean, n_ind)
    
    # Denisovan profile
    pop_deni = df_deni[df_deni['pop'] == pop]
    deni_profiles[pop] = fast_segments_to_bins(pop_deni, n_ind)
    
    print(f"  {pop} ({region}): {n_ind} ind, "
          f"Nean bins={np.sum(nean_profiles[pop] > 0)}, "
          f"Deni bins={np.sum(deni_profiles[pop] > 0)}")

print(f"\nDone. {len(valid_pops)} populations processed.")

# ===== Geographic coordinates for populations =====
pop_coords = {
    # 1000 Genomes
    'GBR': (51.5, -0.1), 'FIN': (61.0, 25.0), 'IBS': (40.0, -4.0),
    'CEU': (49.0, 8.0), 'TSI': (43.5, 11.0),
    'CHB': (39.9, 116.4), 'CHS': (23.1, 113.3), 'CDX': (22.0, 100.0),
    'KHV': (16.0, 106.0), 'JPT': (35.7, 139.7),
    'PUR': (18.2, -66.5), 'CLM': (4.7, -74.1), 'PEL': (-12.0, -77.0),
    'MXL': (23.6, -102.6),
    'PJL': (31.5, 73.0), 'BEB': (23.7, 90.4), 'STU': (7.9, 80.7),
    'ITU': (13.1, 80.3), 'GIH': (23.0, 72.6),
    # HGDP
    'French': (46.0, 2.0), 'Sardinian': (40.0, 9.0), 'Orcadian': (59.0, -3.0),
    'Russian': (55.0, 37.5), 'BergamoItalian': (45.7, 9.7),
    'Tuscan': (43.3, 11.3), 'Basque': (43.0, -2.0), 'Adygei': (44.5, 40.0),
    'Druze': (32.5, 35.5), 'Bedouin': (30.0, 35.0), 'Palestinian': (31.9, 35.2),
    'Mozabite': (32.5, 3.7),
    'Brahui': (28.0, 66.0), 'Balochi': (28.0, 66.5), 'Hazara': (34.5, 67.0),
    'Makrani': (26.0, 63.0), 'Sindhi': (25.4, 68.4), 'Pathan': (34.0, 71.5),
    'Kalash': (35.7, 71.5), 'Burusho': (36.3, 74.6), 'Uygur': (41.0, 80.0),
    'Cambodian': (11.5, 105.0), 'Japanese': (35.7, 139.7),
    'Han': (39.9, 116.4), 'Yakut': (62.0, 130.0),
    'Tujia': (29.0, 109.0), 'Yi': (27.0, 102.0), 'Miao': (27.0, 109.0),
    'Oroqen': (50.5, 126.0), 'Daur': (48.5, 124.0), 'Mongolian': (47.0, 107.0),
    'Hezhen': (47.7, 132.0), 'Xibo': (44.0, 81.0), 'NorthernHan': (39.9, 116.4),
    'Dai': (21.0, 100.0), 'Lahu': (22.5, 100.5), 'She': (27.0, 119.0),
    'Naxi': (27.0, 100.0), 'Tu': (36.5, 102.0),
    'Colombian': (2.0, -76.0), 'Surui': (-11.0, -61.0), 'Maya': (17.0, -89.0),
    'Karitiana': (-10.0, -63.0), 'Pima': (28.0, -109.0),
    'Bougainville': (-6.2, 155.5), 'PapuanSepik': (-4.0, 143.0),
    'PapuanHighlands': (-6.0, 145.0),
}

# Haversine distance
def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    lat1, lat2, lon1, lon2 = map(np.radians, [lat1, lat2, lon1, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat/2)**2 + np.cos(lat1)*np.cos(lat2)*np.sin(dlon/2)**2
    return 2 * R * np.arcsin(np.sqrt(a))

# ===== Pairwise sharing analysis =====
print("\n" + "=" * 60)
print("Computing pairwise sharing...")
print("=" * 60)

results = []
pops_with_coords = [p for p in valid_pops if p in pop_coords]
print(f"Populations with coordinates: {len(pops_with_coords)}")

for i, pop1 in enumerate(pops_with_coords):
    for pop2 in pops_with_coords[i+1:]:
        # Neanderthal correlation
        v1 = nean_profiles[pop1]
        v2 = nean_profiles[pop2]
        # Use correlation on non-zero bins
        mask = (v1 > 0) | (v2 > 0)
        if mask.sum() > 100:
            nean_corr = np.corrcoef(v1[mask], v2[mask])[0, 1]
        else:
            nean_corr = np.nan
        
        # Denisovan correlation
        v1d = deni_profiles[pop1]
        v2d = deni_profiles[pop2]
        mask_d = (v1d > 0) | (v2d > 0)
        if mask_d.sum() > 50:
            deni_corr = np.corrcoef(v1d[mask_d], v2d[mask_d])[0, 1]
        else:
            deni_corr = np.nan
        
        # Geographic distance
        c1 = pop_coords[pop1]
        c2 = pop_coords[pop2]
        dist = haversine(c1[0], c1[1], c2[0], c2[1])
        
        results.append({
            'pop1': pop1, 'pop2': pop2,
            'region1': pop_regions[pop1], 'region2': pop_regions[pop2],
            'nean_corr': nean_corr, 'deni_corr': deni_corr,
            'geo_dist_km': dist,
        })

res_df = pd.DataFrame(results)
print(f"Total pairs: {len(res_df)}")

# Save results
res_df.to_csv('pairwise_sharing.csv', index=False)
print("Saved to pairwise_sharing.csv")

# ===== Find outliers: high sharing despite distance =====
print("\n" + "=" * 60)
print("Identifying outlier pairs (Neanderthal)...")
print("=" * 60)

valid = res_df.dropna(subset=['nean_corr'])

# Fit simple linear regression: nean_corr ~ geo_dist
from numpy.polynomial import polynomial as P
x = valid['geo_dist_km'].values
y = valid['nean_corr'].values
coeffs = np.polyfit(x, y, 1)
predicted = np.polyval(coeffs, x)
residuals = y - predicted
valid = valid.copy()
valid['nean_residual'] = residuals

# Top outliers: much higher sharing than expected
top_outliers = valid.nlargest(20, 'nean_residual')
print("\nTop 20 pairs with HIGHER Neanderthal sharing than expected by distance:")
print(f"{'Pop1':<20} {'Pop2':<20} {'Region1':<15} {'Region2':<15} {'Dist(km)':<10} {'Corr':<8} {'Residual':<8}")
for _, row in top_outliers.iterrows():
    print(f"{row['pop1']:<20} {row['pop2']:<20} {row['region1']:<15} {row['region2']:<15} {row['geo_dist_km']:<10.0f} {row['nean_corr']:<8.3f} {row['nean_residual']:<8.3f}")

# Denisovan outliers
print("\n" + "=" * 60)
print("Identifying outlier pairs (Denisovan)...")
print("=" * 60)

valid_d = res_df.dropna(subset=['deni_corr'])
if len(valid_d) > 10:
    x_d = valid_d['geo_dist_km'].values
    y_d = valid_d['deni_corr'].values
    coeffs_d = np.polyfit(x_d, y_d, 1)
    predicted_d = np.polyval(coeffs_d, x_d)
    residuals_d = y_d - predicted_d
    valid_d = valid_d.copy()
    valid_d['deni_residual'] = residuals_d
    
    top_outliers_d = valid_d.nlargest(20, 'deni_residual')
    print("\nTop 20 pairs with HIGHER Denisovan sharing than expected by distance:")
    print(f"{'Pop1':<20} {'Pop2':<20} {'Region1':<15} {'Region2':<15} {'Dist(km)':<10} {'Corr':<8} {'Residual':<8}")
    for _, row in top_outliers_d.iterrows():
        print(f"{row['pop1']:<20} {row['pop2']:<20} {row['region1']:<15} {row['region2']:<15} {row['geo_dist_km']:<10.0f} {row['deni_corr']:<8.3f} {row['deni_residual']:<8.3f}")

# Also show inter-regional high-sharing pairs specifically
print("\n" + "=" * 60)
print("INTER-REGIONAL pairs with high Neanderthal sharing (potential long-distance movement):")
print("=" * 60)

inter = valid[valid['region1'] != valid['region2']].nlargest(15, 'nean_residual')
print(f"{'Pop1':<20} {'Pop2':<20} {'Region1':<20} {'Region2':<20} {'Dist(km)':<10} {'Corr':<8} {'Resid':<8}")
for _, row in inter.iterrows():
    print(f"{row['pop1']:<20} {row['pop2']:<20} {row['region1']:<20} {row['region2']:<20} {row['geo_dist_km']:<10.0f} {row['nean_corr']:<8.3f} {row['nean_residual']:<8.3f}")

print("\nDone! Now generating visualizations...")
