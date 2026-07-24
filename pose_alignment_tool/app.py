"""
Surgical Pose Alignment Tool
============================
Markerless body pose comparison for aligning intraoperative positioning
with pre-operative CT scan positioning.

Usage:
    streamlit run app.py
"""

import cv2
import numpy as np
import streamlit as st
from PIL import Image

from pose_analyzer import (
    BODY_SEGMENTS,
    JOINT_ANGLES,
    AngleComparison,
    compare_poses,
    create_side_by_side,
    detect_pose,
    draw_comparison_overlay,
)

st.set_page_config(
    page_title="術中体位アライメント",
    page_icon="🏥",
    layout="wide",
)

st.title("術中体位アライメントツール")
st.markdown(
    """
CT撮影時の体位（リファレンス）と術中体位（ターゲット）を比較し、
修正すべき箇所と方向を表示します。
"""
)

# Sidebar settings
st.sidebar.header("設定")
threshold_warning = st.sidebar.slider(
    "警告閾値 (°)", min_value=1.0, max_value=20.0, value=5.0, step=0.5
)
threshold_critical = st.sidebar.slider(
    "要修正閾値 (°)", min_value=5.0, max_value=30.0, value=10.0, step=1.0
)
show_ghost_overlay = st.sidebar.checkbox("リファレンスゴースト表示", value=True)

st.sidebar.markdown("---")
st.sidebar.header("部分体位検出")
detection_confidence = st.sidebar.slider(
    "検出感度（低い＝部分体位でも検出しやすい）",
    min_value=0.1,
    max_value=0.8,
    value=0.3,
    step=0.05,
)
visibility_threshold = st.sidebar.slider(
    "ランドマーク可視性閾値",
    min_value=0.1,
    max_value=0.8,
    value=0.3,
    step=0.05,
    help="この値以下のvisibilityのランドマークは角度計算から除外されます",
)

st.sidebar.markdown("---")
st.sidebar.markdown(
    """
### 色の意味
- 🟢 **緑**: 許容範囲内
- 🟡 **黄**: 要注意（閾値付近）
- 🔴 **赤**: 要修正
- 🔵 **青線**: リファレンス姿勢（ゴースト）

### 部分体位について
CT画像で全身が写っていなくても、
見えている関節のみで比較を行います。
検出感度を下げると部分体位でも
検出しやすくなります。
"""
)

# Image upload
col1, col2 = st.columns(2)

with col1:
    st.subheader("📷 リファレンス画像（CT撮影時体位）")
    ref_file = st.file_uploader(
        "CT撮影時の体位写真をアップロード",
        type=["jpg", "jpeg", "png", "bmp"],
        key="ref",
    )

with col2:
    st.subheader("📷 ターゲット画像（術中体位）")
    target_file = st.file_uploader(
        "現在の術中体位の写真をアップロード",
        type=["jpg", "jpeg", "png", "bmp"],
        key="target",
    )


def load_image(uploaded_file) -> np.ndarray:
    """Load uploaded file as OpenCV image."""
    image = Image.open(uploaded_file)
    image_np = np.array(image)
    if len(image_np.shape) == 2:
        image_np = cv2.cvtColor(image_np, cv2.COLOR_GRAY2BGR)
    elif image_np.shape[2] == 4:
        image_np = cv2.cvtColor(image_np, cv2.COLOR_RGBA2BGR)
    else:
        image_np = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)
    return image_np


def severity_color(severity: str) -> str:
    """Return color for severity level."""
    if severity == "good":
        return "🟢"
    elif severity == "warning":
        return "🟡"
    return "🔴"


if ref_file and target_file:
    with st.spinner("姿勢を解析中..."):
        ref_image = load_image(ref_file)
        target_image = load_image(target_file)

        ref_result = detect_pose(
            ref_image,
            detection_confidence=detection_confidence,
            visibility_threshold=visibility_threshold,
        )
        target_result = detect_pose(
            target_image,
            detection_confidence=detection_confidence,
            visibility_threshold=visibility_threshold,
        )

    if not ref_result.detected:
        st.error(
            "⚠️ リファレンス画像から姿勢を検出できませんでした。\n\n"
            "**対処法:** 検出感度を下げるか、体の輪郭が見える画像を使用してください。"
        )
    elif not target_result.detected:
        st.error(
            "⚠️ ターゲット画像から姿勢を検出できませんでした。\n\n"
            "**対処法:** 検出感度を下げるか、体の輪郭が見える画像を使用してください。"
        )
    else:
        # Compare poses
        comparisons = compare_poses(
            ref_result, target_result, threshold_warning, threshold_critical
        )

        # Show partial detection info
        total_angles = len(JOINT_ANGLES) + len(BODY_SEGMENTS)
        detected_angles = len(ref_result.angles)
        if detected_angles < total_angles:
            st.info(
                f"ℹ️ 部分検出: リファレンス画像で {detected_angles}/{total_angles} "
                f"の測定項目が検出されました（見えている部分のみ比較します）"
            )

        # Visualization
        st.markdown("---")
        st.subheader("解析結果")

        tab1, tab2, tab3 = st.tabs(["🔍 オーバーレイ比較", "📊 角度差分一覧", "📐 並列表示"])

        with tab1:
            if show_ghost_overlay:
                overlay = draw_comparison_overlay(
                    target_result.image_with_pose,
                    ref_result,
                    target_result,
                    comparisons,
                    visibility_threshold=visibility_threshold,
                )
            else:
                overlay = target_result.image_with_pose

            overlay_rgb = cv2.cvtColor(overlay, cv2.COLOR_BGR2RGB)
            st.image(overlay_rgb, caption="ターゲット画像 + リファレンスゴースト + 修正指示", use_container_width=True)

            st.markdown(
                """
            **表示内容:**
            - 緑線 = 現在の体位（ターゲット）
            - 青線（半透明）= CT撮影時体位（リファレンス）
            - 赤/黄丸 = 修正が必要な関節（数値は角度差）
            """
            )

        with tab2:
            st.markdown("### 関節角度比較")

            # Summary metrics
            critical_count = sum(1 for c in comparisons if c.severity == "critical")
            warning_count = sum(1 for c in comparisons if c.severity == "warning")
            good_count = sum(1 for c in comparisons if c.severity == "good")

            mcol1, mcol2, mcol3 = st.columns(3)
            mcol1.metric("✓ 良好", good_count)
            mcol2.metric("⚠ 要注意", warning_count)
            mcol3.metric("✗ 要修正", critical_count)

            st.markdown("---")

            # Detailed table
            for comp in sorted(comparisons, key=lambda c: -abs(c.difference)):
                icon = severity_color(comp.severity)
                with st.expander(
                    f"{icon} {comp.name}  |  差分: {comp.difference:+.1f}°",
                    expanded=(comp.severity == "critical"),
                ):
                    c1, c2, c3 = st.columns(3)
                    c1.metric("リファレンス角度", f"{comp.ref_angle:.1f}°")
                    c2.metric("現在の角度", f"{comp.target_angle:.1f}°")
                    c3.metric("差分", f"{comp.difference:+.1f}°")
                    st.markdown(f"**修正指示:** {comp.correction_text}")

        with tab3:
            side_by_side = create_side_by_side(
                ref_result.image_with_pose,
                target_result.image_with_pose,
                ref_result,
                target_result,
            )
            side_by_side_rgb = cv2.cvtColor(side_by_side, cv2.COLOR_BGR2RGB)
            st.image(side_by_side_rgb, caption="左: リファレンス（CT体位） | 右: ターゲット（術中体位）", use_container_width=True)

        # Overall assessment
        st.markdown("---")
        st.subheader("総合評価")

        if critical_count == 0 and warning_count == 0:
            st.success("✓ すべての関節角度が許容範囲内です。体位はリファレンスと一致しています。")
        elif critical_count == 0:
            st.warning(f"⚠ {warning_count}箇所が閾値付近です。微調整を推奨します。")
        else:
            st.error(f"✗ {critical_count}箇所で大きなズレがあります。以下を修正してください：")
            for comp in comparisons:
                if comp.severity == "critical":
                    st.markdown(f"- **{comp.name}**: {comp.correction_text}")

elif ref_file or target_file:
    st.info("両方の画像をアップロードしてください。")
else:
    st.markdown(
        """
    ---
    ### 使い方
    1. **リファレンス画像**: CT撮影時の体位を撮影した写真をアップロード
    2. **ターゲット画像**: 術中の現在の体位を撮影した写真をアップロード
    3. 自動で姿勢を検出し、角度の差分と修正方向を表示します

    ### 注意事項
    - 全身が写った写真を使用してください（MediaPipeは全身検出を前提としています）
    - 撮影角度をできるだけ揃えてください（同じカメラ位置が理想）
    - 衣服の上からでも検出可能ですが、体のラインが見える方が精度が上がります
    """
    )

st.markdown("---")
st.caption("Powered by MediaPipe Pose | マーカーレス姿勢推定による術中体位アライメント支援ツール")
