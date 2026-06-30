"""コアデータモデル: 患者・薬剤マスタ・投薬イベント."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class Sex(str, Enum):
    MALE = "male"
    FEMALE = "female"


class Delivery(str, Enum):
    BOLUS = "bolus"
    INFUSION = "infusion"


@dataclass
class Patient:
    """患者・症例の人口統計学的情報.

    体重ベース投与・PK/PDモデル・局所麻酔薬極量計算に必須。
    """

    age_years: float
    sex: Sex
    weight_kg: float
    height_cm: float
    patient_id: Optional[str] = None
    asa_ps: Optional[int] = None

    @property
    def bmi(self) -> float:
        h = self.height_cm / 100.0
        return self.weight_kg / (h * h)

    @property
    def lbm_james(self) -> float:
        """James式の除脂肪体重(LBM, kg). Marsh/Minto等の共変量に使用."""
        w, h = self.weight_kg, self.height_cm
        if self.sex is Sex.MALE:
            return 1.1 * w - 128.0 * (w / h) ** 2
        return 1.07 * w - 148.0 * (w / h) ** 2

    @property
    def ibw_devine(self) -> float:
        """Devine式の理想体重(IBW, kg)."""
        inches_over_152 = max(0.0, (self.height_cm - 152.4) / 2.54)
        base = 50.0 if self.sex is Sex.MALE else 45.5
        return base + 2.3 * inches_over_152


@dataclass
class DrugMaster:
    """薬剤マスタ1レコード（外部YAMLの1エントリ）.

    剤型・包装・薬価・投与可能様式・PKモデル選択等を保持。
    """

    id: str
    generic_name: str
    category: str
    container_volume_ml: float
    concentration: float          # strength_unit 当たりの値（例 mg/ml なら mg/ml の数値）
    strength_unit: str
    package_unit: str
    delivery: list[Delivery]
    dose_units: list[str]
    brand_name: Optional[str] = None
    formulation: Optional[str] = None
    nhi_price: Optional[float] = None        # 円/容器（要施設検証）
    nhi_price_date: Optional[str] = None
    billing_rule: str = "round_up_vial"
    routes: list[str] = field(default_factory=list)
    pkpd_enabled: bool = False
    pk_model: Optional[str] = None
    color: Optional[str] = None
    # 局所麻酔薬の極量（mg/kg）。該当薬のみ設定。
    max_dose_mg_per_kg: Optional[float] = None
    max_dose_mg_per_kg_with_epi: Optional[float] = None
    # 輸液関連
    fluid_type: Optional[str] = None
    is_output: bool = False

    @property
    def mass_per_container(self) -> float:
        """1容器あたりの有効成分量（concentration の単位 × 容量）.

        例: 10 mg/ml × 20 ml = 200 mg。輸液(ml/ml)では ml 量となる。
        """
        return self.concentration * self.container_volume_ml

    def supports(self, delivery: Delivery) -> bool:
        return delivery in self.delivery


@dataclass
class MedEvent:
    """投薬イベント1件.

    単回(bolus): start_time と dose/dose_unit。
    持続(infusion): レート変更点を1イベントとして列で表現する。
      - rate/rate_unit を指定し、end_time(=次の変更/中止時刻) で区間を確定。
      - rate=0 は中止を表す。
    """

    drug_id: str
    start_time: datetime
    delivery: Delivery
    dose: Optional[float] = None        # bolus 用
    dose_unit: Optional[str] = None
    rate: Optional[float] = None        # infusion 用
    rate_unit: Optional[str] = None
    end_time: Optional[datetime] = None
    note: Optional[str] = None

    def duration_min(self) -> Optional[float]:
        if self.end_time is None:
            return None
        return (self.end_time - self.start_time).total_seconds() / 60.0
