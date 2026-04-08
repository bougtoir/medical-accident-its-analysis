# Linの一致相関係数：心拍出量モニターバリデーションにおける欠落指標

## Commentary

**投稿先候補**: Journal of Clinical Monitoring and Computing

---

**著者**: [著者名]

**所属**: [所属機関]

**責任著者**: [責任著者]

**語数**: 約2,400語（Commentary）

**キーワード**: 一致相関係数, 心拍出量, 方法比較, Bland-Altman, 血行動態モニタリング, バリデーション

---

## 抄録

心拍出量（CO）モニタリングデバイスのバリデーションは、Bland-Altman解析、パーセント誤差（PE）、およびポーラープロット評価からなる標準的な枠組みへと発展してきた。この3指標は、バイアス、一致限界、およびトレンド追従性を効果的に評価する一方で、絶対測定値の正確度と精度を同時に定量化する統合指標を提供しない。Linの一致相関係数（CCC）は、全体的な一致度を精度（Pearsonのr）と正確度（バイアス補正係数 C_b）に分解できることから、このギャップに対処しうる。他の生物医学的方法比較研究において確立された役割を有するにもかかわらず、CCCはCOモニターの標準バリデーション枠組みに組み込まれていない。本コメンタリーでは、CCCおよびその関連する一致性プロットが、現行の標準的分析手法では把握できない情報を提供する補完的指標として、COモニターバリデーション研究に採用されるべきであると論じる。

---

## 緒言

過去四半世紀にわたり、心拍出量（CO）モニタリングデバイスのバリデーションに関するコンセンサス枠組みが形成されてきた。その骨格をなすのは、バイアスおよび一致限界を評価するBland-Altmanプロット [1,2]、母集団間で正規化された比較を可能にするCritchley-Critchleyのパーセント誤差（PE）基準 [3]、そしてトレンド追従性を評価するポーラープロット [4,5] の3つの分析ツールである。方法論的ガイダンスは、Cecconi ら [6]、Saugel ら [7]、および Odor ら [8] によってさらに洗練され、方法比較研究のための段階的アプローチとチェックリストが確立されている。

この枠組みは当分野に十分貢献してきた。しかし、批判的に検討すると重要なギャップが浮かび上がる。これらのツールのいずれも、45度完全一致線に対するCO絶対測定値の正確度（真値への近さ）と精度（再現性）を同時に捉える統合的な単一値指標を提供しない。Bland-Altmanプロットは差のバイアスとばらつきを評価するが、一致線との直接的な一致度は定量化しない。PEは一致限界を正規化するが、同じ限界を継承する。ポーラープロットは変化の方向と大きさのみを評価し、絶対値は評価しない。

Linの一致相関係数（CCC）は1989年に導入され [9]、まさに方法比較研究におけるこの役割を果たすために設計された。検査医学、画像診断、肺機能検査など他の生物医学分野で広く採用されているにもかかわらず、CCCはCOモニタリングのバリデーション文献に系統的に組み込まれていない。本コメンタリーでは、CCCをCOモニターの標準バリデーションツールキットに追加すべきことを提案し、既存手法を超える診断的情報について説明する。

## 現行の枠組みとその限界

### Bland-Altman解析

Bland-Altmanプロットは、COモニターバリデーションの礎石であり続けている [1,2]。2つの手法の差をその平均に対してプロットすることにより、バイアス（平均差）と精度（一致限界、LoA = バイアス ± 1.96 SD）の視覚的評価を提供する。しかし、Odor ら [8] が認めたように、Bland-Altmanプロットには固有の限界がある。散布図上にデータが広く分散していても一貫したバイアスがないように見えるだけであり、「隠れたまたは一貫性のないバイアス（hidden or inconsistent bias）」を排除することはできない。さらに、LoAは純粋に統計的な境界であり、95%の差がこの範囲に収まることを記述するものであって、新しいデバイスの読み値が個々の測定レベルでリファレンスと互換性があるかどうかを直接示すものではない。

特に重要な限界は、デバイスが比例バイアス（proportional bias）を示す場合に生じる。すなわち、不一致の大きさがCOのレベルに応じて系統的に変動する場合である。このような場合、単一のLoAセットは誤解を招く可能性がある。回帰ベースのアプローチはこの問題に対処できるが [2]、複雑性が増し、適用に一貫性がない。

### パーセント誤差

Critchley-Critchley基準のPE ≤ ±30% [3] は、肺動脈カテーテル（PAC）熱希釈法リファレンスの既知の精度（±20%）から導かれた客観的な許容閾値を提供する。これは、研究間および母集団間の標準化された比較を可能にした画期的な貢献であった。しかし、PEはLoAを平均COで割って算出されるため、Bland-Altman解析の限界を継承する。さらに、30%閾値は特定のリファレンス手法精度を前提としており、リファレンス手法が異なる場合（例：経食道心エコー、経肺熱希釈法）には理論的に再計算すべきだが [6]、実際にはこの調整が行われることはまれである。

### ポーラープロット

Critchley ら [4] が導入したポーラープロットは、COのペア変化量間の一致を放射軸からの角度偏差として表現することにより、トレンド追従性を評価する。角度バイアス、放射方向の一致限界、および極座標一致率が、デバイスが動的変化をどの程度追従するかを記述する。これは目標指向型治療において絶対精度よりもトレンド追従性がより臨床的に重要となりうるため、臨床的に重要である。しかし、ポーラープロットは変化の方向一致のみを明示的に評価し、絶対値の一致に関する情報は提供しない。

### ギャップ

まとめると、現行の3指標は以下を評価する：
- **バイアスとばらつき**（Bland-Altman）— ただし一致線との統合的一致度は評価しない
- **正規化された一致度**（PE）— ただしBland-Altmanの限界を継承する
- **トレンド追従性**（ポーラープロット）— ただし変化のみで、絶対値は評価しない

欠落しているのは、以下の問いに直接答える指標である：*「2つの手法からの対応する測定値は、45度完全一致線上にどの程度近く分布しているか？」* これはまさにLinのCCCが定量化するものである。

## Linの一致相関係数

### 定義と分解

LinのCCC（ρ_c）は、観測値のペアが45度完全一致線上にどの程度位置するかを評価する [9,10]。定義は以下の通りである：

    ρ_c = (2 × σ₁₂) / (σ₁² + σ₂² + (μ₁ - μ₂)²)

ここで σ₁₂ は共分散、σ₁² および σ₂² は分散、μ₁ および μ₂ は2つの測定値の平均である。

決定的に重要なのは、CCCが2つの解釈可能な成分に分解できることである：

    ρ_c = r × C_b

ここで：
- **r**（Pearsonの相関係数）は**精度（precision）**を測定する — データが最良適合線の周囲にどれだけ緊密に分布しているか
- **C_b**（バイアス補正係数）は**正確度（accuracy）**を測定する — 最良適合線が45度一致線からどれだけ乖離しているか

この分解は診断的に強力である。高いrだが低いC_bを持つデバイスは、精度は高いが正確度が低い（一貫したスケールまたはオフセットエラー — 再較正により補正可能な可能性がある）。低いrだが高いC_bを持つデバイスは、平均的な正確度は良好だが精度が低い（固有の測定ノイズ — 較正では補正不可能）。この区別はデバイス開発および臨床的意思決定に直接的な含意を持つが、Bland-Altmanプロットやパーセント誤差からは抽出できない。

### 一致性プロット（Concordance Plot）

一致性プロット — 手法1 vs 手法2の散布図に45度一致線を重ねたもの — は、全体的な一致度の即座の視覚的評価を提供する。差を平均に対してプロットすることにより実際の測定スケールを不明瞭にするBland-Altmanプロットとは異なり、一致性プロットは臨床的測定スケール（COではL/min）を両軸に保持する。これにより以下の直接的な視覚的同定が可能になる：

1. **スケールエラー**（傾き ≠ 1）：最良適合線が一致線から乖離する
2. **オフセットエラー**（切片 ≠ 0）：低値または高値域で系統的なずれが見える
3. **範囲依存的な不一致**：不均一分散を示す扇状パターン
4. **外れ値**：一致線から遠い個別測定値

## 数値的例示

2つの仮想的な非侵襲COモニターを考える。いずれもPAC熱希釈法に対して120組のペア測定（真のCO範囲：2.0–9.0 L/min、平均約5.0 L/min）で比較された（Figure 1）：

**デバイスA**（比例バイアス、高精度）：
- Bland-Altman：バイアス = +0.15 L/min、LoA = [-1.44, +1.75] L/min、PE = 30.5%
- 関係式：CO_A = 1.21 × CO_ref - 0.92（傾き > 1、補償的オフセット）
- CCC = 0.867（r = 0.907、C_b = 0.956）

**デバイスB**（系統的バイアスなし、低精度）：
- Bland-Altman：バイアス = +0.12 L/min、LoA = [-1.70, +1.93] L/min、PE = 34.9%
- 関係式：CO_B = 0.83 × CO_ref + 1.00 + ランダムノイズ（SD = 1.10）
- CCC = 0.778（r = 0.782、C_b = 0.995）

Bland-Altman解析のみでは、デバイスAとBは概ね類似して見える：同程度のバイアス（約0.1 L/min）、重複するLoA範囲、そしていずれもCritchley-Critchley閾値付近の30–35%範囲のPE値。従来型の評価では、両デバイスとも境界的に許容可能な一致度を有すると結論づけうる。しかし、CCC分解は根本的に異なるエラープロファイルを明らかにする（Figure 2）：

- **デバイスA**：高精度（r = 0.907）だが正確度が低下（C_b = 0.956） — 系統的なスケールエラー（傾き = 1.21）であり、ゲインファクターのアルゴリズム再較正により補正可能な可能性がある
- **デバイスB**：高正確度（C_b = 0.995）だが低精度（r = 0.782） — 固有の測定変動性であり、較正では補正不可能

この区別は臨床的にもデバイス開発においても重要である。デバイスAでは、アルゴリズムのゲインファクターを調整するファームウェアアップデートにより一致度が大幅に改善され、PEを30%以下に引き下げられる可能性がある。デバイスBでは、エラーが系統的ではなく確率的であるため、根本的なハードウェアまたは信号処理の改善が必要となる。Bland-Altman解析のみではこれらのシナリオを区別できないが、CCC分解は各デバイスの限界の性質と適切な是正戦略を即座に同定する。

## なぜ今なのか？ Odor et al.から8年後

2017年のOdor ら [8] の出版以降のいくつかの進展が、CCCの導入を裏付ける：

1. **非侵襲デバイスの増加**：非侵襲COモニターの市場は大幅に拡大し、フィンガーカフ（ClearSight/VitaWave）、バイオインピーダンス/バイオリアクタンス（NICOM/Starling）、電気式心拍計測（ICON）、およびパルス分解解析（VitalStream）デバイスがすべて規制当局の承認を取得している [11-13]。測定原理の多様性により、標準化された包括的バリデーションはかつてないほど重要になっている。

2. **規制上の含意**：これらのデバイスに対するFDA 510(k)経路は実質的同等性の実証を要求するが、バリデーションのための具体的な統計手法は規定されていない [14]。公表されたバリデーション研究は圧倒的にBA解析とPEに依存し、トレンド評価にはポーラープロットを用いている。CCCを含めるコンセンサス推奨は、研究デザインと規制上の期待の両方に影響を与えうる。

3. **方法論的不一致の持続**：最近のメタアナリシスおよびシステマティックレビューは、バリデーション結果の報告方法が研究間で一貫していないことを引き続き指摘している [15]。確立されたベンチマーク（例：不良 < 0.90、中程度 0.90–0.95、良好 0.95–0.99、優秀 > 0.99、McBride [16] より改変）を持つ標準化された指標としてCCCを追加することは、研究間比較を促進するだろう。

4. **計算上のアクセス性**：CCCは広く利用可能な統計ソフトウェア（Rパッケージ `epiR`、Python `pingouin`、Stata `concord`）を用いて生のペアデータから容易に計算できる。Bland-Altman解析に既に必要とされるもの以上の追加データ収集は不要である。

## 提案する拡張バリデーション枠組み

COモニターの標準バリデーション枠組みを3指標から4指標に拡張することを提案する：

| 指標 | 評価対象 | 臨床的問い |
|------|---------|-----------|
| **Bland-Altmanプロット** | バイアス、LoA | 系統誤差と差のばらつきはどの程度か？ |
| **パーセント誤差** | 正規化されたLoA | リファレンスに対して一致度は臨床的に許容可能か？ |
| **ポーラープロット** | トレンド追従性 | デバイスは変化を正しい方向に追従するか？ |
| **CCC + 一致性プロット** | 統合された正確度×精度 | 測定値は完全一致線上にどの程度近く分布し、エラーはバイアスによるものかノイズによるものか？ |

CCCはその分解（rおよびC_b）とともに報告されるべきである。個々の成分が実行可能な診断情報を提供するためである。一致性プロットは、45度一致線、最良適合回帰線、およびCCC値を注釈した形で提示されるべきである。

CCCは既存手法の代替としてではなく、特定の分析的ギャップを埋める補完として提案されることを強調する。提案する4指標の各々は異なる臨床的問いに答え、総合してデバイス性能の包括的な特性評価を提供する。

## 結論

COモニターバリデーションの現行標準枠組み — Bland-Altman解析、パーセント誤差、ポーラープロット — は20年以上にわたり当分野に貢献してきた。しかし、正確度と精度を同時に捉える絶対的測定一致度の統合指標が欠落している。Linの一致相関係数は、精度と正確度の成分への解釈可能な分解を伴い、このギャップを埋める。非侵襲COモニタリング技術の増加と標準化されたバリデーション方法論の重要性の高まりを考慮し、CCCおよび一致性プロットがCOモニターバリデーション研究の定常的な構成要素として採用されることを推奨する。

---

## 引用文献

1. Bland JM, Altman DG. Statistical methods for assessing agreement between two methods of clinical measurement. Lancet. 1986;327(8476):307-310. doi:10.1016/S0140-6736(86)90837-8

2. Bland JM, Altman DG. Measuring agreement in method comparison studies. Stat Methods Med Res. 1999;8(2):135-160. doi:10.1177/096228029900800204

3. Critchley LAH, Critchley JAJH. A meta-analysis of studies using bias and precision statistics to compare cardiac output measurement techniques. J Clin Monit Comput. 1999;15(2):85-91. doi:10.1023/A:1009982611386

4. Critchley LA, Lee A, Ho AM-H. A critical review of the ability of continuous cardiac output monitors to measure trends in cardiac output. Anesth Analg. 2010;111(5):1180-1192. doi:10.1213/ANE.0b013e3181f08a5b

5. Critchley LA, Yang XX, Lee A. Assessment of trending ability of cardiac output monitors by polar plot methodology. J Cardiothorac Vasc Anesth. 2011;25(3):536-546. doi:10.1053/j.jvca.2011.01.003

6. Cecconi M, Rhodes A, Poloniecki J, Della Rocca G, Grounds RM. Bench-to-bedside review: the importance of the precision of the reference technique in method comparison studies---with specific reference to the measurement of cardiac output. Crit Care. 2009;13(1):201. doi:10.1186/cc7129

7. Saugel B, Grothe O, Wagner JY. Tracking changes in cardiac output: statistical considerations on the 4-quadrant plot and the polar plot methodology. Anesth Analg. 2015;121(2):514-524. doi:10.1213/ANE.0000000000000725

8. Odor PM, Bampoe S, Cecconi M. Cardiac output monitoring: validation studies---how results should be presented. Curr Anesthesiol Rep. 2017;7(4):410-415. doi:10.1007/s40140-017-0239-0

9. Lin LI. A concordance correlation coefficient to evaluate reproducibility. Biometrics. 1989;45(1):255-268. doi:10.2307/2532051

10. Lin LI. A note on the concordance correlation coefficient. Biometrics. 2000;56(1):324-325. doi:10.1111/j.0006-341X.2000.00324.x

11. Ameloot K, Palmers PJ, Malbrain MLNG. The accuracy of noninvasive cardiac output and pressure measurements with finger cuff: a concise review. Curr Opin Crit Care. 2015;21(3):232-239. doi:10.1097/MCC.0000000000000198

12. Squara P, Denjean D, Estagnasie P, Brusset A, Dib JC, Dubois C. Noninvasive cardiac output monitoring (NICOM): a clinical validation. Intensive Care Med. 2007;33(7):1191-1194. doi:10.1007/s00134-007-0640-0

13. Song W, Guo J, Cao D, et al. Comparison of noninvasive electrical cardiometry and transpulmonary thermodilution for cardiac output measurement in critically ill patients: a prospective observational study. BMC Anesthesiol. 2025;25:123. doi:10.1186/s12871-025-03005-1

14. U.S. Food and Drug Administration. Premarket Notification 510(k). https://www.fda.gov/medical-devices/premarket-submissions-selecting-and-preparing-correct-submission/premarket-notification-510k. Accessed March 2026.

15. Joosten A, Desebbe O, Suehiro K, et al. Accuracy and precision of non-invasive cardiac output monitoring devices in perioperative medicine: a systematic review and meta-analysis. Br J Anaesth. 2017;118(3):298-310. doi:10.1093/bja/aew461

16. McBride GB. A proposal for strength-of-agreement criteria for Lin's concordance correlation coefficient. NIWA Client Report HAM2005-062. 2005.

---

## 補足：ソフトウェア実装

CCCは一般的な統計環境で計算可能である：

**R**:
```r
library(epiR)
result <- epi.ccc(method1, method2, ci = "z-transform", conf.level = 0.95)
# 返値: rho.c (CCC), s.shift (scale shift), l.shift (location shift),
#       C.b (bias correction factor), r (Pearson r)
```

**Python**:
```python
import numpy as np

def concordance_cc(y1, y2):
    """LinのCCCと分解成分を計算"""
    mean1, mean2 = np.mean(y1), np.mean(y2)
    var1, var2 = np.var(y1, ddof=1), np.var(y2, ddof=1)
    sd1, sd2 = np.std(y1, ddof=1), np.std(y2, ddof=1)
    cor = np.corrcoef(y1, y2)[0, 1]  # Pearson r（精度）
    # バイアス補正係数（正確度）
    c_b = (2 * sd1 * sd2) / (var1 + var2 + (mean1 - mean2)**2)
    # CCC = r × C_b
    ccc = cor * c_b
    return {'ccc': ccc, 'pearson_r': cor, 'C_b': c_b}
```

**Stata**:
```stata
concord method1 method2, summary
```

---

*利益相反*: [記載予定]

*資金*: [記載予定]

---

# English Translation

---

# Lin's concordance correlation coefficient: missing indicator in cardiac output monitor validation

## Commentary

**Submission candidate**: Journal of Clinical Monitoring and Computing

---

**Author**: [Author name]

**Affiliation**: [Affiliated institution]

**Corresponding author**: [Corresponding author]

**Number of words**: Approximately 2,400 words (Commentary)

**Keywords**: concordance correlation coefficient, cardiac output, method comparison, Bland-Altman, hemodynamic monitoring, validation

---

## Abstract
Validation of cardiac output (CO) monitoring devices has evolved into a standard framework consisting of Bland-Altman analysis, percent error (PE), and polar plot evaluation. While these three metrics effectively assess bias, limits of agreement, and trend following, they do not provide an integrated metric that simultaneously quantifies the accuracy and precision of absolute measurements. Lin's concordance correlation coefficient (CCC) can address this gap because it can decompose the overall degree of concordance into precision (Pearson's r) and accuracy (bias correction coefficient C_b). Despite having an established role in comparative studies of other biomedical methods, CCC has not been incorporated into standard validation frameworks for CO monitors. This Commentary argues that CCC and its associated consistency plot should be employed in CO monitor validation studies as a complementary metric that provides information not captured by current standard analytical methods.

---

## Introduction
Over the past quarter century, a consensus framework for the validation of cardiac output (CO) monitoring devices has developed. At its core are three analytical tools: Bland-Altman plots [1,2] to assess bias and limits of agreement; the Critchley-Critchley percent error (PE) criterion [3] to enable normalized comparisons across populations; and polar plots [4,5] to assess trend following. Methodological guidance was further refined by Cecconi et al. [6], Saugel et al. [7], and Odor et al. [8], establishing a step-by-step approach and checklist for method comparison studies.

This framework has contributed well to the field. However, upon critical examination, important gaps emerge. None of these tools provide a unified, single-value metric that simultaneously captures the accuracy (closeness to the true value) and precision (reproducibility) of absolute CO measurements relative to the 45-degree perfect match line. The Bland-Altman plot assesses the bias and dispersion of the difference, but does not quantify direct agreement with the line of agreement. PE normalizes the match limits, but inherits the same limits. Polar plots evaluate only the direction and magnitude of change, not the absolute value.
Lin's concordance correlation coefficient (CCC) was introduced in 1989 [9] and was designed to serve exactly this role in method comparison studies. Despite being widely adopted in other biomedical fields such as laboratory medicine, diagnostic imaging, and pulmonary function testing, CCC has not been systematically incorporated into the validation literature for CO monitoring. This commentary proposes that CCC be added to the standard validation toolkit for CO monitors and describes the diagnostic information it provides over existing methods.

## Current framework and its limitations

### Bland-Altman analysis
Bland-Altman plots continue to be a cornerstone of CO monitor validation [1,2]. Plotting the difference between the two methods against their mean provides a visual assessment of bias (mean difference) and accuracy (limits of agreement, LoA = bias ± 1.96 SD). However, as acknowledged by Odor et al. [8], Bland-Altman plots have inherent limitations. Even if the data are widely distributed on a scatter plot, it only makes it appear that there is no consistent bias, and ``hidden or inconsistent bias'' cannot be ruled out. Additionally, the LoA is a purely statistical boundary that describes 95% of the differences within this range and does not directly indicate whether a new device's reading is compatible with the reference at the individual measurement level.

A particularly important limitation occurs when the device exhibits a proportional bias. That is, if the magnitude of the discrepancy varies systematically with the level of CO. In such cases, a single LoA set can be misleading. Regression-based approaches can address this issue [2], but they add complexity and are inconsistently applied.

### Percent error
The Critchley-Critchley criterion PE ≤ ±30% [3] provides an objective acceptance threshold derived from the known accuracy (±20%) of the pulmonary artery catheter (PAC) thermodilution reference. This was a groundbreaking contribution that enabled standardized comparisons between studies and populations. However, PE is calculated by dividing LoA by average CO, so it inherits the limitations of Bland-Altman analysis. Additionally, the 30% threshold assumes a specific reference method accuracy and should theoretically be recalculated if the reference method is different (e.g., transesophageal echocardiography, transpulmonary thermodilution) [6], but this adjustment is rarely made in practice.

### Polar plot

The polar plot introduced by Critchley et al. [4] evaluates trend followability by expressing the agreement between a pair of changes in CO as an angular deviation from the radial axis. Angular bias, radial matching limits, and polar matching rate describe how well the device tracks dynamic changes. This is clinically important because trend following can be more clinically important than absolute accuracy in goal-directed therapy. However, polar plots explicitly evaluate only the directional agreement of changes and do not provide information about the absolute value agreement.

### Gap

In summary, the three current indicators assess:
- **Bias and Variability** (Bland-Altman) — but does not evaluate the overall degree of agreement with the line of agreement
- **Normalized Degree of Agreement** (PE) — but inherits Bland-Altman limits
- **Trend followability** (polar plot) — However, only changes are evaluated, absolute values are not evaluated.

What is missing is a metric that directly answers the question: * "How closely do the corresponding measurements from the two techniques lie on the 45 degree line of perfect coincidence?" * This is exactly what Lin's CCC quantifies.

## Lin's coincidence correlation coefficient

### Definition and decomposition

Lin's CCC (ρ_c) evaluates the extent to which a pair of observations lies on the 45-degree perfect match line [9,10]. The definition is as follows:

    ρ_c = (2 × σ₁₂) / (σ₁² + σ₂² + (μ₁ - μ₂)²)

where σ₁₂ is the covariance, σ₁² and σ₂² are the variances, and μ₁ and μ₂ are the averages of the two measurements.

Crucially, CCC can be decomposed into two interpretable components:

    ρ_c = r × C_b

where:
- **r** (Pearson's correlation coefficient) measures **precision** — how tightly the data are distributed around the line of best fit.
- **C_b** (bias correction factor) measures **accuracy** — how far the best fit line deviates from the 45 degree match line.

This decomposition is diagnostically powerful. Devices with high r but low C_b have high precision but low accuracy (consistent scale or offset errors — which may be correctable by recalibration). Devices with low r but high C_b have good average accuracy but poor precision (inherent measurement noise—cannot be corrected with calibration). This distinction has direct implications for device development and clinical decision making, but cannot be extracted from Bland-Altman plots or percentage errors.

### Concordance Plot

The agreement plot—a scatter plot of Method 1 vs. Method 2 overlaid with a 45 degree agreement line—provides an immediate visual assessment of the overall degree of agreement. Unlike the Bland-Altman plot, which obscures the actual measurement scale by plotting the difference against the mean, the concordance plot preserves the clinical measurement scale (L/min for CO) on both axes. This allows direct visual identification of:

1. **Scale error** (slope ≠ 1): the best fit line deviates from the match line
2. **Offset error** (intercept ≠ 0): systematic deviations are visible in the low or high value range
3. **Range-dependent discrepancy**: fan pattern indicating heteroskedasticity
4. **Outlier**: Individual measurements far from the line of agreement

## Numerical example

Consider two hypothetical non-invasive CO monitors. Both were compared using 120 paired measurements (true CO range: 2.0–9.0 L/min, average ~5.0 L/min) for the PAC thermodilution method (Figure 1):

**Device A** (proportional bias, high precision):
- Bland-Altman: Bias = +0.15 L/min, LoA = [-1.44, +1.75] L/min, PE = 30.5%
- Relation: CO_A = 1.21 × CO_ref - 0.92 (slope > 1, compensatory offset)
- CCC = 0.867 (r = 0.907, C_b = 0.956)

**Device B** (no systematic bias, low precision):
- Bland-Altman: Bias = +0.12 L/min, LoA = [-1.70, +1.93] L/min, PE = 34.9%
- Relational equation: CO_B = 0.83 × CO_ref + 1.00 + random noise (SD = 1.10)
- CCC = 0.778 (r = 0.782, C_b = 0.995)
From Bland-Altman analysis alone, devices A and B appear broadly similar: similar bias (approximately 0.1 L/min), overlapping LoA ranges, and both PE values ​​in the 30–35% range near the Critchley-Critchley threshold. Conventional evaluation may conclude that both devices have a borderline acceptable degree of agreement. However, CCC decomposition reveals a fundamentally different error profile (Figure 2):

- **Device A**: High accuracy (r = 0.907) but reduced accuracy (C_b = 0.956) — Systematic scale error (slope = 1.21), potentially correctable by algorithmic recalibration of gain factor
- **Device B**: High accuracy (C_b = 0.995) but low precision (r = 0.782) — inherent measurement variability that cannot be corrected with calibration
This distinction is important both clinically and in device development. For Device A, a firmware update that adjusts the algorithm's gain factor significantly improves the match, potentially lowering the PE to below 30%. Device B requires fundamental hardware or signal processing improvements because the errors are stochastic rather than systematic. While Bland-Altman analysis alone cannot distinguish between these scenarios, CCC decomposition immediately identifies the nature of each device's limitations and appropriate remediation strategies.

## Why now? Eight years after Odor et al.

Several developments since the publication of Odor et al. [8] in 2017 support the introduction of CCC:

1. **Growth in non-invasive devices**: The market for non-invasive CO monitors has expanded significantly, with finger cuff (ClearSight/VitaWave), bioimpedance/bioreactance (NICOM/Starling), electrical heart rate measurement (ICON), and pulse-resolved analysis (VitalStream) devices all receiving regulatory approval [11-13]. The diversity of measurement principles makes standardized and comprehensive validation more important than ever.
2. **Regulatory Implications**: The FDA 510(k) pathway for these devices requires demonstration of substantial equivalence, but does not specify specific statistical methods for validation [14]. Published validation studies overwhelmingly rely on BA analysis and PE, and use polar plots to assess trends. Consensus recommendations to include CCCs can impact both study design and regulatory expectations.

3. **Persistent methodological inconsistencies**: Recent meta-analyses and systematic reviews continue to point out that the way validation results are reported is inconsistent across studies [15]. Adding CCC as a standardized measure with established benchmarks (e.g., poor < 0.90, moderate 0.90–0.95, good 0.95–0.99, excellent > 0.99, adapted from McBride [16]) would facilitate comparisons between studies.

4. **Computational accessibility**: CCC can be easily calculated from raw paired data using widely available statistical software (R package `epiR`, Python `pingouin`, Stata `concord`). No additional data collection is required beyond what is already required for Bland-Altman analysis.

## Proposed extended validation framework
We propose to expand the standard validation framework for CO monitors from 3 to 4 indicators:

| Indicator | Evaluation target | Clinical question |
|------|---------|---------|
| **Bland-Altman plot** | Bias, LoA | What is the variation in systematic errors and differences? |
| **Percentage Error** | Normalized LoA | Is the agreement clinically acceptable to the reference? |
| **Polar Plot** | Trend Followability | Does the device follow changes in the correct direction? |
| **CCC + Concordance Plot** | Integrated Accuracy x Precision | How closely are the measurements distributed on the perfect match line, and are the errors due to bias or noise? |

CCC should be reported along with its decomposition (r and C_b). This is because the individual components provide actionable diagnostic information. The concordance plot should be presented with the 45 degree match line, best fit regression line, and annotated CCC value.

We emphasize that CCC is not proposed as a replacement for existing methods, but as a complement to fill specific analytical gaps. Each of the four proposed metrics answers a different clinical question and together provide a comprehensive characterization of device performance.

## Conclusion
The current standard framework for CO monitor validation—Bland-Altman analysis, percent error, and polar plots—has served the field for more than 20 years. However, an integrated index of absolute measurement agreement that simultaneously captures accuracy and precision is missing. Lin's concordance correlation coefficient, with its interpretable decomposition into precision and accuracy components, fills this gap. Given the proliferation of non-invasive CO monitoring techniques and the growing importance of standardized validation methodologies, we recommend that CCC and concordance plots be adopted as routine components of CO monitor validation studies.

---

## References

1. Bland JM, Altman DG. Statistical methods for assessing agreement between two methods of clinical measurement. Lancet. 1986;327(8476):307-310. doi:10.1016/S0140-6736(86)90837-8
2. Bland JM, Altman DG. Measuring agreement in method comparison studies. Stat Methods Med Res. 1999;8(2):135-160. doi:10.1177/096228029900800204

3. Critchley LAH, Critchley JAJH. A meta-analysis of studies using bias and precision statistics to compare cardiac output measurement techniques. J Clin Monit Comput. 1999;15(2):85-91. doi:10.1023/A:1009982611386

4. Critchley LA, Lee A, Ho AM-H. A critical review of the ability of continuous cardiac output monitors to measure trends in cardiac output. Anesth Analg. 2010;111(5):1180-1192. doi:10.1213/ANE.0b013e3181f08a5b

5. Critchley LA, Yang XX, Lee A. Assessment of trending ability of cardiac output monitors by polar plot methodology. J Cardiothorac Vasc Anesth. 2011;25(3):536-546. doi:10.1053/j.jvca.2011.01.003

6. Cecconi M, Rhodes A, Poloniecki J, Della Rocca G, Grounds RM. Bench-to-bedside review: the importance of the precision of the reference technique in method comparison studies---with specific reference to the measurement of cardiac output. Crit Care. 2009;13(1):201. doi:10.1186/cc7129

7. Saugel B, Grothe O, Wagner JY. Tracking changes in cardiac output: statistical considerations on the 4-quadrant plot and the polar plot methodology. Anesth Analg. 2015;121(2):514-524. doi:10.1213/ANE.0000000000000725

8. Odor PM, Bampoe S, Cecconi M. Cardiac output monitoring: validation studies---how results should be presented. Curr Anesthesiol Rep. 2017;7(4):410-415. doi:10.1007/s40140-017-0239-0

9. Lin LI. A concordance correlation coefficient to evaluate reproducibility. Biometrics. 1989;45(1):255-268. doi:10.2307/2532051

10. Lin LI. A note on the concordance correlation coefficient. Biometrics. 2000;56(1):324-325. doi:10.1111/j.0006-341X.2000.00324.x

11. Ameloot K, Palmers PJ, Malbrain MLNG. The accuracy of noninvasive cardiac output and pressure measurements with finger cuff: a concise review. Curr Opin Crit Care. 2015;21(3):232-239. doi:10.1097/MCC.0000000000000198

12. Squara P, Denjean D, Estagnasie P, Brusset A, Dib JC, Dubois C. Noninvasive cardiac output monitoring (NICOM): a clinical validation. Intensive Care Med. 2007;33(7):1191-1194. doi:10.1007/s00134-007-0640-0

13. Song W, Guo J, Cao D, et al. Comparison of noninvasive electrical cardiometry and transpulmonary thermodilution for cardiac output measurement in critically ill patients: a prospective observational study. BMC Anesthesiol. 2025;25:123. doi:10.1186/s12871-025-03005-1

14. U.S. Food and Drug Administration. Premarket Notification 510(k). https://www.fda.gov/medical-devices/premarket-submissions-selecting-and-preparing-correct-submission/premarket-notification-510k. Accessed March 2026.

15. Joosten A, Desebbe O, Suehiro K, et al. Accuracy and precision of non-invasive cardiac output monitoring devices in perioperative medicine: a systematic review and meta-analysis. Br J Anaesth. 2017;118(3):298-310. doi:10.1093/bja/aew461

16. McBride GB. A proposal for strength-of-agreement criteria for Lin's concordance correlation coefficient. NIWA Client Report HAM2005-062. 2005.

---

## Supplement: Software implementation

CCC can be computed in common statistical environments:

**R**:
```r
library(epiR)
result <- epi.ccc(method1, method2, ci = "z-transform", conf.level = 0.95)
# Return value: rho.c (CCC), s.shift (scale shift), l.shift (location shift),
# C.b (bias correction factor), r (Pearson r)
````

**Python**:
```python
import numpy as np

def concordance_cc(y1, y2):
    """Calculate CCC and decomposition components of Lin"""
    mean1, mean2 = np.mean(y1), np.mean(y2)
    var1, var2 = np.var(y1, ddof=1), np.var(y2, ddof=1)
    sd1, sd2 = np.std(y1, ddof=1), np.std(y2, ddof=1)
    cor = np.corrcoef(y1, y2)[0, 1] # Pearson r (accuracy)
    # Bias correction factor (accuracy)
    c_b = (2 * sd1 * sd2) / (var1 + var2 + (mean1 - mean2)**2)
    # CCC = r × C_b
    ccc = cor * c_b
return {'ccc': ccc, 'pearson_r': cor, 'C_b': c_b}
````

**Stata**:
```stata
concord method1 method2, summary
````

---

*Conflict of interest*: [To be listed]

*Fund*: [Scheduled to be listed]
