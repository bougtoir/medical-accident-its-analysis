# Candidate A-H 最小 PoC 結果 — 医療費支出→アウトカム・ラグ

## Headline

39 カ国（OECD + 中国）、1960–2023 年、WB 公開データのみで、
**医療費 → 平均寿命ラグの存在**は一目瞭然：

| 指標 | M0 フロー | M1 定数ラグ | M2 テンポ |
|---|---|---|---|
| 平均寿命 level RMSE 中央値（年） | 0.51 | **0.30** | 0.43 |
| 1年変化 RMSE 中央値（年） | 0.46 | 0.39 | 0.41 |
| M vs M0 level-RMSE 改善国率 | — | **100%** | 77% |
| M vs M0 change-RMSE 改善国率 | — | 100% | 92% |

**定数ラグ中央値 μ\* ≒ 4 年**。つまり**医療費が平均寿命に反映されるのに約4年**。
テンポ・ドリフト中央値は +0.15 年/年だが、M2 の追加改善は限定的（M1 を15% しか上回らない）。

## 解釈

- M0 → M1 の大幅改善 (40%) は、医療費の効果が**本質的にストック性**であることを実証。
  「年々の支出が同年の平均寿命を決める」というナイーブモデルは体系的に間違い。
- μ\* ≒ 4 年のラグは、予防投資・慢性疾患治療の効果発現時期として医学的にも整合。
- M2（テンポ）が弱いことは、**医療費のラグ構造は GDP 投資ラグと違って時変性が小さい**
  ことを示唆。医療支出の予測期間は比較的安定した遅れを持つ。

## GDP PoC との対比

| 領域 | 主効果 | 効果サイズ | 主因 |
|---|---|---|---|
| GDP 候補 A（投資ラグ） | Test B 成長率 +0.03 pp | 小 | 年次動態にわずかに寄与 |
| GDP 候補 D（無形資本） | Test A 水準 +0.39 pp | 中 | 長期水準の欠落分を埋める |
| 医療 候補 A-H（支出ラグ）| 水準 RMSE -0.21 年 | **大** | そもそもストック性が支配的 |

医療の場合、ラグ効果は**隠れていた最大の構造特徴**。GDP 投資ラグが年次 RMSE の
1–2% しか削らないのと対照的に、医療では水準 RMSE を 40% 削減する。

## 次ステップ

1. **候補 D-H（忘れられたバケット乗数）の実装**: OECD SHA で医療費を HC.1 治療／
   HC.3 長期ケア／HC.6 予防／HC.R 医療 R&D に分解し、各バケットの乗数 λ_b を同定。
   仮説は λ_prev, λ_R&D ≫ λ_cur で、米国型（治療偏重）と日本型（皆保険＋予防）の
   差を説明できること。
2. **候補 B-H（同時健康人口）**: 年齢別 morbidity で effective health-need を構築。
3. **フロー＋ストック統合会計**: `GDP PoC` の joint identification 枠組みをそのまま
   医療に流用し、E(t) と H(t) を同時推定。

## 図

- `figures/figAH1_level_rmse.png` — 国別 level RMSE 棒グラフ。
- `figures/figAH2_improvements.png` — M1, M2 改善量のボックス。
- `figures/figAH3_tempo_scatter.png` — μ_H1（テンポ・ドリフト） vs M1→M2 改善。

## データ

- `data/poc_AH_results.csv` — 国別全指標。
- `data/poc_AH_summary.json` — 集計。

## 再現

```bash
cd healthcare_tempo_poc
python scripts/fetch_wb_health.py
python scripts/run_poc_AH.py
```

---

*Data: World Bank WDI (SH.XPD.CHEX.PP.CD, SH.XPD.CHEX.GD.ZS, SP.DYN.LE00.IN).
Analysis 2026-04-21.*
