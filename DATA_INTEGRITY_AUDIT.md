# wip 配下 データ/出所 捏造監査（first-pass）

方法: 全55ディレクトリを自動スキャン（実データ読込の有無 / np.array・DataFrameのリテラル数 / DOI・出所注記の有無 / 合成・乱数の使用）＋高リスク項目を手動精査。
判定は「経験的（実測）と称しているのに、データが第三者の一次資料まで辿れない／発明値・想定値である」ものを問題とする。
シミュレーションは**明示されていれば正当**。

> 注意: これは一次スクリーニング。Tier B/C は原稿本文の主張まで含めた精読で最終確定が必要。

---

## Tier A — 捏造確定/濃厚（最優先・現行未修正）

### 1. weibull-clinical-dropout 【確定】
- TBの k=1.22–1.31・95%CI・R²・n をコードにリテラル埋め込み（`TB_RESULTS`）。解析実体なし。
- 比較ドメインの retention 配列はコード上 `# Typical retention...`＝想定値。
- 原稿本文は「reconstructed from published Kaplan-Meier curves」「national programmes」と記載＝出所偽装。
- 引用（Parmar=24か月MDR-TB, Lacerda=文献レビュー等）が本文の主張と不一致。
- → fabrication＋falsification。現在別ブランチで実データ再解析(A1-min)へ移行中。

### 2. canonical_curves_reexamination 【濃厚】
- 52本の"定説曲線"を「現代的手法で再検証、65%が頑健性テストに落ちる」と強い経験的主張。
- しかし各曲線データは `np.array([...])` のハードコード48箇所で、注記は "Representative data from multiple field trials" 等、**出所DOI・digitize座標なし**（実データ読込ほぼ無し）。
- 発明/目分量の"代表値"に対して外れ値依存性やAIC比較を回しても、結論は元データ次第で無意味。実測と称するなら捏造相当。
- → 各曲線を実際の出所データ（原著の図表digitize or 公開データ）に置換しない限り、経験的主張は撤回すべき。

---

## Tier B — 要確認/グレー（出所提示が不十分・主観コーディング）

### 3. medical_sapir_whorf（karoshi ITS）
- 国際比較のIHD/脳血管死亡率が `intl_data` にハードコード。コメントは "approximate values from WHO ... for illustrative comparison"。
- WHO出典は明記だが、数値がWHOデータから抽出された形跡なし（data読込0）。原稿が実測WHO値として提示していれば要修正（実値抽出 or 「概略値・図示用」と明示）。

### 4. beyond-gdp-national-power
- `stock_index=0.40` 等、歴史的主体の指標が著者の**主観コーディング**（根拠コメント付き）。DOIは歴史的事実の裏付け用。
- 比較歴史/政治学のexpert codingとしては正当だが、「客観的な実測データ」と誤認させる書き方なら要修正。主観コーディングであることと採点基準を原稿に明示すれば可。

---

## Tier C — 実データパイプライン確認済み（問題なしと判断、精読推奨）
実際に data ファイル（xlsx/csv/DB）を読み込み、出所注記/DOIを伴うもの：
- ndb-pain-regional-variation-japan（NDB Open Data xlsx を読込。"synthetic"は合成麻薬の薬効分類で誤検出）
- yago_cs_bleeding（data.xlsm 実臨床データ）
- yago_ionv（14ファイル読込）
- pwv_vitaldb_analysis（VitalDB）
- tempo-effect-paper（data+DOI 46）
- discharged_secrets_ijcip（OpenAlex, data20/DOI61）
- round1_crime_analysis / stem_cell_seasonality / medical_accident_its_analysis / vaporizer-price-study / denisovan-archaic-dna-analysis / khmer_inscription_analysis / buddhist_food_lexicon_map / archaic_language_typology

## Tier S — シミュレーション/PoC（合成データ。原稿での"明示"を各自点検）
合成/乱数が主体。**「シミュレーションである」と原稿・コードで明示されていれば正当**。明示なく実測と誤認させる箇所がないか自己点検を推奨：
- threebody_pk_compartment, spectral-causality-{a2-ecd,brainstorm,jmlr}, gdp_tempo_poc, healthcare_tempo_poc, gdp_cwon_integration, sr_ancova_framework, dvs_noise_inverse_problem, clinical_noise_inverse_problem, zero_calibration_pmea, tasuki-electoral-model, sits9, ava_lllt_hypothesis, flood-prediction-review, montmorillonite_{oil,decaf}, gdp_tempo_paper, healthcare_economic_effect

## 対象外（アプリ/ツール類）
paper-dashboard, project-hub, garment-printer-app, pose_alignment_tool, anesthesia-record, biwa_archaeological_prospection, landmine_transparent_map, meeting-slides, slides, color_cooking_concept, tommo_taste_receptor_2025-0057, spectral-causality-a2-ecd

---

## 推奨対応
1. **Tier A（weibull, canonical_curves）**: 経験的主張のまま投稿しない。実データ化 or シミュレーション/概念研究として出所を偽らず再フレーム。
2. **Tier B**: 数値の出所を実データから再抽出、または「概略値/主観コーディング」と明示。
3. **Tier S**: 各原稿の Methods/Abstract に「シミュレーション/合成データ」と明示されているか点検。
