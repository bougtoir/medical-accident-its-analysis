"""麻酔記録（補助記録）アプリ コアパッケージ.

GE CARESCAPE B650 等から取得したバイタルと、投薬イベント・コスト算定・
効果部位濃度(Ce)推定・局所麻酔薬の極量管理を扱う。

設計方針:
- 薬剤マスタはプログラム外の YAML（data/drug_master.yaml）として保持し、起動時に読み込む。
- 帳票レイアウトは様式テンプレートとして差し替え可能（JSA様式 / 院内様式 等）。
"""

from .models import Patient, DrugMaster, MedEvent, Sex, Delivery
from .drug_master import DrugMasterFile, load_drug_master

__all__ = [
    "Patient",
    "DrugMaster",
    "MedEvent",
    "Sex",
    "Delivery",
    "DrugMasterFile",
    "load_drug_master",
]
