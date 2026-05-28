"""
ArUco Marker-Based Pose Alignment Analyzer
===========================================
Compares body positioning between a reference image (CT scan-time photo)
and a target image (intraoperative photo) using ArUco fiducial markers.

Markers are placed on the patient's body before CT, protected with film,
and remain in place through to surgery. This enables camera-angle-independent
comparison of body positioning.
"""

import math
from dataclasses import dataclass, field

import cv2
import numpy as np

# Use 4x4 dictionary with 50 markers (small, robust, sufficient for body markers)
ARUCO_DICT = cv2.aruco.DICT_4X4_50


@dataclass
class MarkerInfo:
    """Information about a single detected ArUco marker."""

    marker_id: int
    corners: np.ndarray  # 4 corner points in image coordinates
    center: np.ndarray  # Center point (x, y)
    rotation_deg: float  # In-plane rotation angle (degrees)
    area: float  # Area in pixels (proxy for distance/scale)


@dataclass
class MarkerDisplacement:
    """Displacement of a single marker between reference and target."""

    marker_id: int
    ref_center: np.ndarray
    target_center: np.ndarray
    translation_px: np.ndarray  # (dx, dy) in pixels
    translation_normalized: np.ndarray  # Normalized by image diagonal
    rotation_diff_deg: float  # Rotation difference in degrees
    scale_ratio: float  # Area ratio (target/ref) - proxy for distance change


@dataclass
class AlignmentResult:
    """Overall alignment analysis between reference and target poses."""

    matched_markers: list[MarkerDisplacement] = field(default_factory=list)
    ref_only_ids: list[int] = field(default_factory=list)
    target_only_ids: list[int] = field(default_factory=list)
    overall_rotation_deg: float = 0.0  # Estimated overall body rotation
    overall_translation: np.ndarray = field(
        default_factory=lambda: np.array([0.0, 0.0])
    )
    alignment_score: float = 0.0  # 0-100, higher = better aligned
    corrections: list[str] = field(default_factory=list)


def detect_markers(image: np.ndarray) -> list[MarkerInfo]:
    """Detect ArUco markers in an image.

    Args:
        image: Input BGR image.

    Returns:
        List of detected MarkerInfo objects.
    """
    aruco_dict = cv2.aruco.getPredefinedDictionary(ARUCO_DICT)
    parameters = cv2.aruco.DetectorParameters()
    # Increase adaptiveThreshWinSizeMax for robustness with film overlay
    parameters.adaptiveThreshWinSizeMax = 30
    parameters.adaptiveThreshWinSizeStep = 5

    detector = cv2.aruco.ArucoDetector(aruco_dict, parameters)
    corners, ids, _ = detector.detectMarkers(image)

    markers = []
    if ids is None:
        return markers

    for i, marker_id in enumerate(ids.flatten()):
        corner_pts = corners[i][0]  # Shape: (4, 2)
        center = corner_pts.mean(axis=0)

        # Calculate in-plane rotation from top-left to top-right edge
        top_vec = corner_pts[1] - corner_pts[0]
        rotation = math.degrees(math.atan2(top_vec[1], top_vec[0]))

        # Calculate area using shoelace formula
        area = cv2.contourArea(corner_pts.astype(np.float32))

        markers.append(
            MarkerInfo(
                marker_id=int(marker_id),
                corners=corner_pts,
                center=center,
                rotation_deg=rotation,
                area=area,
            )
        )

    return markers


def compare_markers(
    ref_markers: list[MarkerInfo],
    target_markers: list[MarkerInfo],
    image_shape: tuple[int, int],
    rotation_threshold: float = 3.0,
    translation_threshold: float = 0.02,
) -> AlignmentResult:
    """Compare marker positions between reference and target images.

    Uses relative marker geometry for camera-angle-tolerant comparison.

    Args:
        ref_markers: Markers detected in reference image.
        target_markers: Markers detected in target image.
        image_shape: (height, width) of the images for normalization.
        rotation_threshold: Degrees threshold for "good" alignment.
        translation_threshold: Normalized translation threshold for "good".

    Returns:
        AlignmentResult with displacement analysis.
    """
    h, w = image_shape[:2]
    diag = math.sqrt(h * h + w * w)

    ref_dict = {m.marker_id: m for m in ref_markers}
    target_dict = {m.marker_id: m for m in target_markers}

    matched_ids = set(ref_dict.keys()) & set(target_dict.keys())
    ref_only = sorted(set(ref_dict.keys()) - matched_ids)
    target_only = sorted(set(target_dict.keys()) - matched_ids)

    displacements = []
    for mid in sorted(matched_ids):
        ref_m = ref_dict[mid]
        tgt_m = target_dict[mid]

        translation = tgt_m.center - ref_m.center
        translation_norm = translation / diag

        rot_diff = _normalize_angle(tgt_m.rotation_deg - ref_m.rotation_deg)

        scale_ratio = tgt_m.area / ref_m.area if ref_m.area > 0 else 1.0

        displacements.append(
            MarkerDisplacement(
                marker_id=mid,
                ref_center=ref_m.center,
                target_center=tgt_m.center,
                translation_px=translation,
                translation_normalized=translation_norm,
                rotation_diff_deg=rot_diff,
                scale_ratio=scale_ratio,
            )
        )

    # Calculate overall body displacement (median of individual markers)
    result = AlignmentResult(
        matched_markers=displacements,
        ref_only_ids=ref_only,
        target_only_ids=target_only,
    )

    if not displacements:
        result.alignment_score = 0.0
        result.corrections.append("共通マーカーが検出されません。マーカーIDを確認してください。")
        return result

    # Overall rotation: median of individual rotations
    rotations = [d.rotation_diff_deg for d in displacements]
    result.overall_rotation_deg = float(np.median(rotations))

    # Overall translation: median of individual translations (normalized)
    translations = np.array([d.translation_normalized for d in displacements])
    result.overall_translation = np.median(translations, axis=0)

    # Alignment score (0-100)
    # Penalize for rotation and translation
    rot_penalty = min(abs(result.overall_rotation_deg) / 30.0, 1.0) * 50
    trans_penalty = (
        min(np.linalg.norm(result.overall_translation) / 0.15, 1.0) * 50
    )
    result.alignment_score = max(0.0, 100.0 - rot_penalty - trans_penalty)

    # Generate correction instructions
    result.corrections = _generate_corrections(
        result, rotation_threshold, translation_threshold
    )

    return result


def _normalize_angle(angle: float) -> float:
    """Normalize angle to [-180, 180] range."""
    while angle > 180:
        angle -= 360
    while angle < -180:
        angle += 360
    return angle


def _generate_corrections(
    result: AlignmentResult,
    rotation_threshold: float,
    translation_threshold: float,
) -> list[str]:
    """Generate human-readable correction instructions."""
    corrections = []

    rot = result.overall_rotation_deg
    tx, ty = result.overall_translation

    if abs(rot) < rotation_threshold and np.linalg.norm(
        result.overall_translation
    ) < translation_threshold:
        corrections.append("✓ 体位はリファレンスと良好に一致しています")
        return corrections

    # Rotation correction
    if abs(rot) >= rotation_threshold:
        direction = "時計回り" if rot > 0 else "反時計回り"
        corrections.append(f"回転: 体を {abs(rot):.1f}° {direction}に修正してください")

    # Horizontal translation
    if abs(tx) >= translation_threshold:
        direction = "左" if tx > 0 else "右"
        corrections.append(f"水平: 体を{direction}に移動してください（ズレ: {abs(tx)*100:.1f}%）")

    # Vertical translation
    if abs(ty) >= translation_threshold:
        direction = "頭側" if ty > 0 else "足側"
        corrections.append(f"垂直: 体を{direction}に移動してください（ズレ: {abs(ty)*100:.1f}%）")

    # Per-marker details for non-uniform displacement
    if len(result.matched_markers) >= 2:
        rot_std = np.std([d.rotation_diff_deg for d in result.matched_markers])
        if rot_std > 2.0:
            corrections.append(
                f"⚠ マーカー間で回転が不均一です（σ={rot_std:.1f}°）。"
                "体の一部が局所的にズレている可能性があります"
            )

    return corrections


def draw_markers_on_image(
    image: np.ndarray,
    markers: list[MarkerInfo],
    color: tuple = (0, 255, 0),
    label_prefix: str = "",
) -> np.ndarray:
    """Draw detected markers on image with IDs and axes."""
    annotated = image.copy()

    for m in markers:
        # Draw marker border
        pts = m.corners.astype(np.int32)
        cv2.polylines(annotated, [pts], True, color, 2)

        # Draw center
        center = tuple(m.center.astype(int))
        cv2.circle(annotated, center, 5, color, -1)

        # Draw ID label
        label = f"{label_prefix}ID:{m.marker_id}"
        cv2.putText(
            annotated,
            label,
            (center[0] + 10, center[1] - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            color,
            2,
        )

        # Draw rotation indicator (arrow from center along top edge direction)
        top_vec = m.corners[1] - m.corners[0]
        top_vec_norm = top_vec / (np.linalg.norm(top_vec) + 1e-8)
        arrow_end = (m.center + top_vec_norm * 25).astype(int)
        cv2.arrowedLine(
            annotated, center, tuple(arrow_end), color, 2, tipLength=0.3
        )

    return annotated


def draw_alignment_overlay(
    target_image: np.ndarray,
    result: AlignmentResult,
    ref_markers: list[MarkerInfo],
) -> np.ndarray:
    """Draw alignment comparison overlay on target image.

    Shows:
    - Reference marker positions as blue ghosts
    - Target marker positions in green
    - Displacement vectors as red arrows
    - Correction text
    """
    overlay = target_image.copy()

    # Draw reference marker ghosts (blue, semi-transparent)
    ghost = overlay.copy()
    ref_dict = {m.marker_id: m for m in ref_markers}
    for m in ref_markers:
        pts = m.corners.astype(np.int32)
        cv2.polylines(ghost, [pts], True, (255, 150, 0), 2)
        center = tuple(m.center.astype(int))
        cv2.circle(ghost, center, 5, (255, 150, 0), -1)
        cv2.putText(
            ghost,
            f"REF:{m.marker_id}",
            (center[0] + 10, center[1] - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.4,
            (255, 150, 0),
            1,
        )
    cv2.addWeighted(ghost, 0.4, overlay, 0.6, 0, overlay)

    # Draw displacement arrows for matched markers
    for disp in result.matched_markers:
        ref_pt = tuple(disp.ref_center.astype(int))
        tgt_pt = tuple(disp.target_center.astype(int))

        # Determine color based on displacement magnitude
        mag = np.linalg.norm(disp.translation_normalized)
        if mag < 0.02:
            arrow_color = (0, 255, 0)  # Green = good
        elif mag < 0.05:
            arrow_color = (0, 165, 255)  # Orange = warning
        else:
            arrow_color = (0, 0, 255)  # Red = critical

        # Draw arrow from reference position to target position
        cv2.arrowedLine(overlay, ref_pt, tgt_pt, arrow_color, 2, tipLength=0.2)

        # Draw rotation difference
        if abs(disp.rotation_diff_deg) >= 2.0:
            rot_text = f"{disp.rotation_diff_deg:+.1f}\xb0"
            cv2.putText(
                overlay,
                rot_text,
                (tgt_pt[0] + 15, tgt_pt[1] + 15),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.4,
                arrow_color,
                1,
            )

    # Draw target markers in green
    for disp in result.matched_markers:
        tgt_pt = tuple(disp.target_center.astype(int))
        cv2.circle(overlay, tgt_pt, 6, (0, 255, 0), -1)
        cv2.putText(
            overlay,
            f"ID:{disp.marker_id}",
            (tgt_pt[0] + 10, tgt_pt[1] - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.4,
            (0, 255, 0),
            1,
        )

    return overlay


def generate_marker_image(
    marker_id: int, size_px: int = 200, border_bits: int = 1
) -> np.ndarray:
    """Generate a single ArUco marker image for printing.

    Args:
        marker_id: Marker ID (0-49 for DICT_4X4_50).
        size_px: Output image size in pixels.
        border_bits: Width of white border in marker bits.

    Returns:
        Grayscale marker image.
    """
    aruco_dict = cv2.aruco.getPredefinedDictionary(ARUCO_DICT)
    marker_img = cv2.aruco.generateImageMarker(aruco_dict, marker_id, size_px)

    # Add white border
    border_px = size_px // (4 + 2 * border_bits) * border_bits
    bordered = cv2.copyMakeBorder(
        marker_img,
        border_px,
        border_px,
        border_px,
        border_px,
        cv2.BORDER_CONSTANT,
        value=255,
    )
    return bordered


def generate_marker_sheet(
    marker_ids: list[int],
    marker_size_px: int = 150,
    cols: int = 4,
    margin: int = 30,
) -> np.ndarray:
    """Generate a printable sheet of ArUco markers.

    Args:
        marker_ids: List of marker IDs to include.
        marker_size_px: Size of each marker in pixels.
        cols: Number of columns in the sheet.
        margin: Margin between markers in pixels.

    Returns:
        Image of the marker sheet (grayscale).
    """
    rows = math.ceil(len(marker_ids) / cols)

    cell_size = marker_size_px + margin * 2
    sheet_w = cols * cell_size + margin
    sheet_h = rows * cell_size + margin + 40  # Extra space for labels

    sheet = np.ones((sheet_h, sheet_w), dtype=np.uint8) * 255

    for idx, mid in enumerate(marker_ids):
        row = idx // cols
        col = idx % cols

        marker_img = generate_marker_image(mid, marker_size_px)
        # Crop to exact marker_size_px (remove extra border for layout)
        h_m, w_m = marker_img.shape[:2]
        # Place in grid
        x = margin + col * cell_size + (cell_size - w_m) // 2
        y = margin + row * cell_size + (cell_size - h_m) // 2

        # Ensure fits
        y_end = min(y + h_m, sheet_h)
        x_end = min(x + w_m, sheet_w)
        sheet[y:y_end, x:x_end] = marker_img[: y_end - y, : x_end - x]

        # Add ID label below marker
        label_y = y + h_m + 15
        if label_y < sheet_h:
            cv2.putText(
                sheet,
                f"ID: {mid}",
                (x + w_m // 4, label_y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                0,
                1,
            )

    # Add title
    cv2.putText(
        sheet,
        "ArUco Markers (4x4_50) - Cut and attach to patient",
        (margin, sheet_h - 15),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        0,
        1,
    )

    return sheet
