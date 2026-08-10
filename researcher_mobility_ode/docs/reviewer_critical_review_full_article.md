# 査読者視点 批判的レビュー：Research Policy full-article manuscript

**対象原稿**: `docs/manuscript_full_article.docx`（生成日: 2026-08-09）  
**検証リビジョン**: `devin/researcher-mobility-ode-full-article` 最新コミット + 公開リポ `bougtoir/researcher-mobility-ode` クリーン clone  
**レビュー観点**: ストーリー・フロー、伏線回収、再現性、実データとの整合性、主張の強さ、図表・文献の整合性

---

## 1. 実施した検証

- **公開リポ再現性**: `git clone --depth=1 https://github.com/bougtoir/researcher-mobility-ode` 後に `bash reproduce.sh` を実行。全 `results/`、図表、docx/pptx/md が再生成され、原稿掲載数値と一致。
- **機械的整合性**: docx 内 7 図・12 表を `python-docx` で解析。すべて本文で初出順に言及され、キャプション付きで同一ファイル内にインライン配置されていることを確認。
- **文献番号**: 1–15 がすべて Vancouver 順で出現し、Reference list も 1–15 で完結。orphan/phantom なし。
- **数値の動的生成**: `scripts/build_full_manuscript.py` が `results/endogenous/equilibrium_summary.csv`、`results/annual/*.csv` 等を読み込み、本文・表・図を生成。ハードコードされた数値は確認されなかった。
- **safety factor ダイナミック化**: 原稿内「safety factor 0.5」は `eq["r"] / eq["r_critical"]` から動的に読み出され、現在は 0.50 として記載される。`grep` で literal "0.5" の残存はなし。

---

## 2. 優先度別指摘

### 2.1 最優先（投稿前に必須）

#### A. Markdown コンパニオンは投稿原稿として不適
- **問題**: `manuscript_full_article.md` のセクション番号が不連続（4.1–4.4 の次に 4.10、5.1–5.4 の次に 5.6–5.8、6.4–6.7 のみ）。docx は連続（4.1–4.11、5.1–5.8、6.1–6.7、7.1）。
- **影響**: 編集・査読者が md を開いた場合、構成が混乱する。docx は原稿版として OK だが、md は「補助」または修正が必要。
- **修正案**: 提出用は docx のみとし、md は `README` や GitHub 表示用に「supplementary / not submission formatted」と明記。あるいは `write_markdown()` でも `add_numbered_heading()` と同じ連番ロジックを適用。

#### B. `Highlights` の値と本文の丸め誤差
- **問題**: 本文・Abstract は「factor 0.246×」だが、Highlights は旧版で「factor 0.25×」と丸められていた（修正済み: 0.246×）。
- **影響**: ハイライトと本文の数値が食い違うと、査読者に数値の信頼性を疑われる。
- **修正済み**: `build_full_manuscript.py` の highlights を `_fmt(..., 3)` に変更し、`reproduce.sh` で再生成。現在は一致。

#### C. `README.md` が旧記述のまま
- **問題**: README は `src/requirements.txt` を参照し、旧パイプライン（openalex_client → cohort_extraction → ode_model → ode_model_endogenous）を記載。`reproduce.sh` 一括実行が書かれていない。また「confidence intervals are not yet computed」とあるが、現在は bootstrap CI 実施済み。
- **影響**: 再現性を確認しようとする読者が、古い手順や不存在ファイルに戸惑う。研究公正上の再現性記述と実態が乖離する。
- **修正済み**: README を `reproduce.sh` 一括実行・現行アウトプット・現在のモデル仮説に更新。

### 2.2 高優先（Major revision リスク）

#### D. 「5 つの研究問い」への回答が 5.6–5.8 / 6.4–6.6 で明確に回収されている
- **確認事項**: RQ5（年次レート推定・2017-2026 予測・実測との整合）と RQ4（safety-factor-bound policy packages）は、Results 5.6–5.8、Discussion 6.4–6.6 で回収。Intro の「early, safety-factor-bound intervention」が Conclusion で「detect divergence early and intervene in a safety-factor-bound way」と回収されている。
- **残る懸念**: RQ4 の「packages」という言葉に対し、本文では単一レバーの感応度や counterfactual しか示していない。政策「パッケージ」としての最適組み合わせ（例: dropout 抑制 + PI 昇進の交互効果）は定量化されていない。Discussion 6.1 で「二つのレバーを同時に変えると相乗効果があると考えられる」とは書かれているが、数値的な packages はない。
- **修正案**: 表に「policy package」シミュレーション（例: d -10% + p_D +10%）を追加するか、RQ4 の文言を「safety-factor-bound single-lever scenarios」に弱める。

#### E. 因果表現の追加チェック
- **確認事項**: Discussion 6.1 で「counterfactuals ... are mechanical perturbations, not causal estimates」と明記。Conclusion も「mechanical sense」を踏襲。
- **残る懸念**: Abstract の「A simulated reduction in dropout yields the largest margin gain...」は、モデル内の機械的シミュレーションであることを本文で補足しているが、Abstract 単独では「実際の政策効果」に読まれかねない。
- **修正案**: Abstract に「in the fitted model」または「in this mechanical scenario」を挿入するか、そのままにして本文の caveat を参照する形にする。

### 2.3 中優先（Minor revision / 補足説明）

#### F. 2017-2023 予測精度（MAPE 35.9%）の解釈
- **問題**: MAPE 35.9% は高い。原稿は zero-observed cells や小コンパートメントの存在を理由に説明している（Results 5.7）が、読者にとって「早期警報系」として十分か疑問視される可能性がある。
- **修正案**: Discussion の Limitations で「35.9% は noisy small compartments を含む full-grid 評価であり、警報系としては二値的な『閾値超過』フラグを主眼とすべき」と追加。現在の記述は部分的に含まれているが、一段階強調してもよい。

#### G. Inter-civilisation 流れの定義
- **問題**: `A`（海外 early-career）コンパートメントは特定文明圏への流出先ではなく「海外全体」の集計。年次遷移行列の `A → D`（帰国）は実際の帰国先を区別しない。
- **影響**: 文明圏間の引き抜き合いを個別にモデル化しているわけではない。これは Methods 4.10 と Limitations 6.7 で言及されているが、Results 5.6 の heatmap 表題「Inter-civilisation flows」はやや強めの言葉。
- **修正案**: 「Author-years abroad by current group」または「Cross-civilisation mobility approximation」に表題・キャプションを弱めるか、本文で「proxy」であることを追加説明。

#### H. 「Hindu」等の命名と説明
- **問題**: グループ名 "Hindu" は宗教・文明圏を指すが、対象はインドを中心とする研究者。査読者がサンプリングバイアスや命名の妥当性を問う可能性がある。
- **修正案**: Methods 3 で「Hindu 文明圏 = インド・ネパール・スリランカ等を含む OpenAlex サンプル」と定義されていることを再度確認。Introduction のマッピング説明で一言補強。

### 2.4 任意（改善推奨）

#### I. 図の視認性
- **問題**: Figure 4（bootstrap CI）などは 9 グループ × 箱ひげで小さい。Research Policy のオンライン添付で高解像度を要求される可能性がある。
- **修正案**: `dpi=300` で PNG 保存済みであれば問題なし。`docs/figures/` の dpi を確認し、必要に応じて 600 dpi に上げる。

#### J. 用語・略号の first-use 定義
- **確認**: Abstract で `M = k × c_bar`、Results でも `T = D + H_D + P_D` を定義している。`c_bar` と `k` の first-use は Abstract と Methods 4.3 でカバー。
- **残る懸念**: `PNR` という略号が本文で使われているか確認。全文検索すると "point of no return" は頻出するが "PNR" 略号は Table キャプションでしか使われていない可能性。統一する。

---

## 3. 総合評価

### 3.1 強み
- **再現性**: 公開リポ一括再現可能。`reproduce.sh` は data/CSV から docx まで完結。
- **整合性**: 数値がすべて `results/` CSV から動的生成され、ハードコード/捏造なし。
- **主張の慎重さ**: 因果を主張せず「mechanical perturbation」「early warning」「scenario tool」として位置づける。
- **ストーリー回収**: Intro の 5 RQs / 4 Hs が Results/Discussion で原則的に回収。特に「早期介入 → 多様性維持」という目標は Conclusion で明確に結ばれている。

### 3.2 主要な弱み
- **MD コンパニオンの不連続番号**が唯一の「投稿そのものを妨害しうる」整形問題。
- **RQ4 の「packages」**は本文の counterfactual 設計より広い。最適 policy package の数値がない。
- **MAPE 35.9%** は早期警報系として読者に懸念を与える。本文では対応策（zero-observed cells, small compartments）を説明しているが、摘要や discussion でさらに一文補強するとよい。

### 3.3 投稿準備判定
**条件付き可（Conditional Accept with minor revisions）**。
- 必須: Markdown コンパニオンの扱い決定、README の最新化（済）、Highlights の丸め一致（済）。
- 推奨: RQ4 文言の調整、MAPE 解釈の追加強調、Figure/Table タイトルの用語強化。

---

## 4. 適用済み修正

1. **safety factor 動的化**: `build_full_manuscript.py` で `safety_factor = (eq["r"] / eq["r_critical"]).min()` を読み込み、全 safety-factor 記述を f-string 化。
2. **Highlights 丸め一致**: `_fmt(closest['critical_factor'], 3)` に統一（0.246×）。
3. **README 更新**: `reproduce.sh` 一括実行、現行アウトプット、現在のモデル仮説を記載。
4. **公開リポ同期**: `bougtoir/researcher-mobility-ode` への subtree 強制 push 後、クリーン clone から `reproduce.sh` が成功することを確認。

---

## 5. 未対応・要検討事項

- `manuscript_full_article.md` のセクション番号連番化、または submission 用 docx のみを使用する方針。
- RQ4 の「policy packages」を文言修正するか、追加 counterfactual を実装するか。
- 年次予測の MAPE 35.9% に対する摘要・Discussion レベルでの追加 caveat。
- 図表の最終印刷品質（dpi）確認。
