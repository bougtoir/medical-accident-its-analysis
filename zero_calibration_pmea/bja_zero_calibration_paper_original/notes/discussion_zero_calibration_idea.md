# ゼロ校正不要論：CCC枠組みによる考察素材

## 着想の検証：「適切に設計すればゼロ校正は不要なはず」→ 正しい

---

## 1. なぜ現在ゼロ校正が必要か（現行システムの設計制約）

現行の観血的動脈圧測定系は以下の構成をとる：

```
カテーテル先端（血管内） → 液充填チューブ → 外部トランスデューサ → モニター
```

この構成では3つの系統的オフセットが生じる：

| オフセット源 | 物理的原因 | 大きさ |
|---|---|---|
| **静水圧カラム** | トランスデューサと測定点の高低差 ΔP = ρgh | ~0.74 mmHg/cm height差 |
| **大気圧変動** | ゲージ圧測定（大気圧基準） | ~760 mmHg を基準にとる |
| **トランスデューサドリフト** | ストレインゲージの経時変化 | 数 mmHg/日 |

**ゼロ校正の操作**：三方活栓を開放 → トランスデューサを大気に暴露 → 0 mmHg にリセット

つまり、ゼロ校正とは**オフセット（切片）の除去操作**に他ならない。

---

## 2. 工学的に不要にできる根拠

### A. カテーテル先端センサ（Millar Mikro-Cath等）

- MEMS圧電抵抗素子をカテーテル先端に直接搭載
- **液充填カラムが存在しない** → 静水圧オフセット = 0
- 患者体位変更の影響を受けない（Millar社："No need to calibrate to patient height"）
- ただし挿入前の大気圧ゼロ校正は依然必要（大気圧基準の問題）

### B. 絶対圧センサ + 気圧補償

- 絶対圧を測定し、モニター内蔵の気圧センサで大気圧を電子的に差し引く
- 手動ゼロ校正が**原理的に不要**になる
- 気圧変動（天候、手術室の陽圧換気環境）も自動補償可能

### C. 自己校正MEMS（Self-Calibrating MEMS）

- チップ上に参照圧力キャビティを内蔵（Kang et al., Sensors 2022）
- 液体-気体相転移を利用した既知圧力点で周期的に自動校正
- 長期ドリフトを原理的に排除

### まとめ：必要な設計要素

| 現行の問題 | 解決する設計 | 結果 |
|---|---|---|
| 静水圧カラム | 先端センサ | ΔP = 0 |
| 大気圧基準 | 絶対圧 + 気圧補償 | 自動ゼロ |
| ドリフト | 自己校正MEMS | 長期安定 |

**3つすべてを実装すれば、手動ゼロ校正は原理的に不要。**

---

## 3. CCCフレームワークとの接続（ここが論文的に重要）

### ゼロ校正はCCCの何を操作しているか？

Lin's CCC の分解: **ρ_c = r × C_b**

ここで C_b（bias correction factor）はさらに分解できる：

```
C_b = 2 / (v + 1/v + u²)

v = σ₁/σ₂  （scale shift：スケール比）
u = (μ₁ - μ₂) / √(σ₁σ₂)  （location shift：位置ずれ）
```

**ゼロ校正が補正するのはuのみ**（location shift = オフセット除去）。

つまり：
- ゼロ校正後：u → 0（平均差が消える）
- しかし：v ≠ 1 であれば **C_b < 1 のまま**
- すなわち：**ゲインエラー（スケール不一致）はゼロ校正では補正されない**

### 具体例

ゼロ校正後のデバイスで以下が観察されるとする：

```
Bland-Altman: bias ≈ 0 mmHg（ゼロ校正が成功）
しかし: 真の関係は P_device = 1.08 × P_true（8%のゲインエラー）
```

- BA plot: bias ≈ 0 に見える（平均では一致）
- しかし低圧域で過小評価、高圧域で過大評価（proportional bias）
- **PE はゲインエラーの存在下で依然 >30% になりうる**

CCC分解：
- r = 0.98（高精度：データは回帰線上に緊密）
- C_b = 0.95（ゲインエラーのため < 1）
- **CCC = 0.93**（見かけ上の「良好な一致」だが、スケール不一致が隠れている）

→ ゼロ校正はuを消すが、vを1にはしない。CCCのC_b分解によって初めてこの残存エラーの性質が可視化される。

---

## 4. 考察に挿入する議論のロジック（提案）

### ロジックの流れ

1. **現状認識**：観血的動脈圧モニタリングではゼロ校正が臨床的に不可欠とされている。同様に、非侵襲COモニターでも各種自動校正機構（ClearSight の Physiocal™、NICOM のバイオリアクタンス位相基準等）が実装されている。

2. **工学的考察**：しかしこれらの校正操作は本質的に**オフセット補正（location shift の除去）**であり、**スケール不一致（scale shift）**は補正しない。カテーテル先端MEMSセンサ＋絶対圧測定＋自己校正機構を適切に設計すれば、手動ゼロ校正自体が不要になるはずである。

3. **CCC的解釈**：CCCの C_b 分解は location shift（u）と scale shift（v）を区別できるため、「ゼロ校正後も残存するスケールエラー」を定量的に検出できる。従来のBA plotでは、ゼロ校正後にbias ≈ 0 となった時点で「良好な一致」と判断されがちだが、proportional bias（CO値依存的な誤差）は依然としてLoA内に隠れうる。

4. **含意**：
   - 機器開発者にとって：CCCのC_b分解は、「オフセット補正で解決可能なエラー」と「ゲイン調整が必要なエラー」を区別する**設計指針**となる
   - 規制当局にとって：ゼロ校正後のバリデーションでbias ≈ 0 を示すだけでは不十分であり、C_bの報告によってスケール一致度を個別に評価すべき
   - 臨床家にとって：ゼロ校正の頻度やタイミングが測定精度に与える影響はr（precision）にのみ依存し、C_b（accuracy）は校正操作では改善されない → **精度と正確度の改善策が本質的に異なる**ことの理解

5. **結論的主張**：適切に設計されたセンサでは C_b → 1.0 が**設計段階で達成される**べきであり、CCC分解はその達成度を定量化する唯一の統合指標である。ゼロ校正に頼る設計は、C_bの不足をuの除去で部分的に補償しているに過ぎない。

---

## 5. 非侵襲COモニターへの拡張

| デバイス | 校正機構 | 補正対象 | 補正しないもの |
|---|---|---|---|
| **観血的動脈圧** | 手動ゼロ校正 | 静水圧オフセット（u） | ゲインエラー（v） |
| **ClearSight** | Physiocal™ | Volume clamp setpoint（u） | 圧→CO変換のゲイン（v） |
| **NICOM/Starling** | バイオリアクタンス位相基準 | 位相オフセット（u） | 位相→SV変換のゲイン（v） |
| **FloTrac** | 動脈圧波形較正 | 平均圧オフセット（u） | パルス輪郭→COのゲイン（v） |

すべてのデバイスに共通する構造：
- **自動/手動校正 → u の除去**（BA plot の bias → 0）
- **ゲインエラー → v ≠ 1 のまま**（BA plot では検出困難、CCC の C_b で検出可能）

---

## 6. 論文への挿入案（英語パラグラフ案）

> **On the relationship between zero calibration and the CCC framework**
>
> An important implication of the CCC decomposition relates to the widespread practice of zero calibration in hemodynamic monitoring. In conventional fluid-filled arterial pressure systems, zeroing the transducer to atmospheric pressure at the phlebostatic axis is required to eliminate the hydrostatic column offset. Analogously, non-invasive CO monitors employ auto-calibration routines---such as ClearSight's Physiocal algorithm---to periodically correct measurement offsets. In CCC terms, these calibration procedures address only the location shift component (*u*) of the bias correction factor *C_b*, driving the mean difference toward zero. However, they do not correct the scale shift (*v*): a systematic proportional error (gain != 1) persists even after successful zero calibration. This residual scale error is difficult to detect on a Bland-Altman plot when the overall bias appears negligible, yet it manifests as a *C_b* < 1.0 in the CCC decomposition.
>
> From an engineering perspective, catheter-tip MEMS pressure sensors (e.g., Millar Mikro-Cath) eliminate the hydrostatic column entirely, and absolute pressure sensors with barometric compensation could remove the need for manual atmospheric zeroing. A well-designed measurement system should achieve *C_b* approaching 1.0 without manual calibration---that is, both location shift and scale shift should be minimised by design rather than compensated by periodic calibration. The CCC and its *C_b* component thus serve not only as validation metrics but as engineering design targets: a device requiring frequent recalibration to maintain acceptable *C_b* has a fundamental design limitation that calibration can only partially mask.

---

## 7. 参考文献（追加分）

- Gupta D, Jain A, Ismaeil M. Zero arterial catheters with every change in the height difference of pressure transducer and catheter insertion site. Ann Card Anaesth. 2025;28(2):205. doi:10.4103/aca.aca_198_24
- Kang Y, et al. Development of a flexible integrated self-calibrating MEMS pressure sensor using a liquid-to-vapor phase change. Sensors. 2022;22(24):9737. doi:10.3390/s22249737
- Millar Inc. Mikro-Cath Pressure Catheter. https://millar.com/Clinical/MikroCath/
- Finapres Medical Systems. Physiocal Technology. https://www.finapres.com/technologies/physiocal

---

# English Translation

---

# Zero calibration unnecessary theory: Materials for consideration using the CCC framework

## Verification of idea: “If designed properly, zero calibration should not be necessary” → Correct

---

## 1. Why is zero calibration currently necessary? (Current system design constraints)

The current invasive arterial pressure measurement system has the following configuration:

````
Catheter tip (intravascular) → Fluid-filled tube → External transducer → Monitor
````

This configuration results in three systematic offsets:

| Offset source | Physical cause | Magnitude |
|---|---|---|
| **Hydrostatic pressure column** | Height difference between transducer and measurement point ΔP = ρgh | ~0.74 mmHg/cm height difference |
| **Atmospheric pressure fluctuation** | Gauge pressure measurement (atmospheric pressure reference) | Based on ~760 mmHg |
| **Transducer drift** | Strain gauge change over time | Several mmHg/day |

**Zero calibration operation**: Open the three-way stopcock → expose the transducer to the atmosphere → reset to 0 mmHg

In other words, zero calibration is nothing but an offset (intercept) removal operation.

---

## 2. Reasons why it can be made unnecessary from an engineering standpoint

### A. Catheter tip sensor (Millar Mikro-Cath, etc.)

- MEMS piezoresistive element mounted directly on the catheter tip
- **No liquid-filled column** → Hydrostatic pressure offset = 0
- Unaffected by changes in patient position (Millar: "No need to calibrate to patient height")
- However, atmospheric pressure zero calibration is still required before insertion (problem with atmospheric pressure standards)

### B. Absolute pressure sensor + barometric compensation

- Measures absolute pressure and electronically subtracts atmospheric pressure with the monitor's built-in barometric pressure sensor
- Manual zero calibration becomes **in principle unnecessary**
- Automatically compensates for atmospheric pressure fluctuations (weather, positive pressure ventilation environment in the operating room)

### C. Self-Calibrating MEMS

- Built-in reference pressure cavity on chip (Kang et al., Sensors 2022)
- Periodic automatic calibration at known pressure points using liquid-gas phase transition
- Eliminate long-term drift in principle

### Summary: Necessary design elements

| Current Problem | Design to Solve | Results |
|---|---|---|
| Hydrostatic column | Tip sensor | ΔP = 0 |
| Atmospheric pressure reference | Absolute pressure + pressure compensation | Automatic zero |
| Drift | Self-calibrating MEMS | Long-term stability |

**If all three are implemented, manual zero calibration is not necessary in principle. **

---

## 3. Connection with CCC framework (this is important for the paper)
### What part of the CCC is operated during zero calibration?

Lin's CCC decomposition: **ρ_c = r × C_b**

Here C_b (bias correction factor) can be further decomposed:

````
C_b = 2 / (v + 1/v + u²)

v = σ₁/σ₂ (scale shift: scale ratio)
u = (μ₁ - μ₂) / √(σ₁σ₂) (location shift)
````

**Zero calibration only corrects u** (location shift = offset removal).

That is:
- After zero calibration: u → 0 (average difference disappears)
- But: if v ≠ 1 **C_b < 1 remains**
- i.e.: **Gain error (scale mismatch) is not corrected by zero calibration**

### Specific example

Suppose the following is observed on the device after zero calibration:

````
Bland-Altman: bias ≈ 0 mmHg (zero calibration successful)
But: The true relationship is P_device = 1.08 × P_true (8% gain error)
````

- BA plot: looks like bias ≈ 0 (match on average)
- However, it is underestimated in the low pressure region and overestimated in the high pressure region (proportional bias)
- **PE can still be >30% in the presence of gain error**

CCC decomposition:
- r = 0.98 (high accuracy: data closely lies on the regression line)
- C_b = 0.95 (< 1 due to gain error)
- **CCC = 0.93** (apparent "good match" but hides scale mismatch)

→ Zero calibration erases u but does not set v to 1. The nature of this residual error is visualized for the first time by C_b decomposition of CCC.

---

## 4. Argument logic (proposal) to be inserted into the discussion

### Logic flow

1. **Current status**: Zero calibration is clinically essential for invasive arterial pressure monitoring. Similarly, non-invasive CO monitors have implemented various automatic calibration mechanisms (e.g., ClearSight's Physiocal™, NICOM's bioreactance phase standard, etc.).

2. **Engineering considerations**: However, these calibration operations are essentially **offset corrections (removal of location shifts)** and do not correct for **scale mismatches**. If the catheter tip MEMS sensor + absolute pressure measurement + self-calibration mechanism is appropriately designed, manual zero calibration itself should be unnecessary.
3. **CCC interpretation**: Since CCC's C_b decomposition can distinguish between location shift (u) and scale shift (v), it is possible to quantitatively detect "scale errors that remain even after zero calibration." In conventional BA plots, a "good match" is often judged when bias ≈ 0 after zero calibration, but proportional bias (CO value-dependent error) can still be hidden within the LoA.

4. **Implication**:
   - For equipment developers: CCC C_b decomposition serves as a **design guideline** that distinguishes between "errors that can be resolved by offset correction" and "errors that require gain adjustment"
   - For regulators: It is not enough to show bias ≈ 0 in post-zero validation; scale agreement should be assessed separately by reporting C_b.
   - For clinicians: The impact of zero calibration frequency and timing on measurement accuracy depends only on r (precision), and C_b (accuracy) is not improved by calibration operations → **understanding that measures to improve precision and accuracy are essentially different**
5. **Concluding argument**: C_b → 1.0 should be **achieved at the design stage** for a properly designed sensor, and CCC decomposition is the only integrated metric to quantify that achievement. Designs that rely on zero calibration only partially compensate for the lack of C_b by removing u.

---

## 5. Expansion to non-invasive CO monitoring

| Device | Calibration mechanism | Correction target | What is not corrected |
|---|---|---|---|
| **Invasive Arterial Pressure** | Manual Zero Calibration | Hydrostatic Pressure Offset (u) | Gain Error (v) |
| **ClearSight** | Physiocal™ | Volume clamp setpoint (u) | Pressure → CO conversion gain (v) |
| **NICOM/Starling** | Bioreactance phase reference | Phase offset (u) | Gain of phase → SV conversion (v) |
| **FloTrac** | Arterial pressure waveform calibration | Mean pressure offset (u) | Pulse contour → CO gain (v) |

Structure common to all devices:
- **Auto/manual calibration → removal of u** (BA plot bias → 0)
- **Gain error → v ≠ remains 1** (Hard to detect with BA plot, detectable with C_b of CCC)

---
## 6. Proposed insertion into the paper (proposed English paragraph)

> **On the relationship between zero calibration and the CCC framework**
>
> An important implication of the CCC decomposition relates to the widespread practice of zero calibration in hemodynamic monitoring. In conventional fluid-filled arterial pressure systems, zeroing the transducer to atmospheric pressure at the phlebostatic axis is required to eliminate the hydrostatic column offset. Analogously, non-invasive CO monitors employ auto-calibration routines---such as ClearSight's Physiocal algorithm---to periodically correct measurement offsets. In CCC terms, these calibration procedures address only the location shift component (*u*) of the bias correction factor *C_b*, driving the mean difference toward zero. However, they do not correct the scale shift (*v*): a systematic proportional error (gain != 1) persists even after successful zero calibration. This residual scale error is difficult to detect on a Bland-Altman plot when the overall bias appears negligible, yet it manifests as a *C_b* < 1.0 in the CCC decomposition.
>
> From an engineering perspective, catheter-tip MEMS pressure sensors (e.g., Millar Mikro-Cath) eliminate the hydrostatic column entirely, and absolute pressure sensors with barometric compensation could remove the need for manual atmospheric zeroing. A well-designed measurement system should achieve *C_b* approaching 1.0 without manual calibration---that is, both location shift and scale shift should be minimised by design rather than compensated by periodic calibration. The CCC and its *C_b* component thus serve not only as validation metrics but as engineering design targets: a device requiring frequent recalibration to maintain acceptable *C_b* has a fundamental design limitation that calibration can only partially mask.
---

## 7. References (additional)

- Gupta D, Jain A, Ismaeil M. Zero arterial catheters with every change in the height difference of pressure transducer and catheter insertion site. Ann Card Anaesth. 2025;28(2):205. doi:10.4103/aca.aca_198_24
- Kang Y, et al. Development of a flexible integrated self-calibrating MEMS pressure sensor using a liquid-to-vapor phase change. Sensors. 2022;22(24):9737. doi:10.3390/s22249737
- Millar Inc. Mikro-Cath Pressure Catheter. https://millar.com/Clinical/MikroCath/
- Finapres Medical Systems. Physiocal Technology. https://www.finapres.com/technologies/physiocal
