"""
ArUco Marker-Based Surgical Pose Alignment Tool
================================================
Compares body positioning between CT scan-time and intraoperative photos
using ArUco fiducial markers placed on the patient's body.

Usage:
    streamlit run aruco_app.py
"""

import cv2
import numpy as np
import streamlit as st
from PIL import Image

from aruco_analyzer import (
    AlignmentResult,
    MarkerInfo,
    compare_markers,
    detect_markers,
    draw_alignment_overlay,
    draw_markers_on_image,
    generate_marker_sheet,
)

st.set_page_config(
    page_title="術中体位アライメント（ArUcoマーカー）",
    page_icon="🎯",
    layout="wide",
)

st.title("術中体位アライメントツール（ArUcoマーカー版）")
st.markdown(
    """
CT撮影時に体表に貼付したArUcoマーカーを用いて、
術中体位のズレを検出し修正方向を提示します。
"""
)

# Sidebar settings
st.sidebar.header("設定")
rotation_threshold = st.sidebar.slider(
    "回転許容閾値 (°)", min_value=1.0, max_value=15.0, value=3.0, step=0.5
)
translation_threshold = st.sidebar.slider(
    "移動許容閾値 (%)", min_value=0.5, max_value=10.0, value=2.0, step=0.5
)

st.sidebar.markdown("---")
st.sidebar.header("マーカー印刷")
marker_ids_input = st.sidebar.text_input(
    "印刷するマーカーID（カンマ区切り）",
    value="0,1,2,3,4,5",
    help="推奨: 体の各部位に1つずつ配置（例: 胸骨、左右肩、左右腸骨稜、剣状突起）",
)
marker_size = st.sidebar.selectbox(
    "マーカーサイズ",
    options=[("小 (2cm)", 80), ("中 (3cm)", 120), ("大 (4cm)", 160)],
    index=1,
    format_func=lambda x: x[0],
)

if st.sidebar.button("マーカーシート生成"):
    try:
        ids = [int(x.strip()) for x in marker_ids_input.split(",") if x.strip()]
        if ids:
            sheet = generate_marker_sheet(ids, marker_size_px=marker_size[1])
            st.sidebar.image(sheet, caption="印刷用マーカーシート", use_container_width=True)
            # Provide download
            _, buf = cv2.imencode(".png", sheet)
            st.sidebar.download_button(
                "📥 マーカーシートをダウンロード",
                data=buf.tobytes(),
                file_name="aruco_markers.png",
                mime="image/png",
            )
        else:
            st.sidebar.error("有効なマーカーIDを入力してください")
    except ValueError:
        st.sidebar.error("IDは数値で入力してください（例: 0,1,2,3）")

st.sidebar.markdown("---")
st.sidebar.markdown(
    """
### 色の意味
- 🟢 **緑**: 現在のマーカー位置（ターゲット）
- 🔵 **青**: リファレンスのマーカー位置（ゴースト）
- 🟡 **黄矢印**: 小さなズレ
- 🔴 **赤矢印**: 大きなズレ（要修正）

### 推奨マーカー配置
- 胸骨上端 (ID:0)
- 左肩峰 (ID:1)
- 右肩峰 (ID:2)
- 左上前腸骨棘 (ID:3)
- 右上前腸骨棘 (ID:4)
- 剣状突起 (ID:5)
"""
)

# Image upload
col1, col2 = st.columns(2)

with col1:
    st.subheader("📷 リファレンス画像（CT撮影時）")
    ref_file = st.file_uploader(
        "CT撮影時の体位写真（マーカー付き）",
        type=["jpg", "jpeg", "png", "bmp"],
        key="ref",
    )

with col2:
    st.subheader("📷 ターゲット画像（術中）")
    target_file = st.file_uploader(
        "術中の体位写真（マーカー付き）",
        type=["jpg", "jpeg", "png", "bmp"],
        key="target",
    )


def load_image(uploaded_file) -> np.ndarray:
    """Load uploaded file as OpenCV BGR image."""
    image = Image.open(uploaded_file)
    image_np = np.array(image)
    if len(image_np.shape) == 2:
        image_np = cv2.cvtColor(image_np, cv2.COLOR_GRAY2BGR)
    elif image_np.shape[2] == 4:
        image_np = cv2.cvtColor(image_np, cv2.COLOR_RGBA2BGR)
    else:
        image_np = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)
    return image_np


if ref_file and target_file:
    with st.spinner("マーカーを検出中..."):
        ref_image = load_image(ref_file)
        target_image = load_image(target_file)

        ref_markers = detect_markers(ref_image)
        target_markers = detect_markers(target_image)

    # Detection summary
    st.markdown("---")
    col_r, col_t = st.columns(2)
    with col_r:
        st.metric("リファレンス検出数", f"{len(ref_markers)} マーカー")
        if ref_markers:
            st.caption(f"ID: {', '.join(str(m.marker_id) for m in ref_markers)}")
    with col_t:
        st.metric("ターゲット検出数", f"{len(target_markers)} マーカー")
        if target_markers:
            st.caption(f"ID: {', '.join(str(m.marker_id) for m in target_markers)}")

    if not ref_markers:
        st.error(
            "⚠️ リファレンス画像からマーカーが検出できませんでした。\n\n"
            "**確認事項:**\n"
            "- マーカーが鮮明に写っていますか？\n"
            "- フィルムの反射でマーカーが見えにくくなっていませんか？\n"
            "- 画像の解像度は十分ですか？"
        )
    elif not target_markers:
        st.error(
            "⚠️ ターゲット画像からマーカーが検出できませんでした。\n\n"
            "**確認事項:**\n"
            "- マーカーが鮮明に写っていますか？\n"
            "- 術中ドレープ等でマーカーが隠れていませんか？"
        )
    else:
        # Compare markers
        result = compare_markers(
            ref_markers,
            target_markers,
            image_shape=target_image.shape,
            rotation_threshold=rotation_threshold,
            translation_threshold=translation_threshold / 100.0,
        )

        # Tabs for visualization
        st.markdown("---")
        st.subheader("解析結果")

        tab1, tab2, tab3 = st.tabs(
            ["🔍 オーバーレイ比較", "📊 マーカー詳細", "📐 並列表示"]
        )

        with tab1:
            overlay = draw_alignment_overlay(target_image, result, ref_markers)
            overlay_rgb = cv2.cvtColor(overlay, cv2.COLOR_BGR2RGB)
            st.image(
                overlay_rgb,
                caption="ターゲット画像 + リファレンスゴースト + 変位ベクトル",
                use_container_width=True,
            )
            st.markdown(
                """
            **表示内容:**
            - 緑点 = 現在のマーカー位置
            - 青枠（半透明）= CT撮影時のマーカー位置
            - 矢印 = リファレンスからのズレ方向（緑=良好、黄=注意、赤=要修正）
            - 角度表示 = マーカーの回転ズレ
            """
            )

        with tab2:
            if not result.matched_markers:
                st.warning("共通IDのマーカーがありません。リファレンスとターゲットで同じIDのマーカーを使用してください。")
            else:
                st.markdown("### 個別マーカー変位")
                for disp in result.matched_markers:
                    mag = np.linalg.norm(disp.translation_normalized)
                    if mag < translation_threshold / 100.0 and abs(disp.rotation_diff_deg) < rotation_threshold:
                        icon = "🟢"
                        status = "良好"
                    elif mag < translation_threshold * 2 / 100.0 and abs(disp.rotation_diff_deg) < rotation_threshold * 2:
                        icon = "🟡"
                        status = "要注意"
                    else:
                        icon = "🔴"
                        status = "要修正"

                    with st.expander(
                        f"{icon} マーカー ID:{disp.marker_id}  |  {status}",
                        expanded=(status == "要修正"),
                    ):
                        c1, c2, c3 = st.columns(3)
                        c1.metric("移動量", f"{mag*100:.2f}%")
                        c2.metric("回転差", f"{disp.rotation_diff_deg:+.1f}°")
                        c3.metric("スケール比", f"{disp.scale_ratio:.2f}x")

                        dx, dy = disp.translation_normalized
                        if abs(dx) > 0.005 or abs(dy) > 0.005:
                            directions = []
                            if abs(dx) > 0.005:
                                directions.append(f"{'左' if dx > 0 else '右'}に{abs(dx)*100:.1f}%")
                            if abs(dy) > 0.005:
                                directions.append(f"{'下' if dy > 0 else '上'}に{abs(dy)*100:.1f}%")
                            st.caption(f"移動方向: {', '.join(directions)}")

            if result.ref_only_ids:
                st.info(f"ℹ️ リファレンスのみ検出: ID {result.ref_only_ids}（ターゲットで未検出）")
            if result.target_only_ids:
                st.info(f"ℹ️ ターゲットのみ検出: ID {result.target_only_ids}（リファレンスで未検出）")

        with tab3:
            ref_annotated = draw_markers_on_image(ref_image, ref_markers, color=(255, 200, 0), label_prefix="REF ")
            tgt_annotated = draw_markers_on_image(target_image, target_markers, color=(0, 255, 0), label_prefix="")

            # Resize to same height
            h1, w1 = ref_annotated.shape[:2]
            h2, w2 = tgt_annotated.shape[:2]
            target_h = max(h1, h2)
            scale1 = target_h / h1
            scale2 = target_h / h2
            ref_resized = cv2.resize(ref_annotated, (int(w1 * scale1), target_h))
            tgt_resized = cv2.resize(tgt_annotated, (int(w2 * scale2), target_h))

            # Labels
            cv2.putText(ref_resized, "REFERENCE (CT)", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 200, 0), 2)
            cv2.putText(tgt_resized, "TARGET (OR)", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

            combined = np.hstack([ref_resized, tgt_resized])
            combined_rgb = cv2.cvtColor(combined, cv2.COLOR_BGR2RGB)
            st.image(combined_rgb, caption="左: リファレンス（CT体位） | 右: ターゲット（術中体位）", use_container_width=True)

        # Overall assessment
        st.markdown("---")
        st.subheader("総合評価")

        score_col, correction_col = st.columns([1, 2])

        with score_col:
            score = result.alignment_score
            if score >= 80:
                st.success(f"アライメントスコア: {score:.0f}/100")
            elif score >= 50:
                st.warning(f"アライメントスコア: {score:.0f}/100")
            else:
                st.error(f"アライメントスコア: {score:.0f}/100")

            st.metric("全体回転", f"{result.overall_rotation_deg:+.1f}°")
            tx, ty = result.overall_translation
            st.metric("全体移動", f"({tx*100:+.1f}%, {ty*100:+.1f}%)")

        with correction_col:
            st.markdown("### 修正指示")
            for correction in result.corrections:
                st.markdown(f"- {correction}")

elif ref_file or target_file:
    st.info("両方の画像をアップロードしてください。")
else:
    st.markdown(
        """
    ---
    ### 使い方

    #### 事前準備
    1. サイドバーの「マーカーシート生成」でマーカーを印刷
    2. マーカーを患者の体表に貼付（推奨位置は左サイドバー参照）
    3. 透明フィルムでマーカーを保護

    #### CT撮影時
    4. マーカーが見える状態で体位写真を撮影（→リファレンス画像）

    #### 手術時
    5. 術中体位の写真を撮影（→ターゲット画像）
    6. 両画像をアップロードして体位のズレを確認

    ### ArUcoマーカーの利点
    - **カメラ角度に非依存**: 異なる方向から撮影しても比較可能
    - **高精度**: マーカーの位置・回転を正確に検出
    - **部分検出対応**: 一部のマーカーが隠れても残りで比較可能
    - **CT画像にも対応**: 放射線不透過マーカーと併用すればCT上でも位置確認可能
    """
    )

st.markdown("---")
st.caption("ArUco Marker-Based Surgical Pose Alignment | OpenCV ArUco検出による術中体位アライメント支援ツール")
