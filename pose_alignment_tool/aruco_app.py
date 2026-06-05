"""
ArUco Marker-Based Surgical Pose Alignment Tool
================================================
Compares body positioning between CT scan-time and intraoperative photos
using ArUco fiducial markers placed on the patient's body.

Includes SNM (Sacral Nerve Stimulation) entry point guidance mode that
calculates and displays the planned insertion point from CT-measured offsets.

Usage:
    streamlit run aruco_app.py
"""

import threading

import av
import cv2
import numpy as np
import streamlit as st
from PIL import Image
from streamlit_webrtc import VideoProcessorBase, webrtc_streamer

from aruco_analyzer import (
    AlignmentResult,
    EntryPointGuideResult,
    MarkerInfo,
    MARKER_SIZES_CM,
    compare_markers,
    compute_entry_point_from_ct_offset,
    compute_px_per_mm,
    detect_markers,
    draw_alignment_overlay,
    draw_entry_point_guide,
    draw_markers_on_image,
    draw_probe_distance,
    generate_marker_sheet,
)

_PROXIMITY_BEEP_JS = """
<script>
(function() {
  // Proximity beep audio feedback via Web Audio API.
  // Reads distance encoded in top-left pixels of the WebRTC video element.
  // Pixel format: BGR → canvas reads as RGB
  //   R (OpenCV B) = encoded distance value (distance_mm * 2)
  //   G (OpenCV G) = 42 (magic validation byte)
  //   B (OpenCV R) = 0
  // When no probe: R=0, G=0, B=255

  const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
  let beepTimer = null;
  let isBeeping = false;
  let currentOsc = null;
  let currentGain = null;
  let lastInterval = -1;

  function startBeep() {
    if (currentOsc) return;
    currentOsc = audioCtx.createOscillator();
    currentGain = audioCtx.createGain();
    currentOsc.type = 'sine';
    currentOsc.frequency.value = 880;
    currentGain.gain.value = 0.3;
    currentOsc.connect(currentGain);
    currentGain.connect(audioCtx.destination);
    currentOsc.start();
    isBeeping = true;
  }

  function stopBeep() {
    if (currentOsc) {
      currentOsc.stop();
      currentOsc.disconnect();
      currentGain.disconnect();
      currentOsc = null;
      currentGain = null;
    }
    isBeeping = false;
  }

  function playPulse(durationMs) {
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.type = 'sine';
    osc.frequency.value = 880;
    gain.gain.value = 0.3;
    osc.connect(gain);
    gain.connect(audioCtx.destination);
    osc.start();
    osc.stop(audioCtx.currentTime + durationMs / 1000);
  }

  function getBeepInterval(distMm) {
    if (distMm < 0) return -1;       // no probe
    if (distMm <= 5) return 0;       // continuous
    if (distMm <= 10) return 150;    // fast
    if (distMm <= 20) return 300;    // medium
    return 1000;                     // slow
  }

  function readDistanceFromVideo() {
    // Find the video element rendered by streamlit-webrtc
    const videos = document.querySelectorAll('video');
    let video = null;
    for (const v of videos) {
      if (v.videoWidth > 0 && v.videoHeight > 0 && !v.paused) {
        video = v;
        break;
      }
    }
    if (!video) return -1;

    const canvas = document.createElement('canvas');
    canvas.width = 8;
    canvas.height = 8;
    const ctx2d = canvas.getContext('2d', {willReadFrequently: true});
    ctx2d.drawImage(video, 0, 0, 8, 8, 0, 0, 8, 8);
    const pixel = ctx2d.getImageData(2, 2, 1, 1).data;
    // Canvas reads as RGBA. OpenCV wrote BGR → WebRTC sends as-is.
    // In canvas: R=OpenCV_B(encoded_val), G=OpenCV_G(42), B=OpenCV_R(0)
    // Actually: WebRTC re-encodes, so video shows normal RGB.
    // OpenCV BGR [encoded_val, 42, 0] → displayed as RGB [0, 42, encoded_val]
    // So in canvas: R=0, G=42, B=encoded_val
    const r = pixel[0];
    const g = pixel[1];
    const b = pixel[2];

    // Validate magic byte (G=42)
    if (g >= 38 && g <= 46) {
      return b / 2.0;  // encoded_val / 2 = distance_mm
    }
    return -1;  // No valid encoding found
  }

  function updateAudio() {
    if (audioCtx.state === 'suspended') {
      audioCtx.resume();
    }
    const distMm = readDistanceFromVideo();
    const interval = getBeepInterval(distMm);

    if (interval === lastInterval) return;
    lastInterval = interval;

    // Clear existing timer
    if (beepTimer) { clearInterval(beepTimer); beepTimer = null; }
    stopBeep();

    if (interval < 0) {
      // No probe detected - silence
      return;
    }
    if (interval === 0) {
      // Continuous tone (target reached)
      startBeep();
      return;
    }
    // Pulsed beep
    playPulse(80);
    beepTimer = setInterval(function() { playPulse(80); }, interval);
  }

  // Poll every 200ms
  setInterval(updateAudio, 200);
})();
</script>
"""

st.set_page_config(
    page_title="術中体位アライメント（ArUcoマーカー）",
    page_icon="🎯",
    layout="wide",
)

st.title("術中体位アライメントツール（ArUcoマーカー版）")

# Mode selection
mode = st.sidebar.radio(
    "モード選択",
    options=["体位比較", "刺入点ガイダンス（SNM）", "連続モード（SNM）"],
    index=0,
    help="体位比較: CT撮影時 vs 術中体位の比較\n刺入点ガイダンス: CT計測値から刺入点位置を表示\n連続モード: カメラでリアルタイム表示",
)

# Sidebar settings
st.sidebar.markdown("---")
st.sidebar.header("設定")

# Marker size selection (shared)
marker_size_label = st.sidebar.selectbox(
    "マーカー物理サイズ",
    options=list(MARKER_SIZES_CM.keys()),
    index=3,  # Default to 特大 (5cm) for SNM precision
    help="実際に印刷するマーカーの一辺の長さ。大きいほど精度向上",
)
marker_physical_size_cm = MARKER_SIZES_CM[marker_size_label]

if mode == "体位比較":
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
    help="推奨(SNM): 左PSIS(ID:0), 右PSIS(ID:1), C7(ID:2), 左肩甲骨(ID:3), 右肩甲骨(ID:4), Th12(ID:5)",
)

# Marker print size (pixel size for the generated sheet)
marker_print_sizes = {
    "小 (2cm)": 80,
    "中 (3cm)": 120,
    "大 (4cm)": 160,
    "特大 (5cm)": 200,
}
marker_print_label = st.sidebar.selectbox(
    "印刷マーカーサイズ",
    options=list(marker_print_sizes.keys()),
    index=3,
    format_func=lambda x: x,
)
marker_print_px = marker_print_sizes[marker_print_label]

if st.sidebar.button("マーカーシート生成"):
    try:
        ids = [int(x.strip()) for x in marker_ids_input.split(",") if x.strip()]
        if ids:
            sheet = generate_marker_sheet(ids, marker_size_px=marker_print_px)
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


# ============================================================
# MODE: 刺入点ガイダンス (Entry Point Guidance)
# ============================================================
if mode == "刺入点ガイダンス（SNM）":
    st.markdown(
        """
    **SNM刺入点ガイダンスモード**

    CT計測で求めた「基準マーカーから刺入点(S3孔)までのオフセット」を入力すると、
    術中写真上に刺入点位置のクロスヘアを表示します。
    """
    )

    # CT offset input
    st.sidebar.markdown("### CT計測値入力")
    st.sidebar.markdown(
        """
    **座標系の定義:**
    - 原点マーカー → 軸マーカー方向 = 側方軸 (LAT)
    - それに垂直（足側方向）= 尾側軸 (CAUD)
    """
    )

    origin_id = st.sidebar.number_input(
        "原点マーカーID（例: 左PSIS = 0）",
        min_value=0, max_value=49, value=0, step=1,
        help="座標原点として使用するマーカー",
    )
    axis_id = st.sidebar.number_input(
        "軸マーカーID（例: 右PSIS = 1）",
        min_value=0, max_value=49, value=1, step=1,
        help="原点→このマーカーの方向が側方軸になります",
    )

    st.sidebar.markdown("---")
    st.sidebar.markdown("**刺入点オフセット (CT計測値)**")
    offset_caudal = st.sidebar.number_input(
        "尾側オフセット (mm)",
        min_value=-200.0, max_value=200.0, value=40.0, step=1.0,
        help="原点から足側方向の距離。+ = 尾側(足側), - = 頭側",
    )
    offset_lateral = st.sidebar.number_input(
        "側方オフセット (mm)",
        min_value=-200.0, max_value=200.0, value=15.0, step=1.0,
        help="原点から側方への距離。+ = 軸マーカー方向, - = 反対方向",
    )

    # Image upload (single image for guide mode)
    st.subheader("📷 術中画像（マーカー検出用）")
    guide_file = st.file_uploader(
        "術中の体位写真（基準マーカー付き）",
        type=["jpg", "jpeg", "png", "bmp"],
        key="guide",
    )

    if guide_file:
        with st.spinner("マーカーを検出中..."):
            guide_image = load_image(guide_file)
            markers = detect_markers(guide_image)

        st.metric("検出マーカー数", f"{len(markers)}")
        if markers:
            st.caption(f"検出ID: {', '.join(str(m.marker_id) for m in markers)}")

        if not markers:
            st.error(
                "⚠️ マーカーが検出できませんでした。\n\n"
                "**確認事項:**\n"
                "- マーカーが鮮明に写っていますか？\n"
                "- フィルムの反射でマーカーが見えにくくなっていませんか？"
            )
        elif origin_id == axis_id:
            st.error("⚠️ 原点マーカーと軸マーカーは異なるIDを指定してください。")
        else:
            # Compute entry point
            result = compute_entry_point_from_ct_offset(
                markers=markers,
                origin_marker_id=origin_id,
                axis_marker_id=axis_id,
                offset_caudal_mm=offset_caudal,
                offset_lateral_mm=offset_lateral,
                marker_physical_size_cm=marker_physical_size_cm,
            )

            if result is None:
                detected_ids = [m.marker_id for m in markers]
                missing = []
                if origin_id not in detected_ids:
                    missing.append(f"原点マーカー(ID:{origin_id})")
                if axis_id not in detected_ids:
                    missing.append(f"軸マーカー(ID:{axis_id})")
                if missing:
                    st.error(f"⚠️ 必要なマーカーが検出されません: {', '.join(missing)}")
                else:
                    st.error("⚠️ 座標計算に失敗しました。マーカーが近すぎる可能性があります。")
            else:
                # Draw overlay
                overlay = draw_entry_point_guide(guide_image, result, markers)
                overlay_rgb = cv2.cvtColor(overlay, cv2.COLOR_BGR2RGB)

                st.subheader("刺入点ガイド表示")
                st.image(
                    overlay_rgb,
                    caption="緑クロスヘア = CT計画上の刺入点位置",
                    use_container_width=True,
                )

                # Info panel
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("スケール", f"{result.px_per_mm:.1f} px/mm")
                    st.caption(f"マーカーサイズ: {marker_physical_size_cm}cm")
                with col2:
                    st.metric("尾側オフセット", f"{offset_caudal:.1f} mm")
                with col3:
                    st.metric("側方オフセット", f"{offset_lateral:.1f} mm")

                st.markdown("---")
                st.markdown(
                    """
                ### 表示内容
                - **緑クロスヘア + 円**: CT計画上の刺入点位置（ここにペンでマーキング）
                - **内側の小円**: S3孔サイズ（直径約5mm）の許容範囲
                - **橙 ORIGIN**: 座標原点マーカー
                - **水色 AXIS**: 軸方向マーカー
                - **左下スケールバー**: 10mmの実寸参考
                - **LAT/CAUD矢印**: 座標軸の方向確認
                """
                )

    else:
        st.markdown(
            """
        ---
        ### 使い方（SNM刺入点ガイダンス）

        #### 事前準備
        1. ArUcoマーカーを印刷（サイドバー「マーカーシート生成」）
        2. マーカー中心にBB弾（鉛コート）を固定
        3. 左右PSIS等の骨突出部に貼付、フィルムで保護

        #### CT撮影
        4. CT撮影（BB弾がCTに映る）
        5. CT画像上でBB弾(=マーカー中心)からS3孔までの距離を計測
           - 尾側方向: ○○mm
           - 側方: ○○mm

        #### CT撮影後
        6. BB弾を除去、ArUcoマーカーのみ残す

        #### 手術当日
        7. 伏臥位で術野の写真を撮影
        8. この画面にアップロード
        9. CT計測値（オフセット）をサイドバーに入力
        10. 表示されたクロスヘアの位置にペンでマーキング
        11. 穿刺

        #### 推奨マーカー配置（伏臥位・SNM）
        - ID:0 = 左後上腸骨棘 (PSIS) ← **原点**
        - ID:1 = 右後上腸骨棘 (PSIS) ← **軸**
        - ID:2 = C7棘突起
        - ID:3 = 左肩甲骨内側縁
        - ID:4 = 右肩甲骨内側縁
        - ID:5 = Th12棘突起付近
        """
        )


# ============================================================
# MODE: 連続モード (Real-time Camera Mode)
# ============================================================
elif mode == "連続モード（SNM）":
    st.markdown(
        """
    **連続モード（リアルタイムカメラ）**

    カメラ映像にリアルタイムで刺入点クロスヘアをオーバーレイ表示します。
    カメラをマーカーに向けると自動的に検出・表示されます。
    """
    )

    # CT offset input (shared with static mode)
    st.sidebar.markdown("### CT計測値入力")
    st.sidebar.markdown(
        """
    **座標系の定義:**
    - 原点マーカー → 軸マーカー方向 = 側方軸 (LAT)
    - それに垂直（足側方向）= 尾側軸 (CAUD)
    """
    )

    live_origin_id = st.sidebar.number_input(
        "原点マーカーID",
        min_value=0, max_value=49, value=0, step=1,
        key="live_origin",
    )
    live_axis_id = st.sidebar.number_input(
        "軸マーカーID",
        min_value=0, max_value=49, value=1, step=1,
        key="live_axis",
    )

    st.sidebar.markdown("---")
    st.sidebar.markdown("**刺入点オフセット (CT計測値)**")
    live_offset_caudal = st.sidebar.number_input(
        "尾側オフセット (mm)",
        min_value=-200.0, max_value=200.0, value=40.0, step=1.0,
        key="live_caudal",
    )
    live_offset_lateral = st.sidebar.number_input(
        "側方オフセット (mm)",
        min_value=-200.0, max_value=200.0, value=15.0, step=1.0,
        key="live_lateral",
    )

    st.sidebar.markdown("---")
    st.sidebar.markdown("**プローブマーカー（近接音用）**")
    live_probe_id = st.sidebar.number_input(
        "プローブマーカーID",
        min_value=0, max_value=49, value=10, step=1,
        key="live_probe",
        help="手持ちのマーカーID。刺入点に近づくとビープ音が速くなります",
    )
    live_beep_enabled = st.sidebar.checkbox(
        "近接ビープ音を有効化", value=True, key="live_beep",
    )

    class EntryPointVideoProcessor(VideoProcessorBase):
        """Process video frames with ArUco detection and entry point overlay."""

        def __init__(self):
            self._lock = threading.Lock()
            self._origin_id = 0
            self._axis_id = 1
            self._offset_caudal = 40.0
            self._offset_lateral = 15.0
            self._marker_size_cm = 5.0
            self._probe_id = 10
            self._beep_enabled = True
            self._last_detection_count = 0
            self._last_scale = 0.0
            self._last_distance_mm = -1.0

        def update_params(
            self,
            origin_id: int,
            axis_id: int,
            offset_caudal: float,
            offset_lateral: float,
            marker_size_cm: float,
            probe_id: int,
            beep_enabled: bool,
        ):
            with self._lock:
                self._origin_id = origin_id
                self._axis_id = axis_id
                self._offset_caudal = offset_caudal
                self._offset_lateral = offset_lateral
                self._marker_size_cm = marker_size_cm
                self._probe_id = probe_id
                self._beep_enabled = beep_enabled

        def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
            img = frame.to_ndarray(format="bgr24")

            with self._lock:
                origin_id = self._origin_id
                axis_id = self._axis_id
                offset_caudal = self._offset_caudal
                offset_lateral = self._offset_lateral
                marker_size_cm = self._marker_size_cm
                probe_id = self._probe_id
                beep_enabled = self._beep_enabled

            markers = detect_markers(img)
            self._last_detection_count = len(markers)
            marker_dict = {m.marker_id: m for m in markers}

            # Reset distance encoding (no probe detected)
            img[0:4, 0:4] = (255, 0, 0)  # No-probe signal

            if markers and origin_id != axis_id:
                result = compute_entry_point_from_ct_offset(
                    markers=markers,
                    origin_marker_id=origin_id,
                    axis_marker_id=axis_id,
                    offset_caudal_mm=offset_caudal,
                    offset_lateral_mm=offset_lateral,
                    marker_physical_size_cm=marker_size_cm,
                )
                if result is not None:
                    self._last_scale = result.px_per_mm
                    img = draw_entry_point_guide(img, result, markers)

                    # Check for probe marker and draw distance
                    if beep_enabled and probe_id in marker_dict:
                        img, dist_mm = draw_probe_distance(
                            img, result, marker_dict[probe_id]
                        )
                        self._last_distance_mm = dist_mm
                    else:
                        self._last_distance_mm = -1.0
                else:
                    img = _draw_marker_status(img, markers, origin_id, axis_id)
                    self._last_distance_mm = -1.0
            elif markers:
                img = _draw_marker_status(img, markers, origin_id, axis_id)
                self._last_distance_mm = -1.0
            else:
                cv2.putText(
                    img, "No markers detected",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2,
                )
                self._last_distance_mm = -1.0

            return av.VideoFrame.from_ndarray(img, format="bgr24")

    ctx = webrtc_streamer(
        key="snm-entry-point-live",
        video_processor_factory=EntryPointVideoProcessor,
        media_stream_constraints={
            "video": {"frameRate": {"ideal": 5, "max": 10}},
            "audio": False,
        },
        async_processing=True,
    )

    if ctx.video_processor:
        ctx.video_processor.update_params(
            origin_id=live_origin_id,
            axis_id=live_axis_id,
            offset_caudal=live_offset_caudal,
            offset_lateral=live_offset_lateral,
            marker_size_cm=marker_physical_size_cm,
            probe_id=live_probe_id,
            beep_enabled=live_beep_enabled,
        )

    # Inject JavaScript for proximity beep audio feedback
    if live_beep_enabled:
        st.components.v1.html(
            _PROXIMITY_BEEP_JS,
            height=0,
        )

    st.markdown(
        """
    ---
    ### 操作方法
    1. 上の **START** ボタンを押してカメラを起動
    2. カメラを体表のArUcoマーカーに向ける
    3. マーカーが検出されると自動的にクロスヘアが表示される
    4. **プローブマーカー**（手持ち）を刺入点に近づけるとビープ音が速くなる
    5. 連続音になったらその位置にペンでマーキング

    **ビープ音の距離:**
    - 🔴 > 20mm: 遅いビープ（1秒間隔）
    - 🟡 10-20mm: 中間ビープ（0.3秒間隔）
    - 🟢 5-10mm: 速いビープ（0.15秒間隔）
    - ✅ < 5mm: 連続音（目標到達）

    **注意:** ブラウザがカメラへのアクセスを要求します。許可してください。
    """
    )


# ============================================================
# MODE: 体位比較 (Pose Comparison)
# ============================================================
else:
    st.markdown(
        """
    CT撮影時に体表に貼付したArUcoマーカーを用いて、
    術中体位のズレを検出し修正方向を提示します。
    """
    )

    st.sidebar.markdown(
        """
    ### 色の意味
    - 🟢 **緑**: 現在のマーカー位置（ターゲット）
    - 🔵 **青**: リファレンスのマーカー位置（ゴースト）
    - 🟡 **黄矢印**: 小さなズレ
    - 🔴 **赤矢印**: 大きなズレ（要修正）

    ### 推奨マーカー配置（伏臥位）
    - C7棘突起 (ID:0)
    - 左肩甲骨内側縁 (ID:1)
    - 右肩甲骨内側縁 (ID:2)
    - 左後上腸骨棘 PSIS (ID:3)
    - 右後上腸骨棘 PSIS (ID:4)
    - Th12棘突起付近 (ID:5)
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


def _draw_marker_status(
    img: np.ndarray,
    markers: list[MarkerInfo],
    origin_id: int,
    axis_id: int,
) -> np.ndarray:
    """Draw detected markers with status when entry point can't be computed."""
    overlay = img.copy()
    detected_ids = {m.marker_id for m in markers}

    for m in markers:
        pts = m.corners.astype(np.int32)
        color = (0, 255, 0) if m.marker_id in (origin_id, axis_id) else (150, 150, 150)
        cv2.polylines(overlay, [pts], True, color, 2)
        center = tuple(m.center.astype(int))
        cv2.circle(overlay, center, 4, color, -1)
        label = f"ID:{m.marker_id}"
        if m.marker_id == origin_id:
            label += " (ORIGIN)"
        elif m.marker_id == axis_id:
            label += " (AXIS)"
        cv2.putText(
            overlay, label,
            (center[0] + 8, center[1] - 8),
            cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1,
        )

    missing = []
    if origin_id not in detected_ids:
        missing.append(f"ORIGIN(ID:{origin_id})")
    if axis_id not in detected_ids:
        missing.append(f"AXIS(ID:{axis_id})")
    if missing:
        cv2.putText(
            overlay, f"Missing: {', '.join(missing)}",
            (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 165, 255), 2,
        )

    return overlay
