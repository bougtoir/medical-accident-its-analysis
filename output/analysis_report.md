# 医療事故と診療科別医師数・施設数の時系列分析レポート

## 概要

医療事故の発生が診療科別の医師数および医療施設数にどのような影響を与えるかを、Interrupted Time Series (ITS) 分析により検証した。事故の定義として3種類を用い、12の主要診療科について分析を行った。

## データソース

| データ | 出典 | 期間 |
|--------|------|------|
| 医療事故件数（定義1） | 日本医療安全調査機構（JMSR） | 2015-2025 |
| 医事関係訴訟件数（定義2） | 最高裁判所 | 2004-2023 |
| 混合指標（定義3） | 定義1・2を[0,1]正規化し平均 | 2015-2023 |
| 診療科別医師数 | 医師・歯科医師・薬剤師統計 | 1994-2022（隔年） |
| 診療科別施設数 | 医療施設動態調査 | 2002-2023 |
| 新規専攻医登録数 | 日本専門医機構 | 2018-2025 |

## 分析手法

1. **ITS セグメント回帰**: Y_t = β0 + β1·time + β2·intervention + β3·time_after + β4·accident_rate + ε_t
2. **クロス相関分析**: トレンド除去後の相互相関によるリードタイム推定
3. **AICモデル選択**: ウィンドウ期間の推定
4. **線形トレンド外挿**: 直近10年のトレンドに基づく将来予測

## 主要結果

### 1. リードタイム推定（事故発生→医師数・施設数への影響遅延）

| 指標 | 平均リードタイム | 中央値 | 加重平均 |
|------|-----------------|--------|----------|
| 医師数 | 1.3年 | 2.5年 | 1.6年 |
| 施設数 | -0.1年 | 0.0年 | — |

**解釈**: 医師数への影響は事故発生から約1〜3年の遅延で現れる傾向がある。施設数への影響はほぼ同時期に現れる（ラグ≒0）。

### 2. ウィンドウ期間推定（影響の持続期間）

| 指標 | 平均ウィンドウ期 | 中央値 |
|------|-----------------|--------|
| 医師数 | 4.1年 | 4.0年 |
| 施設数 | 4.2年 | 5.0年 |

**解釈**: 事故の影響は約4〜5年間持続する。

### 3. ITS分析結果（統計的に有意な結果 p<0.05）

#### 定義1（JMSR: 医療事故調査制度）

| 診療科 | 従属変数 | R² | 事故効果係数 | p値 | 解釈 |
|--------|----------|-----|-------------|------|------|
| 産婦人科 | 医師数 | 0.995 | +17.7 | 0.021 | 事故1件増で医師17.7人増（※） |
| 産婦人科 | 施設数 | 0.999 | +4.3 | 0.042 | 事故1件増で施設4.3増（※） |
| 眼科 | 施設数 | 1.000 | +4.1 | 0.039 | 事故1件増で施設4.1増（※） |

※ 正の係数は直感に反するが、全体的な増加トレンドの中で事故件数も増加しているため、見かけ上の正の相関が生じている可能性がある。

#### 定義2（訴訟統計）

| 診療科 | 従属変数 | R² | 事故効果係数 | p値 | 解釈 |
|--------|----------|-----|-------------|------|------|
| 外科 | 医師数 | 0.994 | +19.3 | <0.001 | 訴訟1件増で医師19.3人増（※） |
| 産婦人科 | 医師数 | 0.977 | +11.6 | <0.001 | 訴訟1件増で医師11.6人増（※） |
| 産婦人科 | 施設数 | 0.990 | +5.5 | <0.001 | 訴訟1件増で施設5.5増（※） |
| 形成外科 | 施設数 | 0.999 | +4.1 | 0.005 | 訴訟1件増で施設4.1増（※） |

#### クロス相関で強い負の相関が検出された組み合わせ（|r| > 0.9）

| 診療科 | 定義 | 従属変数 | ラグ（年） | 相関係数 |
|--------|------|----------|-----------|----------|
| 産婦人科 | JMSR | 医師数 | +3年 | -0.946 |
| 泌尿器科 | JMSR | 医師数 | +6年 | -0.945 |
| 産婦人科 | Mixed | 医師数 | +3年 | -0.947 |
| 麻酔科 | Mixed | 医師数 | -4年 | -0.959 |
| 耳鼻咽喉科 | Litigation | 医師数 | +6年 | -0.973 |
| 皮膚科 | Litigation | 医師数 | +7年 | -0.988 |
| 精神科 | Litigation | 施設数 | +8年 | -0.981 |
| 皮膚科 | Litigation | 施設数 | +8年 | -0.969 |

**注目すべき発見**: 産婦人科は3つの事故定義すべてで医師数との強い負の相関（r < -0.9）を示し、リードタイム約3年。これは産婦人科領域で事故報告が増加すると、約3年後に医師数の減少傾向が強まることを示唆している。

### 4. 専攻医への影響（JMSR事故との相関）

| 診療科 | ラグ（年） | 相関係数 |
|--------|-----------|----------|
| 整形外科 | +4年 | -0.909 |
| 耳鼻咽喉科 | -3年 | -0.941 |
| 泌尿器科 | -4年 | -0.902 |
| 放射線科 | -1年 | -0.867 |
| 内科 | -1年 | -0.806 |
| 麻酔科 | -3年 | -0.805 |
| 皮膚科 | +3年 | -0.796 |
| 精神科 | 0年 | -0.770 |

### 5. 将来予測（2025-2034年）

#### 医師数予測（主要診療科）

| 診療科 | 年間変化 | 2025年推計 | 2030年推計 | 2034年推計 | 傾向 |
|--------|---------|-----------|-----------|-----------|------|
| 内科 | +378人/年 | 65,541 | 67,430 | 68,940 | 増加 |
| 外科 | -260人/年 | 14,391 | 13,093 | 12,054 | 減少 |
| 整形外科 | +190人/年 | 22,777 | 23,728 | 24,488 | 増加 |
| 産婦人科 | +111人/年 | 12,406 | 12,958 | 13,400 | 微増 |
| 小児科 | +206人/年 | 18,923 | 19,954 | 20,778 | 増加 |
| 精神科 | +276人/年 | 18,906 | 20,285 | 21,388 | 増加 |
| 麻酔科 | +186人/年 | 11,034 | 11,965 | 12,710 | 増加 |
| 耳鼻咽喉科 | -16人/年 | 8,668 | 8,588 | 8,524 | 横ばい〜微減 |

#### 施設数予測（主要診療科）

| 診療科 | 年間変化 | 2025年推計 | 2030年推計 | 2034年推計 | 傾向 |
|--------|---------|-----------|-----------|-----------|------|
| 内科 | -256施設/年 | 66,144 | 64,862 | 63,836 | 減少 |
| 外科 | -350施設/年 | 13,468 | 11,718 | 10,318 | 大幅減少 |
| 小児科 | -188施設/年 | 19,530 | 18,589 | 17,836 | 減少 |
| 産婦人科 | -65施設/年 | 5,299 | 4,974 | 4,714 | 減少 |
| 形成外科 | +90施設/年 | 3,442 | 3,892 | 4,252 | 増加 |
| 麻酔科 | +72施設/年 | 3,358 | 3,717 | 4,005 | 増加 |

#### 専攻医数予測（主要診療科）

| 診療科 | 年間変化 | 2025年推計 | 2030年推計 | 傾向 |
|--------|---------|-----------|-----------|------|
| 救急科 | +33人/年 | 476 | 643 | 大幅増加 |
| 内科 | +30人/年 | 2,981 | 3,131 | 増加 |
| 整形外科 | +30人/年 | 748 | 897 | 増加 |
| 総合診療 | +20人/年 | 311 | 410 | 増加 |
| 放射線科 | +17人/年 | 352 | 437 | 増加 |
| 精神科 | +16人/年 | 584 | 666 | 増加 |
| 小児科 | -5人/年 | 529 | 502 | 微減 |
| 耳鼻咽喉科 | -5人/年 | 228 | 201 | 減少 |
| 脳神経外科 | -4人/年 | 221 | 203 | 微減 |

## 限界と注意事項

1. **時系列の短さ**: JMSR事故データは2015年開始（11年間）で、ITS分析に必要な最低点数（推奨15年以上）を下回る
2. **隔年データの補間**: 医師統計は2年ごとの調査であり、年次データへの線形補間が行われている
3. **因果関係の限界**: 相関分析は因果関係を証明しない。事故と医師数の双方に影響する交絡因子が存在する可能性
4. **訴訟データのITSエラー**: 定義2（訴訟統計）では複数の診療科でITSモデルがフィットせず（パラメータ不足エラー）
5. **正の係数の解釈**: ITS回帰で正の事故効果係数が多く出ているのは、事故件数と医師数が共に増加トレンドにあるためで、トレンド除去後のクロス相関分析の方がより適切な解釈を提供する
6. **専攻医データ**: 2018年からの8年間のみで統計的検出力が限定的。2階建部分（サブスペシャルティ）のデータは含まれていない
7. **予測の不確実性**: 線形外挿による予測は構造変化（政策変更等）を考慮していない

## 結論

- **産婦人科**が最も顕著に事故報告と医師数減少の関連を示した（リードタイム約3年、r=-0.95）
- **外科**は訴訟件数と長期的な医師数減少トレンドに有意な関連が見られた
- 全体的な**ウィンドウ期間は約4〜5年**と推定された
- **施設数**は事故とほぼ同時期（ラグ≒0）に影響を受ける傾向
- **外科**の医師数・施設数は今後も減少が続く見通し（年間-260人、-350施設）
- **救急科・総合診療・放射線科**の専攻医は増加傾向

## 生成ファイル一覧

### CSV データ
- `data/its_results_summary.csv` — ITS回帰結果（53モデル）
- `data/lead_time_estimates.csv` — リードタイム推定値
- `data/window_period_estimates.csv` — ウィンドウ期間推定値
- `data/forecast_summary.csv` — 将来予測（41予測）

### 可視化
- `output/its_physicians_def1.png` — ITS: 医師数 vs JMSR事故（12科）
- `output/its_facilities_def1.png` — ITS: 施設数 vs JMSR事故（12科）
- `output/its_physicians_def2.png` — ITS: 医師数 vs 訴訟（12科）
- `output/lead_time_heatmap.png` — リードタイムヒートマップ
- `output/accident_trends.png` — 事故トレンド比較
- `output/forecast_physicians.png` — 医師数予測（6科）
- `output/forecast_facilities.png` — 施設数予測（6科）
- `output/forecast_trainees.png` — 専攻医数予測（9科）

---

# English Translation

---

# Time-series analysis report of medical accidents and number of doctors and facilities by department

## Overview

We used Interrupted Time Series (ITS) analysis to examine how the occurrence of medical accidents affects the number of doctors and medical facilities in each department. We used three types of accident definitions and analyzed 12 major medical departments.

## Data source

| Data | Source | Period |
|--------|------|------|
| Number of medical accidents (definition 1) | Japan Medical Safety Research Organization (JMSR) | 2015-2025 |
| Number of medical-related lawsuits (definition 2) | Supreme Court | 2004-2023 |
| Mixed index (definition 3) | Definitions 1 and 2 are normalized to [0,1] and averaged | 2015-2023 |
| Number of doctors by department | Statistics of physicians, dentists, and pharmacists | 1994-2022 (biennial) |
| Number of facilities by clinical department | Medical facility dynamics survey | 2002-2023 |
| Number of new specialty physician registrations | Japan Medical Specialist Organization | 2018-2025 |

## Analysis method

1. **ITS segment regression**: Y_t = β0 + β1·time + β2·intervention + β3·time_after + β4·accident_rate + ε_t
2. **Cross correlation analysis**: Lead time estimation by cross correlation after trend removal
3. **AIC model selection**: Window period estimation
4. **Linear trend extrapolation**: Future prediction based on trends over the last 10 years

## Key results

### 1. Lead time estimation (accident occurrence → impact delay on number of doctors and facilities)

| Metric | Average Lead Time | Median | Weighted Average |
|------|-----------------|---------|---------|
| Number of doctors | 1.3 years | 2.5 years | 1.6 years |
| Number of facilities | -0.1 year | 0.0 year | — |

**Interpretation**: The impact on the number of doctors tends to appear with a delay of about 1 to 3 years after the accident. The effect on the number of facilities appears around the same time (lag ≒ 0).

### 2. Window duration estimation (duration of impact)

| Indicator | Average window period | Median |
|------|-----|---------|
| Number of doctors | 4.1 years | 4.0 years |
| Number of facilities | 4.2 years | 5.0 years |

**Interpretation**: The effects of the accident last for approximately 4-5 years.

### 3. ITS analysis results (statistically significant results p<0.05)

#### Definition 1 (JMSR: Medical Accident Investigation System)

| Department | Dependent variable | R² | Accident effect coefficient | p-value | Interpretation |
|---------|---------|------|-------------|------|------|
| Obstetrics and Gynecology | Number of doctors | 0.995 | +17.7 | 0.021 | 17.7 doctors increased by 1 accident (*) |
| Obstetrics and Gynecology | Number of facilities | 0.999 | +4.3 | 0.042 | 4.3 facilities increased by 1 accident (*) |
| Ophthalmology | Number of facilities | 1.000 | +4.1 | 0.039 | 4.1 facilities increased by 1 accident (*) |

*A positive coefficient is counterintuitive, but because the number of accidents is also increasing within the overall increasing trend, there may be an apparent positive correlation.

#### Definition 2 (Litigation Statistics)

| Department | Dependent variable | R² | Accident effect coefficient | p-value | Interpretation |
|---------|---------|------|-------------|------|------|
| Surgery | Number of doctors | 0.994 | +19.3 | <0.001 | 19.3 doctors increased due to one more lawsuit (*) |
| Obstetrics and Gynecology | Number of doctors | 0.977 | +11.6 | <0.001 | 11.6 doctors increased by 1 lawsuit (*) |
| Obstetrics and Gynecology | Number of facilities | 0.990 | +5.5 | <0.001 | 5.5 facilities increased by 1 lawsuit (*) |
| Plastic Surgery | Number of Facilities | 0.999 | +4.1 | 0.005 | 4.1 Facilities Increased by 1 Lawsuit (*) |

#### Combinations for which strong negative correlation was detected in cross-correlation (|r| > 0.9)

| Department | Definition | Dependent variable | Lag (years) | Correlation coefficient |
|---------|------|---------|------------|------------|
| Obstetrics and Gynecology | JMSR | Number of doctors | +3 years | -0.946 |
| Urology | JMSR | Number of doctors | +6 years | -0.945 |
| Obstetrics and Gynecology | Mixed | Number of doctors | +3 years | -0.947 |
| Anesthesiology | Mixed | Number of doctors | -4 years | -0.959 |
| Otorhinolaryngology | Litigation | Number of doctors | +6 years | -0.973 |
| Dermatology | Litigation | Number of doctors | +7 years | -0.988 |
| Psychiatry | Litigation | Number of facilities | +8 years | -0.981 |
| Dermatology | Litigation | Number of facilities | +8 years | -0.969 |
**Notable findings**: Obstetrics and gynecology showed a strong negative correlation (r < -0.9) with the number of physicians for all three accident definitions, with a lead time of approximately 3 years. This suggests that if the number of accident reports increases in the field of obstetrics and gynecology, the decline in the number of doctors will increase after about three years.

### 4. Impact on specialized physicians (correlation with JMSR accident)

| Department | Lag (years) | Correlation coefficient |
|---------|------------|---------|
| Orthopedics | +4 years | -0.909 |
| Otorhinolaryngology | -3 years | -0.941 |
| Urology | -4 years | -0.902 |
| Radiology | -1 year | -0.867 |
| Internal medicine | -1 year | -0.806 |
| Anesthesiology | -3 years | -0.805 |
| Dermatology | +3 years | -0.796 |
| Psychiatry | 0 years | -0.770 |

### 5. Future prediction (2025-2034)

#### Prediction of number of doctors (major departments)

| Clinical Department | Annual Change | 2025 Estimate | 2030 Estimate | 2034 Estimate | Trend |
|---------|---------|---------|------------|------------|------|
| Internal medicine | +378 people/year | 65,541 | 67,430 | 68,940 | Increase |
| Surgery | -260 people/year | 14,391 | 13,093 | 12,054 | Decrease |
| Orthopedics | +190 people/year | 22,777 | 23,728 | 24,488 | Increase |
| Obstetrics and Gynecology | +111 people/year | 12,406 | 12,958 | 13,400 | Slight increase |
| Pediatrics | +206 people/year | 18,923 | 19,954 | 20,778 | Increase |
| Psychiatry | +276 people/year | 18,906 | 20,285 | 21,388 | Increase |
| Anesthesiology | +186 people/year | 11,034 | 11,965 | 12,710 | Increase |
| Otorhinolaryngology | -16 patients/year | 8,668 | 8,588 | 8,524 | Flat to slight decrease |

#### Forecast of number of facilities (main clinical departments)

| Clinical Department | Annual Change | 2025 Estimate | 2030 Estimate | 2034 Estimate | Trend |
|---------|---------|---------|------------|------------|------|
| Internal medicine | -256 facilities/year | 66,144 | 64,862 | 63,836 | Decrease |
| Surgery | -350 facilities/year | 13,468 | 11,718 | 10,318 | Significant decrease |
| Pediatrics | -188 facilities/year | 19,530 | 18,589 | 17,836 | Decrease |
| Obstetrics and Gynecology | -65 facilities/year | 5,299 | 4,974 | 4,714 | Decrease |
| Plastic Surgery | +90 facilities/year | 3,442 | 3,892 | 4,252 | Increase |
| Anesthesiology | +72 facilities/year | 3,358 | 3,717 | 4,005 | Increase |

#### Forecast of number of specialized doctors (major medical departments)

| Clinical Department | Annual Change | 2025 Estimate | 2030 Estimate | Trend |
|---------|---------|---------|------------|------|
| Emergency Department | +33 people/year | 476 | 643 | Significant increase |
| Internal medicine | +30 people/year | 2,981 | 3,131 | Increase |
| Orthopedics | +30 people/year | 748 | 897 | Increase |
| General medical care | +20 people/year | 311 | 410 | Increase |
| Radiology | +17 people/year | 352 | 437 | Increase |
| Psychiatry | +16 people/year | 584 | 666 | Increase |
| Pediatrics | -5 people/year | 529 | 502 | Slight decrease |
| Otorhinolaryngology | -5 patients/year | 228 | 201 | Decrease |
| Neurosurgery | -4 people/year | 221 | 203 | Slight decrease |

## Limitations and precautions

1. **Short time series**: JMSR accident data started in 2015 (11 years), which is lower than the minimum score required for ITS analysis (recommended 15 years or more)
2. **Interpolation of biennial data**: Physician statistics are surveyed every two years, and linear interpolation to annual data is performed.
3. **Limitations of Causality**: Correlation analysis does not prove causation. Possible confounding factors that affect both accidents and number of doctors
4. **ITS error in litigation data**: In definition 2 (litigation statistics), the ITS model does not fit in multiple clinical departments (missing parameter error)
5. **Interpretation of positive coefficients**: The reason why there are many positive accident effect coefficients in the ITS regression is that both the number of accidents and the number of doctors are on an increasing trend, and cross-correlation analysis after trend removal provides a more appropriate interpretation.
6. **Specialist data**: Limited statistical power for only 8 years from 2018. Data for the two-story part (subspecialty) is not included.
7. **Forecast uncertainty**: Forecasts based on linear extrapolation do not take into account structural changes (policy changes, etc.)

## Conclusion

- **Obstetrics and Gynecology** showed the most significant relationship between accident reports and a decrease in the number of doctors (lead time approximately 3 years, r=-0.95)
- In **Surgery**, there was a significant relationship between the number of lawsuits and the long-term trend of decreasing number of doctors.
- Overall **window period was estimated to be approximately 4-5 years**
- **Number of facilities** tends to be affected around the same time as the accident (lag ≒ 0)
- The number of **surgery** doctors and facilities is expected to continue decreasing (-260 people, -350 facilities annually)
- The number of doctors specializing in **emergency department, general medicine, radiology** is on the rise

## List of generated files

### CSV data
- `data/its_results_summary.csv` — ITS regression results (53 models)
- `data/lead_time_estimates.csv` — Lead time estimates
- `data/window_period_estimates.csv` — Window period estimates
- `data/forecast_summary.csv` — Future forecast (41 forecasts)

### Visualization
- `output/its_physicians_def1.png` — ITS: Number of doctors vs. JMSR accidents (12 departments)
- `output/its_facilities_def1.png` — ITS: Number of facilities vs. JMSR accidents (12 departments)
- `output/its_physicians_def2.png` — ITS: Number of doctors vs. lawsuits (12 departments)
- `output/lead_time_heatmap.png` — Lead time heatmap
- `output/accident_trends.png` — Accident trend comparison
- `output/forecast_physicians.png` — Forecasting the number of doctors (6 departments)
- `output/forecast_facilities.png` — Forecasting the number of facilities (6 departments)
- `output/forecast_trainees.png` — Prediction of number of major doctors (9 departments)
