"""
Bland-Altman Sphere Simulation — Meridian Version
==================================================

BAプロットの幾何学的拡張: 経度分散配置型3D表面による測定一致度の可視化

各データペア (a, b) を球の経度方向に均等分散配置し（n個なら360°/n間隔）、
一致度に応じた半径の凹凸をガウシアンカーネルで局在化。
回転体（軸対称）版と異なり、回転時に個々のデータ点の品質ムラが
凹凸として直感的に把握できる。上下からの視点で全体パターンを確認可能。
物理デバイスでの常時回転表示を想定した設計。

生成物:
- ba_sphere_dashboard.html: インタラクティブ3Dダッシュボード（自動回転対応）
"""

import numpy as np
from scipy.interpolate import CubicSpline
from scipy.special import legendre
import plotly.graph_objects as go


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
    """測定ペアデータを生成する。"""
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
    generate_scenario("理想的一致 (Perfect)", bias=0.0, random_sd=0.5, seed=1),
    generate_scenario("系統誤差 (Systematic Bias)", bias=8.0, random_sd=0.5, seed=2),
    generate_scenario("ランダム誤差 (Random Error)", bias=0.0, random_sd=8.0, seed=3),
    generate_scenario("スケール依存 (Scale-Dependent)", bias=0.0, random_sd=1.0,
                      scale_slope=0.15, scale_noise=0.5, seed=4),
    generate_scenario("複合誤差 (Mixed Errors)", bias=4.0, random_sd=5.0,
                      scale_slope=0.08, seed=5),
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
    return {"d": d, "s": s, "bias": bias, "sd": sd,
            "loa_upper": loa_upper, "loa_lower": loa_lower}


# =============================================================================
# 3. 経度分散配置型3D表面の構築
# =============================================================================

def build_meridian_body(
    a: np.ndarray,
    b: np.ndarray,
    n_azimuth: int = 360,
    n_interp: int = 200,
    spread_sigma: float = np.pi / 8,
) -> dict:
    """データペアから経度分散配置型の3D表面を構築する。

    各データ点を経度方向に均等分散配置し（n個なら360°/n間隔）、
    各データ点の一致度に応じた半径の凹凸をガウシアンカーネルで局在化。
    回転すれば個々のデータ品質が凹凸として見え、
    極地から見れば全体データのパターンが一目で把握できる。

    Parameters
    ----------
    a, b : 測定値ペア
    n_azimuth : 方位角の分割数（メッシュ解像度）
    n_interp : 極角の補間点数
    spread_sigma : ガウシアンカーネルの幅（ラジアン）
    """
    n = len(a)
    sort_idx = np.argsort((a + b) / 2.0)
    a_sorted = a[sort_idx]
    b_sorted = b[sort_idx]

    # 極角: 平均値順に南極→北極
    phi_data = np.linspace(0.01, np.pi - 0.01, n)
    # 経度: 均等分散配置 (360°/n 間隔)
    theta_data = np.linspace(0, 2 * np.pi, n, endpoint=False)
    # 一致度
    r_data = np.minimum(a_sorted, b_sorted) / np.maximum(a_sorted, b_sorted)
    r_data = np.clip(r_data, 0.01, 1.0)

    # 極角方向の補間プロファイル（ルジャンドル展開等に使用）
    phi_ext = np.concatenate([[0.0], phi_data, [np.pi]])
    r_ext = np.concatenate([[r_data[0]], r_data, [r_data[-1]]])
    cs = CubicSpline(phi_ext, r_ext, bc_type="clamped")
    phi_fine = np.linspace(0, np.pi, n_interp)
    r_fine = np.clip(cs(phi_fine), 0.01, 1.0)

    theta = np.linspace(0, 2 * np.pi, n_azimuth)

    # メッシュ構築: 各データ点のカーネルを重畳
    PHI, THETA = np.meshgrid(phi_fine, theta, indexing="ij")
    R_mesh = np.ones_like(PHI)  # 基準球 r=1

    for i in range(n):
        # 極角方向のカーネル
        d_phi = PHI - phi_data[i]
        w_phi = np.exp(-d_phi**2 / (2 * spread_sigma**2))
        # 経度方向のカーネル
        d_theta = np.abs(THETA - theta_data[i])
        d_theta = np.minimum(d_theta, 2 * np.pi - d_theta)
        w_theta = np.exp(-d_theta**2 / (2 * spread_sigma**2))
        # 2Dガウシアンカーネル
        w = w_phi * w_theta
        R_mesh = R_mesh + (r_data[i] - 1.0) * w

    R_mesh = np.clip(R_mesh, 0.01, 2.0)

    X = R_mesh * np.sin(PHI) * np.cos(THETA)
    Y = R_mesh * np.sin(PHI) * np.sin(THETA)
    Z = R_mesh * np.cos(PHI)

    X_sphere = np.sin(PHI) * np.cos(THETA)
    Y_sphere = np.sin(PHI) * np.sin(THETA)
    Z_sphere = np.cos(PHI)

    # 体積計算 (2D 数値積分)
    inner = np.trapezoid(R_mesh**3, theta, axis=1)
    volume_solid = float(
        (1.0 / 3.0) * np.trapezoid(inner * np.sin(phi_fine), phi_fine)
    )
    volume_sphere = 4 * np.pi / 3
    vor = volume_solid / volume_sphere

    # 表面積 & 球面度
    sa_integrand = R_mesh**2 * np.sin(PHI)
    surface_area = float(
        np.trapezoid(np.trapezoid(sa_integrand, theta, axis=1), phi_fine)
    )
    surface_area = max(surface_area, 1e-10)
    sphericity = float(
        (np.pi ** (1 / 3) * (6 * volume_solid) ** (2 / 3)) / surface_area
    )

    # ルジャンドル多項式展開 (極角方向プロファイル)
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
        "X": X, "Y": Y, "Z": Z,
        "X_sphere": X_sphere, "Y_sphere": Y_sphere, "Z_sphere": Z_sphere,
        "vor": vor, "r_profile": r_fine, "phi_profile": phi_fine,
        "r_data": r_data, "phi_data": phi_data, "theta_data": theta_data,
        "volume_solid": volume_solid, "volume_sphere": volume_sphere,
        "sphericity": sphericity, "legendre_coeffs": legendre_coeffs,
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
    V = 1 - R_bar
    if R_bar > 0 and R_bar < 1:
        v = float(np.sqrt(-2 * np.log(R_bar)))
    else:
        v = 0.0
    n = len(theta)
    Z = n * R_bar ** 2
    p_rayleigh = float(np.exp(-Z) * (1 + (2 * Z - Z ** 2) / (4 * n)))
    p_rayleigh = max(0.0, min(1.0, p_rayleigh))
    return {"theta": theta, "R_bar": R_bar, "mu_hat": mu_hat,
            "V": V, "v": v, "Z_rayleigh": float(Z), "p_rayleigh": p_rayleigh}


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
    return {"E": E, "phi_deg": float(np.degrees(phi)),
            "systematic_ratio": float(np.cos(phi)),
            "random_ratio": float(np.sin(phi))}


# =============================================================================
# 6. ダッシュボード生成 (経線配置版)
# =============================================================================

def _precompute_all(scenarios: list[dict]) -> list[dict]:
    """全シナリオのデータを事前計算する。"""
    all_data = []
    for sc in scenarios:
        ba = compute_ba_stats(sc["a"], sc["b"])
        sphere = build_meridian_body(sc["a"], sc["b"])
        circ = compute_circular_stats(sc["a"], sc["b"])
        compass = compute_error_compass(ba)
        all_data.append({"scenario": sc, "ba": ba, "sphere": sphere,
                         "circ": circ, "compass": compass})
    return all_data


def _make_title(sc, sp, ba, compass, circ):
    """シナリオのタイトル文字列を生成。"""
    leg = "  ".join(f"a{i}={c:.3f}" for i, c in enumerate(sp["legendre_coeffs"][:4]))
    return (
        f'{sc["name"]}<br>'
        f'VOR={sp["vor"]:.3f}  球面度={sp["sphericity"]:.3f}  '
        f'Bias={ba["bias"]:.2f}  SD={ba["sd"]:.2f}<br>'
        f'誤差角\u03c6={compass["phi_deg"]:.1f}\u00b0  '
        f'(系統{compass["systematic_ratio"]:.0%} / '
        f'ランダム{compass["random_ratio"]:.0%})  '
        f'R\u0304={circ["R_bar"]:.3f}<br>'
        f'Legendre: {leg}'
    )


def create_sphere_chart(all_data: list[dict]) -> go.Figure:
    """3D経線配置型表面チャート（ドロップダウン付き）。"""
    fig = go.Figure()
    init_idx = 0
    traces_per = 5

    for sc_idx, data in enumerate(all_data):
        visible = sc_idx == init_idx
        sp = data["sphere"]

        fig.add_trace(go.Surface(
            x=sp["X_sphere"], y=sp["Y_sphere"], z=sp["Z_sphere"],
            opacity=0.08,
            colorscale=[[0, "rgb(200,200,200)"], [1, "rgb(200,200,200)"]],
            showscale=False, name="参照球", visible=visible, hoverinfo="skip"))

        r_mesh = np.sqrt(sp["X"]**2 + sp["Y"]**2 + sp["Z"]**2)
        fig.add_trace(go.Surface(
            x=sp["X"], y=sp["Y"], z=sp["Z"],
            surfacecolor=r_mesh, colorscale="RdYlGn", cmin=0.3, cmax=1.0,
            opacity=0.85, showscale=True,
            colorbar=dict(title=dict(text="一致度 r", font=dict(size=11)),
                          len=0.5, x=1.0, y=0.5, tickfont=dict(size=10)),
            name="経線体", visible=visible,
            hovertemplate="x: %{x:.2f}<br>y: %{y:.2f}<br>z: %{z:.2f}<br>一致度: %{surfacecolor:.3f}<extra></extra>"))

        fig.add_trace(go.Scatter3d(
            x=[0, 0], y=[0, 0], z=[-1.1, 1.1],
            mode="lines+text", line=dict(color="gray", width=3, dash="dash"),
            text=["南極 (小)", "北極 (大)"],
            textposition=["bottom center", "top center"],
            textfont=dict(size=9), showlegend=False, visible=visible, hoverinfo="skip"))

        phi_d, r_d = sp["phi_data"], sp["r_data"]
        theta_d = sp["theta_data"]
        fig.add_trace(go.Scatter3d(
            x=r_d * np.sin(phi_d) * np.cos(theta_d),
            y=r_d * np.sin(phi_d) * np.sin(theta_d),
            z=r_d * np.cos(phi_d),
            mode="markers",
            marker=dict(size=5, color=r_d, colorscale="RdYlGn",
                        cmin=0.3, cmax=1.0, showscale=False,
                        line=dict(width=1, color="black")),
            name="データ点", visible=visible,
            hovertemplate="r=%{marker.color:.3f}<extra></extra>"))

        # 赤道リング（経度方向のデータ配置を示すガイドライン）
        guide_theta = np.linspace(0, 2 * np.pi, 100)
        fig.add_trace(go.Scatter3d(
            x=np.cos(guide_theta), y=np.sin(guide_theta),
            z=np.zeros(100),
            mode="lines", line=dict(color="#f1c40f", width=3, dash="dot"),
            name="赤道ガイド", visible=visible, hoverinfo="skip"))

    buttons = []
    for sc_idx, data in enumerate(all_data):
        vis = [False] * (len(all_data) * traces_per)
        for t in range(traces_per):
            vis[sc_idx * traces_per + t] = True
        label = _make_title(data["scenario"], data["sphere"],
                            data["ba"], data["compass"], data["circ"])
        buttons.append(dict(label=data["scenario"]["name"], method="update",
                            args=[{"visible": vis}, {"title.text": label}]))

    init = all_data[init_idx]
    init_title = _make_title(init["scenario"], init["sphere"],
                             init["ba"], init["compass"], init["circ"])

    fig.update_layout(
        title=dict(text=init_title, font=dict(size=12), x=0.01, xanchor="left"),
        updatemenus=[dict(type="dropdown", direction="down",
                          x=0.0, xanchor="left", y=1.22, yanchor="top",
                          buttons=buttons, font=dict(size=12),
                          bgcolor="white", bordercolor="#888")],
        height=520, autosize=True, template="plotly_white",
        margin=dict(l=10, r=10, t=150, b=10),
        scene=dict(
            xaxis=dict(range=[-1.2, 1.2], title="", showticklabels=False),
            yaxis=dict(range=[-1.2, 1.2], title="", showticklabels=False),
            zaxis=dict(range=[-1.2, 1.2], title="", showticklabels=False),
            aspectmode="cube",
            camera=dict(eye=dict(x=1.5, y=1.5, z=0.8), up=dict(x=0, y=0, z=1))))
    return fig


def create_ba_chart(all_data: list[dict]) -> go.Figure:
    """BA プロットチャート（ドロップダウン付き）。"""
    fig = go.Figure()
    init_idx = 0

    for sc_idx, data in enumerate(all_data):
        visible = sc_idx == init_idx
        ba = data["ba"]
        fig.add_trace(go.Scatter(
            x=ba["s"], y=ba["d"], mode="markers",
            marker=dict(size=8, color=np.abs(ba["d"]),
                        colorscale="Reds", opacity=0.7, showscale=False),
            name="データ", visible=visible,
            hovertemplate="平均: %{x:.1f}<br>差: %{y:.2f}<extra></extra>"))

    init_ba = all_data[init_idx]["ba"]
    s_min = float(np.min(init_ba["s"])) - 2
    s_max = float(np.max(init_ba["s"])) + 2
    for y_val, color, dash, width in [
        (init_ba["bias"], "blue", "solid", 2),
        (init_ba["loa_upper"], "red", "dash", 1.5),
        (init_ba["loa_lower"], "red", "dash", 1.5),
    ]:
        fig.add_shape(type="line", x0=s_min, x1=s_max, y0=y_val, y1=y_val,
                      line=dict(color=color, width=width, dash=dash))

    buttons = []
    for sc_idx, data in enumerate(all_data):
        ba = data["ba"]
        sc = data["scenario"]
        vis = [False] * len(all_data)
        vis[sc_idx] = True
        s_min_sc = float(np.min(ba["s"])) - 2
        s_max_sc = float(np.max(ba["s"])) + 2
        buttons.append(dict(
            label=sc["name"], method="update",
            args=[{"visible": vis},
                  {"shapes": [
                      dict(type="line", x0=s_min_sc, x1=s_max_sc,
                           y0=ba["bias"], y1=ba["bias"],
                           line=dict(color="blue", width=2)),
                      dict(type="line", x0=s_min_sc, x1=s_max_sc,
                           y0=ba["loa_upper"], y1=ba["loa_upper"],
                           line=dict(color="red", width=1.5, dash="dash")),
                      dict(type="line", x0=s_min_sc, x1=s_max_sc,
                           y0=ba["loa_lower"], y1=ba["loa_lower"],
                           line=dict(color="red", width=1.5, dash="dash")),
                  ]}]))

    fig.update_layout(
        title=dict(text="Bland-Altman プロット", font=dict(size=14)),
        updatemenus=[dict(type="dropdown", direction="down",
                          x=0.0, xanchor="left", y=1.20, yanchor="top",
                          buttons=buttons, font=dict(size=11),
                          bgcolor="white", bordercolor="#888")],
        xaxis=dict(title="平均 (a+b)/2"),
        yaxis=dict(title="差 a\u2212b"),
        height=380, autosize=True, template="plotly_white",
        margin=dict(l=50, r=20, t=80, b=50))
    return fig


def create_circular_chart(all_data: list[dict]) -> go.Figure:
    """円周密度プロット（ドロップダウン付き）。"""
    fig = go.Figure()
    init_idx = 0

    for sc_idx, data in enumerate(all_data):
        visible = sc_idx == init_idx
        circ = data["circ"]
        theta_deg = np.degrees(circ["theta"])
        hist_vals, bin_edges = np.histogram(theta_deg, bins=36, range=(-45, 45))
        bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
        fig.add_trace(go.Barpolar(
            r=hist_vals, theta=bin_centers, width=2.5,
            marker=dict(color=hist_vals, colorscale="Viridis", showscale=False),
            name="偏差角分布", visible=visible,
            hovertemplate="角度: %{theta:.1f}\u00b0<br>頻度: %{r}<extra></extra>"))

    buttons = []
    for sc_idx, data in enumerate(all_data):
        vis = [False] * len(all_data)
        vis[sc_idx] = True
        buttons.append(dict(label=data["scenario"]["name"], method="update",
                            args=[{"visible": vis}]))

    fig.update_layout(
        title=dict(text="円周密度 (偏差角分布)", font=dict(size=14)),
        updatemenus=[dict(type="dropdown", direction="down",
                          x=0.0, xanchor="left", y=1.15, yanchor="top",
                          buttons=buttons, font=dict(size=11),
                          bgcolor="white", bordercolor="#888")],
        polar=dict(
            radialaxis=dict(showticklabels=True, tickfont=dict(size=9)),
            angularaxis=dict(
                tickmode="array",
                tickvals=[-45, -30, -15, 0, 15, 30, 45],
                ticktext=["-45\u00b0", "-30\u00b0", "-15\u00b0",
                          "0\u00b0(一致)", "15\u00b0", "30\u00b0", "45\u00b0"],
                tickfont=dict(size=9), direction="clockwise", rotation=90)),
        height=380, autosize=True, template="plotly_white",
        margin=dict(l=30, r=30, t=80, b=30))
    return fig


# =============================================================================
# 7. 比較サマリーテーブル
# =============================================================================

def create_comparison_table(scenarios: list[dict]) -> go.Figure:
    """全シナリオの指標比較テーブル。"""
    rows = []
    for sc in scenarios:
        ba = compute_ba_stats(sc["a"], sc["b"])
        sp = build_meridian_body(sc["a"], sc["b"])
        circ = compute_circular_stats(sc["a"], sc["b"])
        compass = compute_error_compass(ba)
        rows.append({
            "シナリオ": sc["name"],
            "VOR": f'{sp["vor"]:.4f}',
            "球面度 \u03a8": f'{sp["sphericity"]:.4f}',
            "Bias": f'{ba["bias"]:.2f}',
            "SD": f'{ba["sd"]:.2f}',
            "誤差角 \u03c6": f'{compass["phi_deg"]:.1f}\u00b0',
            "系統:ランダム": f'{compass["systematic_ratio"]:.0%}:{compass["random_ratio"]:.0%}',
            "R\u0304 (集中度)": f'{circ["R_bar"]:.4f}',
            "Rayleigh p": f'{circ["p_rayleigh"]:.4f}',
            "a\u2080": f'{sp["legendre_coeffs"][0]:.3f}',
            "a\u2081": f'{sp["legendre_coeffs"][1]:.3f}',
            "a\u2082": f'{sp["legendre_coeffs"][2]:.3f}',
        })
    headers = list(rows[0].keys())
    cells = [[r[h] for r in rows] for h in headers]
    fig = go.Figure(data=[go.Table(
        header=dict(values=headers, fill_color="#2c3e50",
                    font=dict(color="white", size=12), align="center"),
        cells=dict(values=cells,
                   fill_color=[["#ecf0f1" if i % 2 == 0 else "white"
                                for i in range(len(rows))]] * len(headers),
                   font=dict(size=11), align="center", height=28))])
    fig.update_layout(
        title=dict(text="シナリオ比較テーブル \u2014 BA 経線配置型指標",
                   font=dict(size=16)),
        height=280, autosize=True, margin=dict(l=10, r=10, t=50, b=10))
    return fig


# =============================================================================
# 8. 半径プロファイル比較図
# =============================================================================

def create_profile_comparison(scenarios: list[dict]) -> go.Figure:
    """全シナリオの経線プロファイルを重ね描き。"""
    fig = go.Figure()
    colors = ["#2ecc71", "#3498db", "#e74c3c", "#f39c12", "#9b59b6"]
    for sc_idx, sc in enumerate(scenarios):
        sp = build_meridian_body(sc["a"], sc["b"])
        phi_deg = np.degrees(sp["phi_profile"])
        fig.add_trace(go.Scatter(
            x=phi_deg, y=sp["r_profile"], mode="lines", name=sc["name"],
            line=dict(color=colors[sc_idx % len(colors)], width=2.5),
            hovertemplate="緯度: %{x:.1f}\u00b0<br>半径: %{y:.3f}<extra></extra>"))

    fig.add_hline(y=1.0, line=dict(color="gray", dash="dot", width=1),
                  annotation_text="完全一致 (r=1)", annotation_position="top right")
    fig.update_layout(
        title=dict(text="経線プロファイル比較 \u2014 極角 \u03c6 に沿った一致度の変化",
                   font=dict(size=14)),
        xaxis=dict(title="極角 \u03c6 (\u00b0)  [0\u00b0=北極(大) \u2192 180\u00b0=南極(小)]",
                   range=[0, 180]),
        yaxis=dict(title="半径 r (一致度)", range=[0, 1.1]),
        height=380, autosize=True, template="plotly_white",
        margin=dict(l=60, r=30, t=60, b=60),
        legend=dict(x=0.01, y=0.01, bgcolor="rgba(255,255,255,0.8)"))
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
        bias_abs = abs(ba["bias"])
        sd = ba["sd"]
        fig.add_trace(go.Scatter(
            x=[0, bias_abs], y=[0, sd], mode="lines+markers+text",
            line=dict(color=colors[sc_idx % len(colors)], width=3),
            marker=dict(size=[6, 12], symbol=["circle", "diamond"]),
            text=["", sc["name"].split(" (")[0]],
            textposition="top right", textfont=dict(size=10),
            name=f'{sc["name"]} (\u03c6={compass["phi_deg"]:.0f}\u00b0, E={compass["E"]:.1f})',
            hovertemplate=(
                f'{sc["name"]}<br>系統誤差|Bias|: {bias_abs:.2f}<br>'
                f'ランダム誤差 SD: {sd:.2f}<br>総合誤差 E: {compass["E"]:.2f}<br>'
                f'誤差角 \u03c6: {compass["phi_deg"]:.1f}\u00b0<extra></extra>')))

    max_val = max(
        max(abs(compute_ba_stats(sc["a"], sc["b"])["bias"]) for sc in scenarios),
        max(compute_ba_stats(sc["a"], sc["b"])["sd"] for sc in scenarios),
    ) * 1.2
    fig.add_trace(go.Scatter(x=[0, max_val], y=[0, max_val], mode="lines",
                             line=dict(color="gray", dash="dot", width=1),
                             showlegend=False, hoverinfo="skip"))
    fig.add_annotation(x=max_val * 0.7, y=max_val * 0.75,
                       text="\u03c6=45\u00b0 (等分)", showarrow=False,
                       font=dict(size=10, color="gray"))
    fig.update_layout(
        title=dict(text="誤差コンパス \u2014 系統誤差 vs ランダム誤差の角度表現",
                   font=dict(size=14)),
        xaxis=dict(title="|系統誤差| (Bias の絶対値)", rangemode="tozero"),
        yaxis=dict(title="ランダム誤差 (SD)", rangemode="tozero"),
        height=450, autosize=True, template="plotly_white",
        margin=dict(l=60, r=30, t=60, b=60))
    return fig

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0, user-scalable=yes">
<title>BA Sphere \u2014 経線配置型3D表面による測定一致度の可視化</title>
<style>
  *, *::before, *::after {{ box-sizing: border-box; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', sans-serif;
    margin: 0; padding: 16px; background: #f8f9fa; -webkit-text-size-adjust: 100%; }}
  h1 {{ color: #2c3e50; margin-bottom: 5px; font-size: clamp(20px, 5vw, 28px); }}
  .subtitle {{ color: #7f8c8d; margin-bottom: 16px; font-size: clamp(12px, 3vw, 14px); }}
  .section {{ background: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    padding: 12px; margin-bottom: 16px; overflow-x: auto; -webkit-overflow-scrolling: touch; }}
  .section h2 {{ color: #34495e; font-size: clamp(14px, 3.5vw, 16px); margin-top: 0;
    border-bottom: 2px solid #3498db; padding-bottom: 5px; }}
  .grid-2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }}
  .grid-3 {{ display: grid; grid-template-columns: 1fr; gap: 16px; }}
  .legend-box {{ background: #ecf0f1; border-radius: 6px; padding: 12px; margin-top: 10px;
    font-size: clamp(12px, 3vw, 13px); }}
  .legend-box h3 {{ margin: 0 0 8px; font-size: clamp(13px, 3.5vw, 14px); color: #2c3e50; }}
  .legend-box ul {{ margin: 0; padding-left: 18px; }}
  .legend-box li {{ margin-bottom: 6px; line-height: 1.5; }}
  .plotly-graph-div {{ width: 100% !important; }}
  .touch-hint {{ display: none; background: #3498db; color: white; border-radius: 6px;
    padding: 10px 14px; margin-bottom: 12px; font-size: 14px; text-align: center; }}
  .controls-bar {{ display: flex; gap: 8px; margin-bottom: 12px; flex-wrap: wrap; align-items: center; }}
  .ctrl-btn {{ padding: 8px 14px; border: 1px solid #3498db; background: white; color: #3498db;
    border-radius: 6px; cursor: pointer; font-size: 13px; font-weight: 600;
    transition: background 0.2s, color 0.2s; -webkit-tap-highlight-color: transparent; }}
  .ctrl-btn:hover, .ctrl-btn.active {{ background: #3498db; color: white; }}
  .speed-group {{ display: flex; align-items: center; gap: 6px; margin-left: 8px;
    font-size: 12px; color: #555; }}
  .speed-group input[type=range] {{ width: 80px; }}
  @media (min-width: 901px) {{
    .grid-3 {{ grid-template-columns: 3fr 2fr; grid-template-rows: auto auto; }}
    .grid-3 > :first-child {{ grid-row: 1 / 3; }}
  }}
  @media (max-width: 900px) {{ .grid-2 {{ grid-template-columns: 1fr; }} }}
  @media (max-width: 768px) {{
    body {{ padding: 8px; }}
    .section {{ padding: 10px; border-radius: 6px; }}
    .touch-hint {{ display: block; }}
    .js-plotly-plot .plotly .modebar {{ display: none !important; }}
  }}
  @media (max-width: 480px) {{
    body {{ padding: 6px; }}
    .section {{ padding: 8px; margin-bottom: 12px; }}
    .legend-box {{ padding: 8px; }}
    .legend-box ul {{ padding-left: 14px; }}
  }}
</style>
</head>
<body>
<h1>BA Sphere \u2014 Meridian Version</h1>
<p class="subtitle">Bland-Altman \u30d7\u30ed\u30c3\u30c8\u306e\u5e7e\u4f55\u5b66\u7684\u62e1\u5f35 \u2014 \u7d4c\u5ea6\u5206\u6563\u914d\u7f6e\u578b3D\u8868\u9762 (Volume Occupancy Ratio) \u306b\u3088\u308b\u6e2c\u5b9a\u4e00\u81f4\u5ea6\u306e\u53ef\u8996\u5316</p>

<div class="section">
<h2>1. \u30e1\u30a4\u30f3\u30c0\u30c3\u30b7\u30e5\u30dc\u30fc\u30c9 \u2014 \u81ea\u52d5\u56de\u8ee2\u30fb\u30d3\u30e5\u30fc\u5207\u66ff\u30fb\u30b7\u30ca\u30ea\u30aa\u5207\u66ff</h2>
<div class="controls-bar">
  <button class="ctrl-btn" id="rotate-btn" onclick="toggleRotation()">&#9654; \u81ea\u52d5\u56de\u8ee2</button>
  <button class="ctrl-btn" onclick="setCameraView('top')">&#8593; \u4e0a\u304b\u3089</button>
  <button class="ctrl-btn" onclick="setCameraView('bottom')">&#8595; \u4e0b\u304b\u3089</button>
  <button class="ctrl-btn" onclick="setCameraView('side')">&#8594; \u6a2a\u304b\u3089</button>
  <button class="ctrl-btn" onclick="setCameraView('meridian')">&#9678; \u7d4c\u7dda\u6b63\u9762</button>
  <button class="ctrl-btn" onclick="setCameraView('default')">&#10226; \u521d\u671f\u4f4d\u7f6e</button>
  <div class="speed-group">
    <label for="speed-slider">\u901f\u5ea6:</label>
    <input type="range" id="speed-slider" min="10" max="90" value="30" oninput="setSpeed(this.value)">
    <span id="speed-label">30&deg;/s</span>
  </div>
</div>
<div class="touch-hint">\u6307\u3067\u30c9\u30e9\u30c3\u30b0\u3057\u30663D\u56de\u8ee2 / \u30d4\u30f3\u30c1\u3067\u30ba\u30fc\u30e0 / \u4e0a\u306e\u30dc\u30bf\u30f3\u3067\u81ea\u52d5\u56de\u8ee2\u30fb\u30d3\u30e5\u30fc\u5207\u66ff</div>
<div class="grid-3">
  <div>{sphere_html}</div>
  <div>{ba_html}</div>
  <div>{circ_html}</div>
</div>
<div class="legend-box">
  <h3>\u8aad\u307f\u65b9\u30ac\u30a4\u30c9</h3>
  <ul>
    <li><b>3D\u7d4c\u5ea6\u5206\u6563\u914d\u7f6e\u4f53</b>: \u5404\u30c7\u30fc\u30bf\u3092\u7d4c\u5ea6\u65b9\u5411\u306b\u5747\u7b49\u914d\u7f6e\uff0824\u30c7\u30fc\u30bf\u306a\u308915\u00b0\u9593\u9694\uff09\u3002\u7dd1=\u4e00\u81f4\u826f\u597d\u3001\u8d64=\u4e0d\u4e00\u81f4\u3002\u51f9\u51f8\u304c\u54c1\u8cea\u30e0\u30e9\u3092\u76f4\u611f\u7684\u306b\u8868\u73fe\u3002<b>\u81ea\u52d5\u56de\u8ee2</b>\u3067\u5404\u30c7\u30fc\u30bf\u70b9\u306e\u54c1\u8cea\u304c\u9806\u306b\u78ba\u8a8d\u3067\u304d\u308b\u3002<b>\u4e0a\u304b\u3089/\u4e0b\u304b\u3089</b>\u3067\u5168\u4f53\u30d1\u30bf\u30fc\u30f3\u3092\u4e00\u76ee\u3067\u628a\u63e1\u3002</li>
    <li><b>BA\u30d7\u30ed\u30c3\u30c8</b>: \u9752\u7dda=\u30d0\u30a4\u30a2\u30b9\u3001\u8d64\u7834\u7dda=\u4e00\u81f4\u9650\u754c (\u00b11.96SD)</li>
    <li><b>\u5186\u5468\u5bc6\u5ea6</b>: 0\u00b0\u304c\u5b8c\u5168\u4e00\u81f4\u65b9\u5411\u3002\u5206\u5e03\u304c0\u00b0\u306b\u96c6\u4e2d\u3059\u308b\u307b\u3069\u4e00\u81f4\u5ea6\u304c\u9ad8\u3044</li>
    <li><b>VOR</b>: \u4f53\u7a4d\u5360\u6709\u7387 (0\u301c1)\u30021\u306b\u8fd1\u3044\u307b\u3069\u5168\u4f53\u7684\u306a\u4e00\u81f4\u5ea6\u304c\u9ad8\u3044</li>
    <li><b>\u8aa4\u5dee\u89d2\u03c6</b>: 0\u00b0=\u7d14\u7c8b\u306a\u7cfb\u7d71\u8aa4\u5dee\u300190\u00b0=\u7d14\u7c8b\u306a\u30e9\u30f3\u30c0\u30e0\u8aa4\u5dee</li>
    <li><b>Legendre a\u2080</b>: \u5168\u4f53\u7684\u306a\u4e00\u81f4\u5ea6\u3001<b>a\u2081</b>: \u30b9\u30b1\u30fc\u30eb\u4f9d\u5b58\u6027\uff08\u5357\u5317\u975e\u5bfe\u79f0\uff09\u3001<b>a\u2082</b>: \u4e2d\u9593\u5024\u4ed8\u8fd1\u306e\u30d1\u30bf\u30fc\u30f3</li>
  </ul>
</div>
</div>

<div class="section">
<h2>2. \u30b7\u30ca\u30ea\u30aa\u6bd4\u8f03</h2>
{table_html}
</div>

<div class="grid-2">
<div class="section">
<h2>3. \u7d4c\u7dda\u30d7\u30ed\u30d5\u30a1\u30a4\u30eb\u6bd4\u8f03</h2>
{profile_html}
</div>
<div class="section">
<h2>4. \u8aa4\u5dee\u30b3\u30f3\u30d1\u30b9</h2>
{compass_html}
</div>
</div>

<div class="section">
<h2>5. \u54c1\u8cea\u7ba1\u7406\u3067\u306e\u6d3b\u7528\u4f8b \u2014 \u7d4c\u7dda\u914d\u7f6e\u7248\u306e\u5229\u70b9</h2>
<div class="legend-box">
  <ul>
    <li><b>\u7269\u7406\u30c7\u30d0\u30a4\u30b9\u8868\u793a</b>: \u5e38\u6642\u56de\u8ee2\u3059\u308b3D\u30c7\u30a3\u30b9\u30d7\u30ec\u30a4\u3067\u3001\u73fe\u5728\u306e\u54c1\u8cea\u72b6\u614b\u3092\u30ea\u30a2\u30eb\u30bf\u30a4\u30e0\u63d0\u793a\u3002\u5404\u30c7\u30fc\u30bf\u306e\u51f9\u51f8\u304c\u7d4c\u5ea6\u65b9\u5411\u306b\u5206\u6563\u3057\u3066\u304a\u308a\u3001\u56de\u8ee2\u3059\u308b\u3068\u500b\u3005\u306e\u54c1\u8cea\u304c\u9806\u756a\u306b\u898b\u3048\u308b</li>
    <li><b>\u4e0a\u304b\u3089/\u4e0b\u304b\u3089\u306e\u78ba\u8a8d</b>: \u56de\u8ee2\u4f53\u7248\u3067\u306f\u65ad\u9762\u69cb\u7bc9\u304c\u5fc5\u8981\u3060\u3063\u305f\u5168\u4f53\u50cf\u304c\u3001\u4e0a\u4e0b\u304b\u3089\u306e\u8996\u70b9\u3067\u4e00\u76ee\u3067\u628a\u63e1\u53ef\u80fd</li>
    <li><b>\u6e2c\u5b9a\u5668\u6821\u6b63</b>: VOR \u3092\u5b9a\u671f\u30e2\u30cb\u30bf\u30ea\u30f3\u30b0\u3057\u3001\u95be\u5024 (\u4f8b: VOR &lt; 0.95) \u3092\u4e0b\u56de\u3063\u305f\u3089\u518d\u6821\u6b63\u30c8\u30ea\u30ac\u30fc</li>
    <li><b>\u53d7\u5165\u691c\u67fb</b>: \u30ed\u30c3\u30c8\u5185\u30b5\u30f3\u30d7\u30eb\u306e VOR \u304c\u898f\u683c\u5024\u4ee5\u4e0a\u306a\u3089\u5408\u683c\u5224\u5b9a</li>
    <li><b>\u30b9\u30b1\u30fc\u30eb\u4f9d\u5b58\u4e0d\u826f\u306e\u691c\u51fa</b>: Legendre a\u2081 \u304c\u5927\u304d\u3044 \u2192 \u5927\u304d\u3044/\u5c0f\u3055\u3044\u90e8\u54c1\u3067\u7cbe\u5ea6\u304c\u7570\u306a\u308b</li>
    <li><b>\u5de5\u7a0b\u6539\u5584\u306e\u8ffd\u8de1</b>: \u6539\u5584\u524d\u5f8c\u306e\u7d4c\u7dda\u4f53\u3092\u4e26\u3079\u3066\u6bd4\u8f03\u3057\u3001\u3069\u306e\u9818\u57df\u3067\u6539\u5584\u3055\u308c\u305f\u304b\u3092\u76f4\u611f\u7684\u306b\u628a\u63e1</li>
  </ul>
</div>
</div>

<script>
(function() {{
  var sphereDiv = document.getElementById('sphere-chart');
  var autoRotating = false;
  var rotAngle = 0;
  var lastTime = 0;
  var degPerSec = 30;

  window.toggleRotation = function() {{
    autoRotating = !autoRotating;
    var btn = document.getElementById('rotate-btn');
    btn.innerHTML = autoRotating ? '&#9646;&#9646; \u505c\u6b62' : '&#9654; \u81ea\u52d5\u56de\u8ee2';
    if (autoRotating) btn.classList.add('active');
    else btn.classList.remove('active');
    if (autoRotating) {{
      lastTime = performance.now();
      requestAnimationFrame(animate);
    }}
  }};

  function animate(ts) {{
    if (!autoRotating) return;
    var dt = Math.min((ts - lastTime) / 1000, 0.1);
    lastTime = ts;
    rotAngle += degPerSec * dt;
    var rad = rotAngle * Math.PI / 180;
    var r = 2.2;
    Plotly.relayout(sphereDiv, {{
      'scene.camera.eye': {{x: r * Math.cos(rad), y: r * Math.sin(rad), z: 0.6}}
    }});
    requestAnimationFrame(animate);
  }}

  window.setCameraView = function(view) {{
    autoRotating = false;
    var btn = document.getElementById('rotate-btn');
    btn.innerHTML = '&#9654; \u81ea\u52d5\u56de\u8ee2';
    btn.classList.remove('active');
    var eye, up = {{x:0, y:0, z:1}};
    switch(view) {{
      case 'top': eye = {{x:0, y:0.01, z:3}}; up = {{x:0, y:1, z:0}}; break;
      case 'bottom': eye = {{x:0, y:0.01, z:-3}}; up = {{x:0, y:1, z:0}}; break;
      case 'side': eye = {{x:0, y:2.5, z:0}}; break;
      case 'meridian': eye = {{x:2.5, y:0, z:0}}; break;
      default: eye = {{x:1.5, y:1.5, z:0.8}};
    }}
    Plotly.relayout(sphereDiv, {{'scene.camera.eye': eye, 'scene.camera.up': up}});
  }};

  window.setSpeed = function(val) {{
    degPerSec = parseInt(val, 10);
    document.getElementById('speed-label').textContent = degPerSec + '\\u00b0/s';
  }};

  function resizeAll() {{
    document.querySelectorAll('.js-plotly-plot').forEach(function(gd) {{
      if (gd.data) Plotly.Plots.resize(gd);
    }});
  }}
  window.addEventListener('resize', resizeAll);
  window.addEventListener('orientationchange', function() {{
    setTimeout(resizeAll, 300);
  }});
}})();
</script>
</body>
</html>"""


# =============================================================================
# 10. HTML ダッシュボード出力 (経線配置版 — 自動回転・ビュー切替対応)
# =============================================================================

def export_dashboard(output_path: str = "ba_sphere_dashboard.html") -> None:
    """全図をまとめた HTML ダッシュボードを出力する。"""
    all_data = _precompute_all(SCENARIOS)
    sphere_fig = create_sphere_chart(all_data)
    ba_fig = create_ba_chart(all_data)
    circ_fig = create_circular_chart(all_data)
    table = create_comparison_table(SCENARIOS)
    profile = create_profile_comparison(SCENARIOS)
    compass = create_error_compass(SCENARIOS)

    plotly_config = {"responsive": True, "scrollZoom": True}

    sphere_html = sphere_fig.to_html(
        full_html=False, include_plotlyjs="cdn", config=plotly_config,
        div_id="sphere-chart")
    ba_html = ba_fig.to_html(
        full_html=False, include_plotlyjs=False, config=plotly_config)
    circ_html = circ_fig.to_html(
        full_html=False, include_plotlyjs=False, config=plotly_config)
    table_html = table.to_html(
        full_html=False, include_plotlyjs=False, config=plotly_config)
    profile_html = profile.to_html(
        full_html=False, include_plotlyjs=False, config=plotly_config)
    compass_html = compass.to_html(
        full_html=False, include_plotlyjs=False, config=plotly_config)

    # Build HTML with str.format() to avoid f-string brace issues with CSS/JS
    html_template = HTML_TEMPLATE
    html_content = html_template.format(
        sphere_html=sphere_html,
        ba_html=ba_html,
        circ_html=circ_html,
        table_html=table_html,
        profile_html=profile_html,
        compass_html=compass_html,
    )

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"Dashboard exported to: {output_path}")


# =============================================================================
# メイン
# =============================================================================

if __name__ == "__main__":
    export_dashboard("ba_sphere_dashboard.html")
