# 査読者視点 批判的レビュー：Research Policy full-article manuscript

**対象原稿**: `docs/manuscript_full_article.docx`（生成日: 2026-08-09）  
**検証リビジョン**: `devin/1786331050-reviewer-audit` → `devin/researcher-mobility-ode-full-article`  
**レビュー観点**: ストーリー・フロー、伏線回収、データと主張の整合性、再現性、図表・文献の整合性

---

## 1. 実施した検証

- **公開リポ再現性**: `git clone --depth=1 https://github.com/bougtoir/researcher-mobility-ode` 後に `bash reproduce.sh` を実行。`results/`、図表、docx/pptx/md/zip が再生成され、原稿掲載数値と一致。
- **機械的整合性**: `docs/manuscript_full_article.md` 内の Figure/Table 初出を抽出。Figure 1–9、Table 1–12 ともに初出順に番号が増加し、orphan/phantom なし。
- **数値の動的生成**: `scripts/build_full_manuscript.py` が `results/endogenous/equilibrium_summary.csv`、`results/point_of_no_return.csv`、`results/annual/*.csv` 等を読み込み、本文・表・図を生成。ハードコードされた数値は確認されなかった。
- **年度移行率スクリプトの修正圧妥当性**: `annual_rates_projection_report.py` における I_total NaN 処理、右打ち切り (right censoring) 対応、初年度 compartment 配分の訓練期全期間集計、dashed/solid 描画分離、fig_dir 引数追加を確認。
- **Methods テキスト整合**: 修正後の docx/md で「dropout cap = 1.5 × 90th percentile」「inflow apportionment = training-period first-compartment distribution」と記述され、コードと一致。

---

## 2. 修正済みの再現性・整合性バグ

| # | 問題 | 修正内容 | 影響 |
|---|---|---|---|
| 1 | `annual_rates_projection_report.py` で zero-inflow 年を outer-merge 後 `dropna()` していたため、I_total 平均が過大評価されていた | `rate_table["I_total"] = rate_table["I_total"].fillna(0.0).astype(float)` を追加 | projected inflow が training 全期間の実測分布に基づくようになり、一部文明圏で低下・収束する傾向が正しく反映された |
| 2 | `build_annual_exits` で各著者の最終観測年も離脱 (exit) としてカウントしていた | `year != last_year` の条件を追加して右打ち切りを除外 | 2023 年などの d=1.0 異常値が消え、離脱率が現実的な水準になった |
| 3 | `project_population` で初年度 compartment 配分を 1 年目だけで計算していた | 訓練期 (2000-2016) 全体の first-compartment inflow を合計して share を計算 | 複数年度にわたる流入パターンが正しく反映され、プロジェクト期の compartment 配分が安定的になった |
| 4 | `plot_annual_rates` で observed・projected を区別せず一本の実線で描いていた | observed を `-`、projected を `--`、同一色で重ね描きし凡例を整理 | Figure 5 で 2016 年を境に実線と破線が切り替わる |
| 5 | `build_full_manuscript.py --output-dir` 使用時に annual 図が `docs/figures` に固定出力されていた | `plot_annual_rates/interciv_heatmap/projection_by_compartment` に `fig_dir` 引数を追加し、`build_annual_figures` から渡す | 任意 output dir で再現可能 |
| 6 | Methods の記述がコードと不一致（90th percentile・2016 distribution） | 「1.5 times the 90th percentile」「training-period first-compartment distribution」に修正 | コードと本文が一致 |

---

## 3. 優先度別指摘（改訂版評価）

### 3.1 最優先（投稿前に必須と思われるもの）

#### A. Markdown コンパニオンのセクション番号不連続
- **問題**: `manuscript_full_article.md` のセクション番号が `4.1-4.4` の次に `4.10-4.11`、`5.1-5.5` の次に `5.6-5.8`、`6.1-6.3` の次に `6.4-6.7` と飛んでいる。docx 側は `add_numbered_heading` によって連続的に生成されている。
- **影響**: 投稿物としては docx が正だが、GitHub/PDF 補助閲覧者や査読者が md を開いた場合、構成が混乱する。
- **修正案**: 提出用は docx のみとし、md は `README` 等で「supplementary / not submission formatted」と明記するか、`write_markdown` に連番ロジックを適用する。

#### B. 年次予測精度（RMSE 3.35 / MAPE 42.5%）の解釈強化
- **問題**: MAPE 42.5% は高く、早期警報系としての信頼性を疑問視される可能性がある。
- **現状**: 原稿は「small compartments and sparse transition counts」「conservative, non-standard measure computed against count_obs + 1」と説明している。
- **修正案**: Abstract または Discussion で「MAPE が高くても、警報系としては『閾値超過』フラグや T/M の方向性を追うものであり、精密な count 予測ではない」と一段階強調すると、査読者の懸念が和らぐ。

### 3.2 高優先（Major revision リスク）

#### C. RQ4「policy packages」の表現と実装のギャップ
- **問題**: Intro の RQ4 は「safety-factor-bound policy packages」としているが、Results/Discussion では single-lever counterfactual（d 減少、p_D 増加等）しか提示していない。
- **現状**: Discussion 6.1 で「二つのレバーを同時に変えると相乗効果があると考えられる」とは書かれている。
- **修正案**: RQ4 の文言を「safety-factor-bound single-lever and two-lever scenarios」に弱めるか、Table 7 に d-10% + p_D+10% のような 2 レバー組み合わせを追加する。

#### D. 因果表現の摘要レベルでの caveat
- **問題**: Abstract の「A simulated reduction in dropout yields the largest margin gain...」は、単独で読むと実際の政策効果を暗示しやすい。
- **現状**: Discussion 6.1・6.7・Conclusion で「mechanical perturbation」「not causal estimates」と明示。
- **修正案**: Abstract 最後に「in the fitted model」または「in these mechanical scenarios」を 1 語追加するか、そのままにして本文の caveat 参照を明確にする。

### 3.3 中優先（Minor revision / 補足説明）

#### E. Inter-civilisation flow の定義
- **問題**: `A`（abroad early-career）は特定文明圏への流出先ではなく「海外全体」の集計。年次遷移行列の `A → D`（帰国）は実際の帰国先を区別しない。
- **現状**: Methods 4.10 および Discussion 6.7 で proxy / lower-bound として説明。
- **修正案**: Figure 6 のキャプションを「Inter-civilisation abroad author-years」に留め、「Inter-civilisation flows」という強い表題を避けるか、本文で「proxy」であることを追加する。

#### F. 「Hindu」等の命名
- **問題**: グループ名 "Hindu" は宗教・文明圏を指すが、対象はインドを中心とする研究者。査読者がサンプリングバイアスや命名の妥当性を問う可能性がある。
- **現状**: Methods 3 で定義されている。
- **修正案**: Introduction のマッピング説明で「Hindu 文明圏 = インド・ネパール・スリランカ等を含む OpenAlex サンプル」と補強する。

### 3.4 任意（改善推奨）

#### G. Figure 4（bootstrap CI）の視認性
- 9 文明圏 × 箱ひげが多く、印刷サイズを超える可能性がある。高解像度 PNG (300 dpi 以上) の確認を推奨。

#### H. PNR 略号の統一
- 全文で "point of no return" と略号 "PNR" が混在。Table キャプションでは PNR、本文ではフル表記が多い。用例を統一する。

---

## 4. 総合評価

### 4.1 強み
- **再現性**: 公開リポ `bougtoir/researcher-mobility-ode` をクリーン clone して `bash reproduce.sh` 一括実行可能。全数値は `results/` CSV から動的生成され、捏造・ハードコードなし。
- **整合性**: 修正後の annual projection は observed/projected 分離、右打ち切り処理、訓練期 first-compartment 配分を反映し、コードと本文が一致。
- **主張の慎重さ**: 因果を主張せず「mechanical perturbation」「early warning」「scenario tool」として位置づける。
- **ストーリー回収**: Intro の 5 RQs と 4 Hs が Results/Discussion/Conclusion で原則的に回収。特に「早期介入 → 文明圏多様性維持」という目標が Conclusion で結ばれている。

### 4.2 主要な弱み
- Markdown セクション番号の不連続（docx は OK）。
- MAPE 42.5% が高く、警報系としての解釈を一段強化する必要がある。
- RQ4 の「policy packages」は single-lever counterfactual に対して言葉が大きい。
- Inter-civilisation flow は approximation/proxy であることを、表題・キャプション・本文でさらに強調すべき。

### 4.3 投稿準備判定
**条件付き可（Conditional Accept with minor revisions）**。必須は A（Markdown 扱い）のみ。B・C・D は本文の微調整で対応可能。E・F は Minor revision 対応として積んでおく。

---

## 5. 未対応・要検討事項

- `manuscript_full_article.md` のセクション番号連番化、または submission 用 docx のみ使用する方針の明文化。
- RQ4 文言の修正または 2 レバー policy package 表の追加。
- MAPE 42.5% に対する摘要・Discussion レベルでの追加 caveat。
- 図表の最終印刷品質（dpi）確認。
- PNR 略号の全文統一。

---

## 6. 検証に使用したコマンド（再現用）

```bash
git clone --depth=1 https://github.com/bougtoir/researcher-mobility-ode
cd researcher-mobility-ode
bash reproduce.sh
# 出力: docs/manuscript_full_article.docx, .md, .pptx, _submission.zip
```

主な整合性チェック:

```python
import pandas as pd
pd.read_csv("results/endogenous/equilibrium_summary.csv")[["group","T_equilibrium","M_threshold","T_over_M","margin_to_threshold_T","I0","r"]]
pd.read_csv("results/point_of_no_return.csv").query("group=='Japanese'")
pd.read_csv("results/annual/projected_ode_rates.csv").query("origin_group=='Anglosphere ex-US' & year>=2017")[["year","I_total","d"]]
```
