# Sales Conversation Dynamics

ターンあたりの単語数の時間的変化が、説得・成約にどう関係するかを分析します。

## データセット

- **PersuasionForGood** (メイン): 英語の慈善寄付説得対話 1,017件。寄付成否/金額を指標に使用。
- **CyberAgentAILab/salestalk-dataset** (検証): 日本語のB2Cセールス対話 109件。購入意欲スコアの前後差を指標に使用。

## ディレクトリ

- `data/`: 生データおよび前処理済みデータ
- `src/`: 分析スクリプト
- `output/`: 数値結果・表
- `figures/`: 可視化画像

## 実行

```bash
pip install -r requirements.txt
cd src
python run_analysis.py
```
