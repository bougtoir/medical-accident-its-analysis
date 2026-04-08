"""
Bland-Altman Sphere Simulation
==============================

BAプロットの幾何学的拡張: 3D球面回転体による測定一致度の可視化

各データペア (a, b) を球の南極→北極軸に沿って配置し、
一致度に応じた半径で回転体を生成。元の球との体積比 (VOR) で
品質を定量化する。

生成物:
- ba_sphere_dashboard.html: インタラクティブ3Dダッシュボード
"""

import numpy as np
from scipy import stats
from scipy.interpolate import CubicSpline
from scipy.special import legendre
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json


# =============================================================================
# 1. シミュレーションデータ生成
# =============================================================================

def generate_scenario(
    name: str,
    n: int = 60,
    seed: int = 42,
    bias: float = 0.0,
    random_sd: float = 0.0,
    scale_slope: float = 0.0,
    scale_noise: float = 0.0,
) -> dict:
    """測定ペアデータを生成する。

    Parameters
    ----------
    name : シナリオ名
    n : データ点数
    seed : 乱数シード
    bias : 系統誤差（定数バイアス）
    random_sd : ランダム誤差の標準偏差
    scale_slope : スケール依存バイアスの傾き
    scale_noise : スケール依存ノイズの傾き
    """
    rng = np.random.default_rng(seed)
    true_values = rng.uniform(10, 100, n)
    true_values.sort()

    noise_a = rng.normal(0, 1.0, n)
    noise_b = rng.normal(0, 1.0, n)

    a = true_values + noise_a
    b = (
        true_values
        + bias
        + rng.normal(0, random_sd, n)
        + scale_slope * (true_values - true_values.mean())
        + scale_noise * true_values * rng.normal(0, 0.02, n)
        + noise_b
    )

    return {
        "name": name,
        "a": a,
        "b": b,
        "true_values": true_values,
        "n": n,
    }


SCENARIOS = [
    generate_scenario(
        "理想的一致 (Perfect)",
        bias=0.0,
        random_sd=0.5,
        seed=1,
    ),
    generate_scenario(
        "系統誤差 (Systematic Bias)",
        bias=8.0,
        random_sd=0.5,
        seed=2,
    ),
    generate_scenario(
        "ランダム誤差 (Random Error)",
        bias=0.0,
        random_sd=8.0,
        seed=3,
    ),
    generate_scenario(
        "スケール依存 (Scale-Dependent)",
        bias=0.0,
        random_sd=1.0,
        scale_slope=0.15,
        scale_noise=0.5,
        seed=4,
    ),
    generate_scenario(
        "複合誤差 (Mixed Errors)",
        bias=4.0,
        random_sd=5.0,
        scale_slope=0.08,
        seed=5,
    ),
]


# =============================================================================
# 2. BA 統計量の計算
# =============================================================================

def compute_ba_stats(a: np.ndarray, b: np.ndarray) -> dict:
    """BA プロット関連の統計量を計算する。"""
    d = a - b
    s = (a + b) / 2.0
    bias = float(np.mean(d))
    sd = float(np.std(d, ddof=1))
    loa_upper = bias + 1.96 * sd
    loa_lower = bias - 1.96 * sd
    return {
        "d": d,
        "s": s,
        "bias": bias,
        "sd": sd,
        "loa_upper": loa_upper,
        "loa_lower": loa_lower,
    }


# =============================================================================
# 3. 球面回転体の構築
# =============================================================================

def build_sphere_body(
    a: np.ndarray,
    b: np.ndarray,
    n_azimuth: int = 80,
    n_interp: int = 200,
) -> dict:
    """データペアから球面回転体を構築する。

    Returns
    -------
    dict with keys:
        X, Y, Z : 回転体表面メッシュ (n_interp x n_azimuth)
        X_sphere, Y_sphere, Z_sphere : 参照球メッシュ
        vor : Volume Occupancy Ratio
        r_profile : 各緯度の半径プロファイル
        phi_profile : 各緯度の極角
        r_data : 各データ点の半径
        phi_data : 各データ点の極角
        volume_solid : 回転体の体積
        volume_sphere : 参照球の体積
        sphericity : 球面度
        legendre_coeffs : ルジャンドル展開係数
    """
    n = len(a)
    sort_idx = np.argsort((a + b) / 2.0)
    a_sorted = a[sort_idx]
    b_sorted = b[sort_idx]

    # 極角: (0, π) に等間隔配置
    phi_data = np.linspace(0.01, np.pi - 0.01, n)

    # 半径の計算: 比率ベース r = min/max
    r_data = np.minimum(a_sorted, b_sorted) / np.maximum(a_sorted, b_sorted)
    r_data = np.clip(r_data, 0.01, 1.0)

    # 両極を追加してスプライン補間
    phi_ext = np.concatenate([[0.0], phi_data, [np.pi]])
    r_ext = np.concatenate([[r_data[0]], r_data, [r_data[-1]]])

    cs = CubicSpline(phi_ext, r_ext, bc_type="clamped")
    phi_fine = np.linspace(0, np.pi, n_interp)
    r_fine = np.clip(cs(phi_fine), 0.01, 1.0)

    # 方位角
    theta = np.linspace(0, 2 * np.pi, n_azimuth)

    # 回転体メッシュ
    PHI, THETA = np.meshgrid(phi_fine, theta, indexing="ij")
    R_mesh = np.outer(r_fine, np.ones(n_azimuth))

    X = R_mesh * np.sin(PHI) * np.cos(THETA)
    Y = R_mesh * np.sin(PHI) * np.sin(THETA)
    Z = R_mesh * np.cos(PHI)

    # 参照球メッシュ (R=1)
    X_sphere = np.sin(PHI) * np.cos(THETA)
    Y_sphere = np.sin(PHI) * np.sin(THETA)
    Z_sphere = np.cos(PHI)

    # 体積計算 (数値積分)
    # V = (2π/3) ∫₀^π r(φ)³ sin(φ) dφ
    integrand = r_fine ** 3 * np.sin(phi_fine)
    volume_solid = float((2 * np.pi / 3) * np.trapezoid(integrand, phi_fine))
    volume_sphere = 4 * np.pi / 3  # R=1

    vor = volume_solid / volume_sphere

    # 球面度
    # 表面積の近似計算
    dphi = phi_fine[1] - phi_fine[0]
    dtheta = theta[1] - theta[0]
    surface_area = 0.0
    for i in range(len(phi_fine) - 1):
        r_avg = (r_fine[i] + r_fine[i + 1]) / 2
        sin_avg = (np.sin(phi_fine[i]) + np.sin(phi_fine[i + 1])) / 2
        surface_area += 2 * np.pi * r_avg * sin_avg * dphi
    surface_area = max(surface_area, 1e-10)
    sphericity = float(
        (np.pi ** (1 / 3) * (6 * volume_solid) ** (2 / 3)) / surface_area
    )

    # ルジャンドル多項式展開 (軸対称: m=0)
    max_l = 6
    legendre_coeffs = []
    for l_val in range(max_l + 1):
        p_l = legendre(l_val)
        cos_phi = np.cos(phi_fine)
        integrand_l = r_fine * p_l(cos_phi) * np.sin(phi_fine)
        c_l = float(
            (2 * l_val + 1) / 2 * np.trapezoid(integrand_l, phi_fine)
        )
        legendre_coeffs.append(c_l)

    return {
        "X": X,
        "Y": Y,
        "Z": Z,
        "X_sphere": X_sphere,
        "Y_sphere": Y_sphere,
        "Z_sphere": Z_sphere,
        "vor": vor,
        "r_profile": r_fine,
        "phi_profile": phi_fine,
        "r_data": r_data,
        "phi_data": phi_data,
        "volume_solid": volume_solid,
        "volume_sphere": volume_sphere,
        "sphericity": sphericity,
        "legendre_coeffs": legendre_coeffs,
    }


# =============================================================================
# 4. 円周統計量
# =============================================================================

def compute_circular_stats(a: np.ndarray, b: np.ndarray) -> dict:
    """偏差角を計算し、円周統計量を返す。"""
    theta = np.arctan2(a - b, a + b)

    C = float(np.mean(np.cos(theta)))
    S = float(np.mean(np.sin(theta)))
    R_bar = float(np.sqrt(C ** 2 + S ** 2))
    mu_hat = float(np.arctan2(S, C))

    V = 1 - R_bar  # circular variance
    if R_bar > 0 and R_bar < 1:
        v = float(np.sqrt(-2 * np.log(R_bar)))
    else:
        v = 0.0

    # Rayleigh test
    n = len(theta)
    Z = n * R_bar ** 2
    p_rayleigh = float(np.exp(-Z) * (1 + (2 * Z - Z ** 2) / (4 * n)))
    p_rayleigh = max(0.0, min(1.0, p_rayleigh))

    return {
        "theta": theta,
        "R_bar": R_bar,
        "mu_hat": mu_hat,
        "V": V,
        "v": v,
        "Z_rayleigh": float(Z),
        "p_rayleigh": p_rayleigh,
    }


# =============================================================================
# 5. 誤差コンパス角
# =============================================================================

def compute_error_compass(ba: dict) -> dict:
    """系統誤差とランダム誤差の角度表現。"""
    bias_abs = abs(ba["bias"])
    sd = ba["sd"]
    E = float(np.sqrt(bias_abs ** 2 + sd ** 2))
    if E < 1e-12:
        phi = 0.0
    else:
        phi = float(np.arctan2(sd, bias_abs))
    return {
        "E": E,
        "phi_deg": float(np.degrees(phi)),
        "systematic_ratio": float(np.cos(phi)),
        "random_ratio": float(np.sin(phi)),
    }


# =============================================================================
# 6. ダッシュボード生成
# =============================================================================

def create_dashboard(scenarios: list[dict]) -> go.Figure:
    """全シナリオを含むインタラクティブダッシュボードを生成する。"""

    # 各シナリオのデータを事前計算
    all_data = []
    for sc in scenarios:
        ba = compute_ba_stats(sc["a"], sc["b"])
        sphere = build_sphere_body(sc["a"], sc["b"])
        circ = compute_circular_stats(sc["a"], sc["b"])
        compass = compute_error_compass(ba)
        all_data.append({
            "scenario": sc,
            "ba": ba,
            "sphere": sphere,
            "circ": circ,
            "compass": compass,
        })

    # 初期表示シナリオ
    init_idx = 0

    fig = make_subplots(
        rows=2,
        cols=3,
        specs=[
            [
                {"type": "surface", "colspan": 2, "rowspan": 2},
                None,
                {"type": "xy"},
            ],
            [
                None,
                None,
                {"type": "polar"},
            ],
        ],
        subplot_titles=[
            "3D 球面回転体 (くるくる回してください)",
            "Bland-Altman プロット",
            "円周密度 (偏差角分布)",
        ],
        horizontal_spacing=0.08,
        vertical_spacing=0.12,
        column_widths=[0.4, 0.2, 0.4],
        row_heights=[0.55, 0.45],
    )

    # 全シナリオのトレースを追加（非表示で）
    traces_per_scenario = 7  # 各シナリオのトレース数
    for sc_idx, data in enumerate(all_data):
        visible = sc_idx == init_idx
        sp = data["sphere"]
        ba = data["ba"]
        circ = data["circ"]
        sc = data["scenario"]

        # --- トレース 1: 参照球 (半透明) ---
        fig.add_trace(
            go.Surface(
                x=sp["X_sphere"],
                y=sp["Y_sphere"],
                z=sp["Z_sphere"],
                opacity=0.08,
                colorscale=[[0, "rgb(200,200,200)"], [1, "rgb(200,200,200)"]],
                showscale=False,
                name="参照球",
                visible=visible,
                hoverinfo="skip",
            ),
            row=1,
            col=1,
        )

        # --- トレース 2: 回転体 (色付き) ---
        r_mesh = np.sqrt(sp["X"] ** 2 + sp["Y"] ** 2 + sp["Z"] ** 2)
        fig.add_trace(
            go.Surface(
                x=sp["X"],
                y=sp["Y"],
                z=sp["Z"],
                surfacecolor=r_mesh,
                colorscale="RdYlGn",
                cmin=0.3,
                cmax=1.0,
                opacity=0.85,
                showscale=True,
                colorbar=dict(
                    title=dict(text="一致度 r", font=dict(size=11)),
                    len=0.4,
                    x=0.42,
                    y=0.5,
                    tickfont=dict(size=10),
                ),
                name="回転体",
                visible=visible,
                hovertemplate=(
                    "x: %{x:.2f}<br>y: %{y:.2f}<br>z: %{z:.2f}"
                    "<br>一致度: %{surfacecolor:.3f}<extra></extra>"
                ),
            ),
            row=1,
            col=1,
        )

        # --- トレース 3: 軸 (南北極線) ---
        fig.add_trace(
            go.Scatter3d(
                x=[0, 0],
                y=[0, 0],
                z=[-1.1, 1.1],
                mode="lines+text",
                line=dict(color="gray", width=3, dash="dash"),
                text=["南極 (小スケール)", "北極 (大スケール)"],
                textposition=["bottom center", "top center"],
                textfont=dict(size=9),
                showlegend=False,
                visible=visible,
                hoverinfo="skip",
            ),
            row=1,
            col=1,
        )

        # --- トレース 4: データ点を球面上に表示 ---
        phi_d = sp["phi_data"]
        r_d = sp["r_data"]
        xd = r_d * np.sin(phi_d)
        yd = np.zeros_like(r_d)
        zd = r_d * np.cos(phi_d)
        fig.add_trace(
            go.Scatter3d(
                x=xd,
                y=yd,
                z=zd,
                mode="markers",
                marker=dict(
                    size=4,
                    color=r_d,
                    colorscale="RdYlGn",
                    cmin=0.3,
                    cmax=1.0,
                    showscale=False,
                ),
                name="データ点",
                visible=visible,
                hovertemplate="r=%{marker.color:.3f}<extra></extra>",
            ),
            row=1,
            col=1,
        )

        # --- トレース 5: BA プロット ---
        fig.add_trace(
            go.Scatter(
                x=ba["s"],
                y=ba["d"],
                mode="markers",
                marker=dict(
                    size=7,
                    color=np.abs(ba["d"]),
                    colorscale="Reds",
                    opacity=0.7,
                    showscale=False,
                ),
                name="データ",
                visible=visible,
                hovertemplate=(
                    "平均: %{x:.1f}<br>差: %{y:.2f}<extra></extra>"
                ),
            ),
            row=1,
            col=3,
        )

        # --- トレース 6: BA プロット LoA ライン ---
        s_range = [float(np.min(ba["s"])) - 2, float(np.max(ba["s"])) + 2]
        fig.add_trace(
            go.Scatter(
                x=s_range * 3,
                y=(
                    [ba["bias"], ba["bias"]]
                    + [ba["loa_upper"], ba["loa_upper"]]
                    + [ba["loa_lower"], ba["loa_lower"]]
                ),
                mode="lines",
                line=dict(color="rgba(0,0,0,0)"),
                showlegend=False,
                visible=visible,
                hoverinfo="skip",
            ),
            row=1,
            col=3,
        )

        # --- トレース 7: 円周密度プロット ---
        theta_deg = np.degrees(circ["theta"])
        hist_vals, bin_edges = np.histogram(theta_deg, bins=36, range=(-45, 45))
        bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
        fig.add_trace(
            go.Barpolar(
                r=hist_vals,
                theta=bin_centers,
                width=2.5,
                marker=dict(
                    color=hist_vals,
                    colorscale="Viridis",
                    showscale=False,
                ),
                name="偏差角分布",
                visible=visible,
                hovertemplate="角度: %{theta:.1f}°<br>頻度: %{r}<extra></extra>",
            ),
            row=2,
            col=3,
        )

    # BA プロットにバイアスと LoA の shape を追加（初期シナリオのみ、updateで切替）
    init_ba = all_data[init_idx]["ba"]
    s_min = float(np.min(init_ba["s"])) - 2
    s_max = float(np.max(init_ba["s"])) + 2

    fig.add_shape(
        type="line",
        x0=s_min, x1=s_max,
        y0=init_ba["bias"], y1=init_ba["bias"],
        line=dict(color="blue", width=2),
        row=1, col=3,
    )
    fig.add_shape(
        type="line",
        x0=s_min, x1=s_max,
        y0=init_ba["loa_upper"], y1=init_ba["loa_upper"],
        line=dict(color="red", width=1.5, dash="dash"),
        row=1, col=3,
    )
    fig.add_shape(
        type="line",
        x0=s_min, x1=s_max,
        y0=init_ba["loa_lower"], y1=init_ba["loa_lower"],
        line=dict(color="red", width=1.5, dash="dash"),
        row=1, col=3,
    )

    # ドロップダウンメニュー
    buttons = []
    for sc_idx, data in enumerate(all_data):
        sp = data["sphere"]
        ba = data["ba"]
        compass = data["compass"]
        circ = data["circ"]
        sc = data["scenario"]

        visibility = [False] * (len(scenarios) * traces_per_scenario)
        for t in range(traces_per_scenario):
            visibility[sc_idx * traces_per_scenario + t] = True

        s_min_sc = float(np.min(ba["s"])) - 2
        s_max_sc = float(np.max(ba["s"])) + 2

        legendre_str = "  ".join(
            [f"a{i}={c:.3f}" for i, c in enumerate(sp["legendre_coeffs"][:4])]
        )

        label = (
            f'{sc["name"]}<br>'
            f'  VOR={sp["vor"]:.3f}  '
            f'球面度={sp["sphericity"]:.3f}  '
            f'Bias={ba["bias"]:.2f}  '
            f'SD={ba["sd"]:.2f}<br>'
            f'  誤差角φ={compass["phi_deg"]:.1f}°  '
            f'(系統{compass["systematic_ratio"]:.0%} / '
            f'ランダム{compass["random_ratio"]:.0%})  '
            f'R̄={circ["R_bar"]:.3f}<br>'
            f'  Legendre: {legendre_str}'
        )

        buttons.append(
            dict(
                label=sc["name"],
                method="update",
                args=[
                    {"visible": visibility},
                    {
                        "title.text": label,
                        "shapes": [
                            dict(
                                type="line",
                                xref="x2", yref="y2",
                                x0=s_min_sc, x1=s_max_sc,
                                y0=ba["bias"], y1=ba["bias"],
                                line=dict(color="blue", width=2),
                            ),
                            dict(
                                type="line",
                                xref="x2", yref="y2",
                                x0=s_min_sc, x1=s_max_sc,
                                y0=ba["loa_upper"], y1=ba["loa_upper"],
                                line=dict(color="red", width=1.5, dash="dash"),
                            ),
                            dict(
                                type="line",
                                xref="x2", yref="y2",
                                x0=s_min_sc, x1=s_max_sc,
                                y0=ba["loa_lower"], y1=ba["loa_lower"],
                                line=dict(color="red", width=1.5, dash="dash"),
                            ),
                        ],
                    },
                ],
            )
        )

    # 初期タイトル
    init_sp = all_data[init_idx]["sphere"]
    init_compass = all_data[init_idx]["compass"]
    init_circ = all_data[init_idx]["circ"]
    init_sc = scenarios[init_idx]
    init_legendre = "  ".join(
        [f"a{i}={c:.3f}" for i, c in enumerate(init_sp["legendre_coeffs"][:4])]
    )
    init_title = (
        f'{init_sc["name"]}<br>'
        f'  VOR={init_sp["vor"]:.3f}  '
        f'球面度={init_sp["sphericity"]:.3f}  '
        f'Bias={init_ba["bias"]:.2f}  '
        f'SD={init_ba["sd"]:.2f}<br>'
        f'  誤差角φ={init_compass["phi_deg"]:.1f}°  '
        f'(系統{init_compass["systematic_ratio"]:.0%} / '
        f'ランダム{init_compass["random_ratio"]:.0%})  '
        f'R̄={init_circ["R_bar"]:.3f}<br>'
        f'  Legendre: {init_legendre}'
    )

    fig.update_layout(
        title=dict(
            text=init_title,
            font=dict(size=13),
            x=0.01,
            xanchor="left",
        ),
        updatemenus=[
            dict(
                type="dropdown",
                direction="down",
                x=0.0,
                xanchor="left",
                y=1.18,
                yanchor="top",
                buttons=buttons,
                font=dict(size=12),
                bgcolor="white",
                bordercolor="#888",
            ),
        ],
        height=820,
        width=1400,
        template="plotly_white",
        margin=dict(l=30, r=30, t=160, b=30),
    )

    # 3D シーンの設定
    fig.update_scenes(
        dict(
            xaxis=dict(range=[-1.2, 1.2], title="", showticklabels=False),
            yaxis=dict(range=[-1.2, 1.2], title="", showticklabels=False),
            zaxis=dict(range=[-1.2, 1.2], title="", showticklabels=False),
            aspectmode="cube",
            camera=dict(
                eye=dict(x=1.5, y=1.5, z=0.8),
                up=dict(x=0, y=0, z=1),
            ),
        ),
        row=1,
        col=1,
    )

    # BA プロット軸
    fig.update_xaxes(title_text="平均 (a+b)/2", row=1, col=3)
    fig.update_yaxes(title_text="差 a−b", row=1, col=3)

    # 極座標軸
    fig.update_polars(
        radialaxis=dict(showticklabels=True, tickfont=dict(size=9)),
        angularaxis=dict(
            tickmode="array",
            tickvals=[-45, -30, -15, 0, 15, 30, 45],
            ticktext=["-45°", "-30°", "-15°", "0°(一致)", "15°", "30°", "45°"],
            tickfont=dict(size=9),
            direction="clockwise",
            rotation=90,
        ),
    )

    return fig


# =============================================================================
# 7. 比較サマリーテーブル (別図)
# =============================================================================

def create_comparison_table(scenarios: list[dict]) -> go.Figure:
    """全シナリオの指標比較テーブルを生成する。"""
    rows = []
    for sc in scenarios:
        ba = compute_ba_stats(sc["a"], sc["b"])
        sp = build_sphere_body(sc["a"], sc["b"])
        circ = compute_circular_stats(sc["a"], sc["b"])
        compass = compute_error_compass(ba)
        rows.append({
            "シナリオ": sc["name"],
            "VOR": f'{sp["vor"]:.4f}',
            "球面度 Ψ": f'{sp["sphericity"]:.4f}',
            "Bias": f'{ba["bias"]:.2f}',
            "SD": f'{ba["sd"]:.2f}',
            "誤差角 φ": f'{compass["phi_deg"]:.1f}°',
            "系統:ランダム": (
                f'{compass["systematic_ratio"]:.0%}:'
                f'{compass["random_ratio"]:.0%}'
            ),
            "R̄ (集中度)": f'{circ["R_bar"]:.4f}',
            "Rayleigh p": f'{circ["p_rayleigh"]:.4f}',
            "a₀": f'{sp["legendre_coeffs"][0]:.3f}',
            "a₁": f'{sp["legendre_coeffs"][1]:.3f}',
            "a₂": f'{sp["legendre_coeffs"][2]:.3f}',
        })

    headers = list(rows[0].keys())
    cells = [[r[h] for r in rows] for h in headers]

    fig = go.Figure(
        data=[
            go.Table(
                header=dict(
                    values=headers,
                    fill_color="#2c3e50",
                    font=dict(color="white", size=12),
                    align="center",
                ),
                cells=dict(
                    values=cells,
                    fill_color=[
                        [
                            "#ecf0f1" if i % 2 == 0 else "white"
                            for i in range(len(rows))
                        ]
                    ]
                    * len(headers),
                    font=dict(size=11),
                    align="center",
                    height=28,
                ),
            )
        ]
    )
    fig.update_layout(
        title=dict(
            text="シナリオ比較テーブル — BA 球面回転体指標",
            font=dict(size=16),
        ),
        height=280,
        width=1400,
        margin=dict(l=10, r=10, t=50, b=10),
    )
    return fig


# =============================================================================
# 8. 半径プロファイル比較図
# =============================================================================

def create_profile_comparison(scenarios: list[dict]) -> go.Figure:
    """全シナリオの半径プロファイルを重ね描きする。"""
    fig = go.Figure()

    colors = [
        "#2ecc71",  # green - perfect
        "#3498db",  # blue - systematic
        "#e74c3c",  # red - random
        "#f39c12",  # orange - scale-dependent
        "#9b59b6",  # purple - mixed
    ]

    for sc_idx, sc in enumerate(scenarios):
        sp = build_sphere_body(sc["a"], sc["b"])
        phi_deg = np.degrees(sp["phi_profile"])
        fig.add_trace(
            go.Scatter(
                x=phi_deg,
                y=sp["r_profile"],
                mode="lines",
                name=sc["name"],
                line=dict(color=colors[sc_idx % len(colors)], width=2.5),
                hovertemplate="緯度: %{x:.1f}°<br>半径: %{y:.3f}<extra></extra>",
            )
        )

    # 理想線 r=1
    fig.add_hline(
        y=1.0,
        line=dict(color="gray", dash="dot", width=1),
        annotation_text="完全一致 (r=1)",
        annotation_position="top right",
    )

    fig.update_layout(
        title=dict(
            text="半径プロファイル比較 — 極角 φ に沿った一致度の変化",
            font=dict(size=14),
        ),
        xaxis=dict(
            title="極角 φ (°)  [0°=北極(大スケール) → 180°=南極(小スケール)]",
            range=[0, 180],
        ),
        yaxis=dict(title="半径 r (一致度)", range=[0, 1.1]),
        height=380,
        width=1400,
        template="plotly_white",
        margin=dict(l=60, r=30, t=60, b=60),
        legend=dict(x=0.01, y=0.01, bgcolor="rgba(255,255,255,0.8)"),
    )
    return fig


# =============================================================================
# 9. 誤差コンパス図
# =============================================================================

def create_error_compass(scenarios: list[dict]) -> go.Figure:
    """誤差コンパス: 各シナリオの誤差角を可視化。"""
    fig = go.Figure()

    colors = ["#2ecc71", "#3498db", "#e74c3c", "#f39c12", "#9b59b6"]

    for sc_idx, sc in enumerate(scenarios):
        ba = compute_ba_stats(sc["a"], sc["b"])
        compass = compute_error_compass(ba)

        # ベクトル: (系統誤差, ランダム誤差)
        bias_abs = abs(ba["bias"])
        sd = ba["sd"]

        fig.add_trace(
            go.Scatter(
                x=[0, bias_abs],
                y=[0, sd],
                mode="lines+markers+text",
                line=dict(color=colors[sc_idx % len(colors)], width=3),
                marker=dict(size=[6, 12], symbol=["circle", "diamond"]),
                text=["", sc["name"].split(" (")[0]],
                textposition="top right",
                textfont=dict(size=10),
                name=(
                    f'{sc["name"]} '
                    f'(φ={compass["phi_deg"]:.0f}°, E={compass["E"]:.1f})'
                ),
                hovertemplate=(
                    f'{sc["name"]}<br>'
                    f'系統誤差|Bias|: {bias_abs:.2f}<br>'
                    f'ランダム誤差 SD: {sd:.2f}<br>'
                    f'総合誤差 E: {compass["E"]:.2f}<br>'
                    f'誤差角 φ: {compass["phi_deg"]:.1f}°'
                    "<extra></extra>"
                ),
            )
        )

    # 45° ガイドライン
    max_val = max(
        max(abs(compute_ba_stats(sc["a"], sc["b"])["bias"]) for sc in scenarios),
        max(compute_ba_stats(sc["a"], sc["b"])["sd"] for sc in scenarios),
    ) * 1.2
    fig.add_trace(
        go.Scatter(
            x=[0, max_val],
            y=[0, max_val],
            mode="lines",
            line=dict(color="gray", dash="dot", width=1),
            showlegend=False,
            hoverinfo="skip",
        )
    )
    fig.add_annotation(
        x=max_val * 0.7,
        y=max_val * 0.75,
        text="φ=45° (等分)",
        showarrow=False,
        font=dict(size=10, color="gray"),
    )

    fig.update_layout(
        title=dict(
            text="誤差コンパス — 系統誤差 vs ランダム誤差の角度表現",
            font=dict(size=14),
        ),
        xaxis=dict(title="|系統誤差| (Bias の絶対値)", rangemode="tozero"),
        yaxis=dict(title="ランダム誤差 (SD)", rangemode="tozero"),
        height=450,
        width=700,
        template="plotly_white",
        margin=dict(l=60, r=30, t=60, b=60),
    )
    return fig


# =============================================================================
# 10. HTML ダッシュボード出力
# =============================================================================

def export_dashboard(output_path: str = "ba_sphere_dashboard.html") -> None:
    """全図をまとめた HTML ダッシュボードを出力する。"""
    dashboard = create_dashboard(SCENARIOS)
    table = create_comparison_table(SCENARIOS)
    profile = create_profile_comparison(SCENARIOS)
    compass = create_error_compass(SCENARIOS)

    html_parts = [
        "<!DOCTYPE html>",
        '<html lang="ja">',
        "<head>",
        '<meta charset="UTF-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">',
        "<title>BA Sphere Simulation — 球面回転体による測定一致度の可視化</title>",
        "<style>",
        "  body { font-family: 'Segoe UI', sans-serif; margin: 0; padding: 20px;"
        " background: #f8f9fa; }",
        "  h1 { color: #2c3e50; margin-bottom: 5px; }",
        "  .subtitle { color: #7f8c8d; margin-bottom: 20px; font-size: 14px; }",
        "  .section { background: white; border-radius: 8px;"
        " box-shadow: 0 2px 4px rgba(0,0,0,0.1); padding: 15px;"
        " margin-bottom: 20px; }",
        "  .section h2 { color: #34495e; font-size: 16px;"
        " margin-top: 0; border-bottom: 2px solid #3498db;"
        " padding-bottom: 5px; }",
        "  .grid-2 { display: grid;"
        " grid-template-columns: 1fr 1fr; gap: 20px; }",
        "  .legend-box { background: #ecf0f1; border-radius: 6px;"
        " padding: 12px; margin-top: 10px; font-size: 13px; }",
        "  .legend-box h3 { margin: 0 0 8px; font-size: 14px; color: #2c3e50; }",
        "  .legend-box ul { margin: 0; padding-left: 18px; }",
        "  .legend-box li { margin-bottom: 4px; }",
        "  @media (max-width: 900px) {"
        " .grid-2 { grid-template-columns: 1fr; } }",
        "</style>",
        "</head>",
        "<body>",
        '<h1>BA Sphere Simulation</h1>',
        '<p class="subtitle">'
        "Bland-Altman プロットの幾何学的拡張 — "
        "球面回転体 (Volume Occupancy Ratio) による測定一致度の可視化"
        "</p>",
        "",
        '<div class="section">',
        "<h2>1. メインダッシュボード — ドロップダウンでシナリオを切り替え</h2>",
        dashboard.to_html(full_html=False, include_plotlyjs="cdn"),
        '<div class="legend-box">',
        "<h3>読み方ガイド</h3>",
        "<ul>",
        "<li><b>3D球面回転体 (左)</b>: "
        "緑=一致良好、赤=不一致。マウスドラッグで回転、ホイールでズーム。"
        "球が潰れるほど品質にムラがある</li>",
        "<li><b>BAプロット (右上)</b>: "
        "青線=バイアス、赤破線=一致限界 (±1.96SD)</li>",
        "<li><b>円周密度 (右下)</b>: "
        "0°が完全一致方向。分布が0°に集中するほど一致度が高い</li>",
        "<li><b>VOR</b>: 体積占有率 (0〜1)。"
        "1に近いほど全体的な一致度が高い</li>",
        "<li><b>誤差角φ</b>: 0°=純粋な系統誤差、90°=純粋なランダム誤差</li>",
        "<li><b>Legendre a₀</b>: 全体的な一致度、"
        "<b>a₁</b>: スケール依存性（南北非対称）、"
        "<b>a₂</b>: 中間値付近のパターン</li>",
        "</ul>",
        "</div>",
        "</div>",
        "",
        '<div class="section">',
        "<h2>2. シナリオ比較</h2>",
        table.to_html(full_html=False, include_plotlyjs=False),
        "</div>",
        "",
        '<div class="grid-2">',
        '<div class="section">',
        "<h2>3. 半径プロファイル比較</h2>",
        profile.to_html(full_html=False, include_plotlyjs=False),
        "</div>",
        '<div class="section">',
        "<h2>4. 誤差コンパス</h2>",
        compass.to_html(full_html=False, include_plotlyjs=False),
        "</div>",
        "</div>",
        "",
        '<div class="section">',
        "<h2>5. 品質管理での活用例</h2>",
        '<div class="legend-box">',
        "<ul>",
        "<li><b>測定器校正</b>: VOR を定期モニタリングし、"
        "閾値 (例: VOR &lt; 0.95) を下回ったら再校正トリガー</li>",
        "<li><b>受入検査</b>: ロット内サンプルの VOR が規格値以上なら合格判定</li>",
        "<li><b>スケール依存不良の検出</b>: "
        "Legendre a₁ が大きい → 大きい/小さい部品で精度が異なる</li>",
        "<li><b>工程改善の追跡</b>: 改善前後の球面回転体を並べて比較し、"
        "どの領域で改善されたかを直感的に把握</li>",
        "</ul>",
        "</div>",
        "</div>",
        "",
        "</body>",
        "</html>",
    ]

    html_content = "\n".join(html_parts)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"Dashboard exported to: {output_path}")


# =============================================================================
# メイン
# =============================================================================

if __name__ == "__main__":
    export_dashboard("ba_sphere_dashboard.html")
