"""
特許出願用 図面（図1〜図7）作図スクリプト。

JPO提出図面の慣行に合わせ、白黒の線図（無彩色・グレースケール）で作図する。
各図には符号（1: サシェ, 2: 包材, 3: MMT粒子, 4: タグ付き紐, 5: インジケータ,
6: 飲料, 7: 飲用容器）を付す。

出力: patent_fig1.png 〜 patent_fig7.png
"""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch, Polygon, Circle
import numpy as np

# 日本語フォント（IPAGothic）。JPO図面の慣行に合わせ、無彩色（純粋な白黒）で作図する。
matplotlib.rcParams["font.family"] = "IPAGothic"
matplotlib.rcParams["axes.unicode_minus"] = False
matplotlib.rcParams["hatch.linewidth"] = 0.5

LINE = "black"
# グレーを用いず、破線・ハッチングで区別する。
GRAY = "black"


def _grid(ax, axis="both"):
    ax.grid(axis=axis, color="black", lw=0.3, ls=":")


def _hatch_span(ax, x0, x1, ymin=0.0, ymax=1.0, hatch="...."):
    ax.axvspan(x0, x1, ymin=ymin, ymax=ymax, facecolor="none",
               edgecolor="black", hatch=hatch, lw=0.0)


def _save(fig, name):
    fig.savefig(name, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"saved: {name}")


def fig1():
    """図1: サシェの外観図および断面図。"""
    fig, (axA, axB) = plt.subplots(1, 2, figsize=(9, 5))
    for ax in (axA, axB):
        ax.set_xlim(0, 10)
        ax.set_ylim(0, 12)
        ax.axis("off")

    # (A) 外観図（テトラ型）
    axA.set_title("(A) 外観図", fontsize=11)
    # 紐とタグ
    axA.plot([5, 5], [8.2, 10.6], color=LINE, lw=1.2)
    tag = mpatches.FancyBboxPatch(
        (3.9, 10.6), 2.2, 1.0, boxstyle="round,pad=0.05",
        facecolor="white", edgecolor=LINE, lw=1.2,
    )
    axA.add_patch(tag)
    axA.text(5, 11.1, "4", ha="center", va="center", fontsize=10)
    # テトラ型（四面体）本体：三角形＋稜線
    tri = Polygon([(2.6, 2.5), (7.4, 2.5), (5.0, 8.2)], closed=True,
                  fill=False, edgecolor=LINE, lw=1.6)
    axA.add_patch(tri)
    axA.plot([5.0, 5.0], [2.5, 8.2], color=GRAY, lw=0.8, ls="--")  # 稜線
    axA.plot([2.6, 5.0], [2.5, 5.0], color=GRAY, lw=0.8, ls="--")
    axA.plot([7.4, 5.0], [2.5, 5.0], color=GRAY, lw=0.8, ls="--")
    axA.annotate("1", xy=(6.2, 4.6), xytext=(8.3, 5.6), fontsize=10,
                 arrowprops=dict(arrowstyle="->", color=LINE, lw=1))
    axA.annotate("2", xy=(3.6, 3.6), xytext=(1.2, 4.4), fontsize=10,
                 arrowprops=dict(arrowstyle="->", color=LINE, lw=1))

    # (B) 断面図
    axB.set_title("(B) 断面図", fontsize=11)
    # 包材の壁（二重線）
    outer = mpatches.FancyBboxPatch(
        (2.4, 2.5), 5.2, 6.0, boxstyle="round,pad=0.02",
        facecolor="white", edgecolor=LINE, lw=1.6,
    )
    axB.add_patch(outer)
    inner = mpatches.FancyBboxPatch(
        (2.65, 2.75), 4.7, 5.5, boxstyle="round,pad=0.02",
        facecolor="none", edgecolor=GRAY, lw=0.8,
    )
    axB.add_patch(inner)
    # 内部のMMT粒子（円、粒径>孔径を表現）
    rng = np.random.default_rng(3)
    for _ in range(26):
        x = rng.uniform(3.0, 7.0)
        y = rng.uniform(3.1, 8.0)
        axB.add_patch(Circle((x, y), 0.22, fill=False, edgecolor=LINE, lw=0.9))
    # 包材の孔（小さな切れ目）を右壁に表現
    for yy in np.linspace(3.2, 7.8, 10):
        axB.plot([7.6, 7.75], [yy, yy], color=LINE, lw=0.8)
    axB.annotate("3\n（粒径0.05〜1.0mm）", xy=(4.4, 6.6), xytext=(0.2, 9.6),
                 fontsize=9, ha="left",
                 arrowprops=dict(arrowstyle="->", color=LINE, lw=1))
    axB.annotate("2\n（孔径1〜50μm）", xy=(7.7, 5.5), xytext=(7.9, 9.4),
                 fontsize=9, ha="left",
                 arrowprops=dict(arrowstyle="->", color=LINE, lw=1))
    _save(fig, "patent_fig1.png")


def fig2():
    """図2（選択図）: MMT層間のインターカレーション吸着機構。"""
    fig, ax = plt.subplots(figsize=(8, 5.5))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 9)
    ax.axis("off")
    ax.set_title("図2　モンモリロナイト層間の選択的吸着機構", fontsize=11)

    # シリケート層（横長の帯）
    layer_y = [1.5, 4.0, 6.5]
    for y in layer_y:
        ax.add_patch(mpatches.Rectangle((1.0, y), 10.0, 0.7,
                                        facecolor="white", edgecolor=LINE, lw=1.2,
                                        hatch="...."))
        ax.text(0.6, y + 0.35, "シリケート層", ha="right", va="center", fontsize=8)

    # 層間カチオン（+）
    for y in [2.9, 5.4]:
        for x in np.linspace(2.0, 10.0, 6):
            ax.text(x, y, "＋", ha="center", va="center", fontsize=9, color=LINE)

    # カフェイン分子（小円）→ 層間に取り込まれる
    for x in [3.2, 5.0, 6.8]:
        ax.add_patch(Circle((x, 2.9), 0.26, fill=False, edgecolor=LINE, lw=1.3))
    # 上方から層間に入るカフェイン
    ax.add_patch(Circle((4.0, 8.3), 0.28, fill=False, edgecolor=LINE, lw=1.3))
    ax.add_patch(FancyArrowPatch((4.0, 7.9), (4.0, 5.9),
                                 arrowstyle="-|>,head_length=0.35,head_width=0.22",
                                 mutation_scale=10, color=LINE, lw=1.3))
    ax.text(0.6, 8.5, "カフェイン（MW194）\n→層間に吸着", ha="left", va="center", fontsize=9)

    # ポリフェノール（大きい六角形）→ 排除
    hexx = mpatches.RegularPolygon((9.6, 8.3), numVertices=6, radius=0.5,
                                   orientation=0.3, fill=False, edgecolor=LINE, lw=1.3)
    ax.add_patch(hexx)
    ax.add_patch(FancyArrowPatch((9.6, 7.7), (9.6, 6.1),
                                 arrowstyle="-|>,head_length=0.35,head_width=0.22",
                                 mutation_scale=10, color=LINE, lw=1.3, ls="--"))
    ax.plot([9.1, 10.1], [6.0, 6.6], color=LINE, lw=1.8)  # ×印（排除）
    ax.plot([9.1, 10.1], [6.6, 6.0], color=LINE, lw=1.8)
    ax.text(10.4, 8.3, "ポリフェノール\n（MW290〜869）\n→立体排除", ha="left",
            va="center", fontsize=9)
    _save(fig, "patent_fig2.png")


def _bw_bar(ax, cats, vals, hatches):
    x = np.arange(len(cats))
    for xi, v, h in zip(x, vals, hatches):
        ax.bar(xi, v, width=0.6, facecolor="white", edgecolor=LINE, hatch=h, lw=1.2)
        ax.text(xi, v + 1.5, f"{v}", ha="center", va="bottom", fontsize=8)
    ax.set_xticks(x)
    ax.set_xticklabels(cats, fontsize=8)


def fig3():
    """図3: 各種飲料のカフェイン除去率・ポリフェノール保持率（実施例6）。"""
    drinks = ["緑茶", "紅茶", "烏龍茶", "コーヒー", "エスプレッソ", "エナジー\nドリンク"]
    removal = [93, 90, 92, 88, 85, 72]
    retain = [96, 93, 95, 92, 90, 0]
    x = np.arange(len(drinks))
    w = 0.38
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.bar(x - w / 2, removal, w, facecolor="white", edgecolor=LINE, hatch="///", lw=1.1,
           label="カフェイン除去率")
    ax.bar(x + w / 2, retain, w, facecolor="white", edgecolor=LINE, hatch="...", lw=1.1,
           label="ポリフェノール保持率")
    ax.set_xticks(x)
    ax.set_xticklabels(drinks, fontsize=8)
    ax.set_ylabel("割合 (%)")
    ax.set_ylim(0, 110)
    ax.set_title("図3　各種飲料における除去率・保持率（実施例6）", fontsize=11)
    ax.legend(fontsize=8, frameon=False)
    _grid(ax, axis="y")
    _save(fig, "patent_fig3.png")


def fig4():
    """図4: 粒径 vs 3分後カフェイン除去率（実施例4）。"""
    size = [0.05, 0.1, 0.3, 0.5, 1.0, 2.0]
    rem = [75, 89, 91, 85, 68, 42]
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.plot(size, rem, marker="o", color=LINE, lw=1.5, mfc="white", mec=LINE)
    for s, r in zip(size, rem):
        ax.text(s, r + 1.8, f"{r}", ha="center", fontsize=8)
    _hatch_span(ax, 0.1, 0.5)
    ax.text(0.3, 50, "最適範囲\n0.1〜0.5mm", ha="center", fontsize=8)
    ax.set_xscale("log")
    ax.set_xlabel("MMT粒径 (mm)")
    ax.set_ylabel("3分後カフェイン除去率 (%)")
    ax.set_ylim(30, 100)
    ax.set_title("図4　粒径とカフェイン吸着効率の関係（実施例4）", fontsize=11)
    _grid(ax)
    _save(fig, "patent_fig4.png")


def fig5():
    """図5: 接触時間 vs カフェイン除去率 / Fe溶出量（実施例5）。"""
    t = [1, 3, 5, 10, 20, 30, 60]
    rem = [62, 88, 93, 96, 97, 97, 98]
    fe = [0.005, 0.02, 0.05, 0.12, 0.28, 0.45, 1.2]
    fig, ax1 = plt.subplots(figsize=(7.5, 4.5))
    ax1.plot(t, rem, marker="o", color=LINE, lw=1.5, mfc="white", mec=LINE,
             label="カフェイン除去率")
    ax1.set_xlabel("接触時間 (分)")
    ax1.set_ylabel("カフェイン除去率 (%)")
    ax1.set_ylim(50, 105)
    ax2 = ax1.twinx()
    ax2.plot(t, fe, marker="s", color="black", lw=1.5, ls="--", mfc="white", mec="black",
             label="Fe溶出量")
    ax2.axhline(0.3, color=LINE, lw=1.0, ls=":")
    ax2.text(60, 0.34, "飲料水基準 0.3 mg/L", ha="right", va="bottom", fontsize=8)
    ax2.set_ylabel("Fe溶出量 (mg/L)")
    ax2.set_ylim(0, 1.3)
    _hatch_span(ax1, 3, 5)
    ax1.set_title("図5　接触時間と除去率・Fe溶出量の関係（実施例5）", fontsize=11)
    lines1, lab1 = ax1.get_legend_handles_labels()
    lines2, lab2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, lab1 + lab2, fontsize=8, frameon=False, loc="center right")
    _grid(ax1)
    _save(fig, "patent_fig5.png")


def fig6():
    """図6: 選択性2次元プロット（本発明 vs 比較例）。"""
    pts = {
        "MMT／Al3+交換MMT（本発明）": (93, 96, "o", (-14, 10)),
        "活性炭": (89, 31, "s", (8, 4)),
        "ゼオライト": (28, 94, "D", (8, 4)),
        "架橋ポリマー": (78, 62, "v", (8, 4)),
    }
    fig, ax = plt.subplots(figsize=(6.5, 5.5))
    for label, (xx, yy, mk, off) in pts.items():
        ax.scatter(xx, yy, s=90, facecolor="white", edgecolor=LINE, marker=mk, lw=1.3)
        ax.annotate(label, (xx, yy), textcoords="offset points", xytext=off,
                    fontsize=8, ha="right" if off[0] < 0 else "left")
    _hatch_span(ax, 80, 100, ymin=0.8)
    ax.text(90, 84, "高除去・高保持", ha="center", fontsize=8)
    ax.set_xlabel("カフェイン除去率 (%)")
    ax.set_ylabel("カテキン（ポリフェノール）保持率 (%)")
    ax.set_xlim(20, 105)
    ax.set_ylim(20, 105)
    ax.set_title("図6　吸着材の選択性比較", fontsize=11)
    _grid(ax)
    _save(fig, "patent_fig6.png")


def fig7():
    """図7: 平型 vs テトラ型の外観およびカップ収まり比較（実施例7）。"""
    fig, (axA, axB) = plt.subplots(1, 2, figsize=(9, 5))
    for ax in (axA, axB):
        ax.set_xlim(0, 10)
        ax.set_ylim(0, 10)
        ax.axis("off")

    # (A) 平型：カップからはみ出す
    axA.set_title("(A) 平型（比較）", fontsize=11)
    # カップ（台形）
    cupA = Polygon([(2.5, 1.5), (7.5, 1.5), (8.3, 6.0), (1.7, 6.0)], closed=True,
                   fill=False, edgecolor=LINE, lw=1.6)
    axA.add_patch(cupA)
    axA.text(5, 0.9, "7（内径75mm）", ha="center", fontsize=9)
    # 平型サシェ（縦長長方形、上端がカップ開口より上＝はみ出す）
    axA.add_patch(mpatches.Rectangle((4.1, 3.0), 1.8, 5.5, facecolor="white",
                                     edgecolor=LINE, lw=1.4))
    axA.plot([4.1, 5.9], [8.5, 8.5], color=LINE, lw=1.0)
    axA.annotate("1（60×80mm）\nはみ出す", xy=(5.0, 8.0), xytext=(6.4, 8.8),
                 fontsize=8, ha="left",
                 arrowprops=dict(arrowstyle="->", color=LINE, lw=1))

    # (B) テトラ型：カップ内に収まる
    axB.set_title("(B) テトラ型（本発明）", fontsize=11)
    cupB = Polygon([(2.5, 1.5), (7.5, 1.5), (8.3, 6.0), (1.7, 6.0)], closed=True,
                   fill=False, edgecolor=LINE, lw=1.6)
    axB.add_patch(cupB)
    axB.text(5, 0.9, "7（内径75mm）", ha="center", fontsize=9)
    # テトラ（三角形）カップ内に収まる
    triB = Polygon([(3.6, 2.0), (6.4, 2.0), (5.0, 4.8)], closed=True,
                   fill=False, edgecolor=LINE, lw=1.6)
    axB.add_patch(triB)
    axB.plot([5.0, 5.0], [2.0, 4.8], color=GRAY, lw=0.7, ls="--")
    axB.annotate("1'（底面35mm角）\nカップ内に収まる", xy=(5.0, 3.4),
                 xytext=(0.2, 8.6), fontsize=8, ha="left",
                 arrowprops=dict(arrowstyle="->", color=LINE, lw=1))
    _save(fig, "patent_fig7.png")


if __name__ == "__main__":
    fig1()
    fig2()
    fig3()
    fig4()
    fig5()
    fig6()
    fig7()
    print("All patent figures generated.")
