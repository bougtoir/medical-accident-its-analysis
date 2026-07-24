---
name: testing-aruco-alignment
description: Test the ArUco marker-based surgical pose alignment tool end-to-end. Use when verifying marker detection, alignment scoring, or correction instruction changes.
---

# Testing ArUco Marker Alignment Tool

## Setup

```bash
cd pose_alignment_tool && pip install -r requirements.txt && streamlit run aruco_app.py --server.port 8502
```

App runs at `http://localhost:8502`.

## Generating Test Images

The app requires images with ArUco markers (DICT_4X4_50). Generate synthetic test images:

```python
import cv2
import numpy as np

aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)

def create_marker_image(marker_ids, positions, size=(800, 600), marker_size=80, bg_color=200):
    img = np.ones((size[1], size[0], 3), dtype=np.uint8) * bg_color
    for mid, pos in zip(marker_ids, positions):
        marker_img = cv2.aruco.generateImageMarker(aruco_dict, mid, marker_size)
        marker_bgr = cv2.cvtColor(marker_img, cv2.COLOR_GRAY2BGR)
        x, y = pos
        x1, y1 = x - marker_size//2, y - marker_size//2
        img[y1:y1+marker_size, x1:x1+marker_size] = marker_bgr
    return img

# Standard 6-marker layout simulating body landmarks
marker_ids = [0, 1, 2, 3, 4, 5]
ref_positions = [(400, 100), (200, 150), (600, 150), (250, 400), (550, 400), (400, 300)]
```

## Key Test Cases

### 1. Same Position (Baseline)
- Upload identical images as reference and target
- Expected: Score = 100/100, rotation = +0.0°, message = "✓ 体位はリファレンスと良好に一致しています"

### 2. Shifted Position
- Shift all marker positions by known px offset (e.g., +40px right, +30px down)
- Expected: Score < 100, corrections mention "左に移動" and "頭側に移動"
- Verify correction directions are opposite to the applied shift

### 3. Rotated Markers
- Apply rotation to marker images (e.g., 10°)
- Expected: Score < 100, rotation correction appears

### 4. No Markers (Error Path)
- Upload a blank image with no markers as target
- Expected: Warning "ターゲット画像からマーカーが検出できませんでした" with troubleshooting hints

### 5. Marker Sheet Generation
- Click "マーカーシート生成" in sidebar
- Expected: Sheet image appears with labeled markers + download button

## UI Structure

- **Sidebar**: Settings (rotation/translation thresholds), marker sheet generation
- **Main**: File uploaders (リファレンス画像 / ターゲット画像)
- **Results**: Three tabs (オーバーレイ比較, マーカー詳細, 並列表示)
- **Assessment**: 総合評価 section with score, rotation, translation, and correction instructions

## Tips

- Marker IDs 0-5 correspond to: sternum, left shoulder, right shoulder, left ASIS, right ASIS, xiphoid
- The app uses `adaptiveThreshWinSizeMax=30` for robustness with film overlay
- Translation is reported as % of image dimensions
- Correction directions tell the user how to move the PATIENT (not the camera)
- If markers aren't detected, check image contrast and marker size (minimum ~40px recommended)

## Devin Secrets Needed

None required - this is a local-only tool with no external dependencies.
