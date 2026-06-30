# anesthesia-record

麻酔記録（**補助記録**）のためのコア・ライブラリ。GE CARESCAPE B650 等から取得した
バイタル（VitalRecorder / VSCapture の CSV・`.vital`）と、投薬イベント・コスト算定・
効果部位濃度(Ce)推定・局所麻酔薬の極量管理を扱う。

> ⚠️ 本ツールは**補助記録・研究用途**であり、正式な診療録や投与判断の根拠に用いてはならない。
> 薬価・極量・PKモデル等は**各施設で検証**すること（同梱マスタの薬価はサンプル値）。

## 特徴
- **薬剤・輸液マスタは外部参照ファイル**（`data/drug_master.yaml`、起動時ホットリロード）。
- **投薬イベント**: 時刻指定、単回(bolus)／持続(infusion)、体重ベース投与の自動換算。
- **コスト算定**: 剤型(容器)考慮。`billing_rule`（バイアル単位切上げ＝残液破棄課金／按分）切替。
- **効果部位濃度(Ce)推定**: 3-コンパートメント+ke0。propofol(Marsh/Schnider)、
  remifentanil(Minto)、fentanyl(Shafer・近似)。
- **局所麻酔薬の極量管理**: mg/kg 累積に対する警告（アドレナリン添加で上限切替）。
- **チャート出力**: バイタル + 投薬注記 + Ce を1枚に描画（様式テンプレート差し替え可能）。

## セットアップ
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## デモ
```bash
PYTHONPATH=. python demo.py    # demo_chart.png を生成
```

## テスト
```bash
PYTHONPATH=. pytest -q
```

## 構成
```
data/drug_master.yaml          薬剤・輸液マスタ（外部参照ファイル）
anesthesia_record/
  models.py                    Patient / DrugMaster / MedEvent
  drug_master.py               マスタYAMLローダ（ホットリロード）
  units.py                     投与量の単位変換（→ mg / ml）
  cost.py                      コスト算定（剤型考慮）
  pkpd.py                      効果部位濃度(Ce)推定エンジン
  local_anesthetic.py          局所麻酔薬 極量管理
  vitals.py                    バイタル CSV / .vital 取り込み・時刻整合
  chart.py                     チャート描画（様式テンプレート）
tests/                         pytest
demo.py                        一連の流れのデモ
```

## 薬剤マスタの編集
`data/drug_master.yaml` をプログラム外で編集する。主なフィールドは README とファイル冒頭の
コメントを参照。`pkpd_enabled: true` の薬剤のみ Ce 推定の対象。`max_dose_mg_per_kg` を持つ
局所麻酔薬は極量管理の対象。
