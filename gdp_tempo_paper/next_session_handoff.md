# 次セッション引き継ぎ: Economica投稿準備

## 決定事項
- **投稿先**: Economica (1921年創刊, LSE, Wiley)
- **Fee**: $0 (submission fee無料、Subscription選択ならAPC $0)
- **投稿URL**: https://editorialexpress.com/economica/
- **形式**: PDF提出

## 前セッションで完了済み
- PR #101 (JEDC準備) → merged
- PR #102 (Empirical Economics準備) → merged
- 現在のmainブランチにはEE形式のフロントマターが入っている

## Economica向けに必要な作業

### A. 追加解析（フォークブランチで実施）
ナレッジ「追加解析はフォークブランチで実施する」に従い、mainから新ブランチを作成して作業。

#### 優先度高（必須）
1. **Solow残差の歴史的分解シミュレーション**
   - 各国について M0のTFP vs M2/M4のTFP を比較
   - TFPの何%がtempo artifact（タイミングの帳簿上の歪み）か定量化
   - 例: 「日本の1990年代TFP低下の約X%はμ(t)ドリフトで説明」
   - **Economicaの「So what?」への核心的回答**

2. **反事実シミュレーション: 「もしβが公式統計に含まれていたら」**
   - CWON公式値 vs β補正後の国民富裕度を比較
   - 国ごとに「公式統計がどれだけ過小/過大評価しているか」可視化
   - 政策含意を具体化

#### 優先度中
3. **将来予測シミュレーション（2020-2040）**
   - μ(t)トレンド継続 vs 安定化シナリオ
   - AI/デジタル投資急増のGDP計測への影響

4. **クロスカントリー異質性のクラスター分析**
   - (μ̂, β̂) で国をクラスター化
   - 製造業 vs サービス vs 資源国

#### 優先度低
5. **δ(t) 頑健性チェック**
6. **Monte Carlo identification sharpness**

### B. フレーミング調整
- **現在**: 「計測手法を人口学から移植」（RIOW向け）
- **Economica向け**: 「成長会計の見えていなかった部分を明らかにし、TFPの再解釈と国富の再評価を行う」
- タイトル・Abstract・Introduction を「経済学的発見」として再構成
- 人口学アナロジーは「フック」として残すが中心ではなくする

### C. フォーマット調整（EE → Economica）
- Economicaの投稿規定を確認（Author Guidelines）
- EE (Springer) → Economica (Wiley/LSE) のフォーマット差分を確認
  - 参考文献スタイル
  - Abstract語数制限
  - AI宣言形式
  - カバーレター
- build_docx_pptx.py のdocstring更新

## Economicaスコープ情報
- **公式**: "all branches of economics, of interest to general readers"
- **一般経済学誌** — 計測ジャーナル（RIOW）ではない
- **編集長**: Timothy Besley (政治経済学), Wouter den Haan (マクロ), Rachel Ngai (マクロ/成長)
- **最近掲載例**: エネルギーショックとGDP (Bachmann et al. 2024)、寿命と長期成長 (Kuhn & Prettner 2022)
- **RIOWのMD理由「計測手法の応用に過ぎない」はEconomicaでは問題にならない**
- フィリップス曲線(1958)、コース「企業の本質」(1937)を掲載した歴史あるジャーナル

## 歴史的意義
- Economica 1921年創刊 ≈ 彦根高等商業学校 1922年創立
- LSEの「実学としての経済学」= 彦根高商の「士魂商才」の精神と共鳴

## リポジトリ情報
- リポジトリ: /home/ubuntu/repos/wip/
- プロジェクト: /home/ubuntu/repos/wip/gdp_tempo_paper/
- 原稿(EN): gdp_tempo_paper/manuscript/manuscript_en.md
- 原稿(JA): gdp_tempo_paper/manuscript/manuscript_ja.md
- カバーレター: gdp_tempo_paper/cover_letter/
- スクリプト: gdp_tempo_paper/scripts/
- ビルド: gdp_tempo_paper/scripts/build_docx_pptx.py
- 図表生成: gdp_tempo_paper/scripts/make_fig3_and_fig5.py

## RIOW MD reject の要点（参考）
- Editor: Robert Inklaar
- 理由: 「計測手法の拡張ではなく、既存手法の適用」
- M3(β追加)とM4(joint)がOOS改善しない点を指摘
- **スコープ違いであり質の問題ではない**
