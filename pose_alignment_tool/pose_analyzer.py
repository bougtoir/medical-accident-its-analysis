"""
Markerless Pose Alignment Analyzer
Compares body positioning between a reference image (e.g., CT scan position)
and a target image (e.g., intraoperative position) using MediaPipe Pose Landmarker.
"""

import math
import os
import urllib.request
from dataclasses import dataclass
from pathlib import Path

import cv2
import mediapipe as mp
import numpy as np
from mediapipe.tasks.python import BaseOptions, vision

PoseLandmark = vision.PoseLandmark

MODEL_URL = "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_heavy/float16/latest/pose_landmarker_heavy.task"
MODEL_PATH = str(Path(__file__).parent / "pose_landmarker_heavy.task")


def _ensure_model():
    """Download pose landmarker model if not present."""
    if not os.path.exists(MODEL_PATH):
        print(f"Downloading pose model to {MODEL_PATH}...")
        urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
        print("Download complete.")

# Pose connections for drawing (matching MediaPipe's standard skeleton)
POSE_CONNECTIONS = [
    (PoseLandmark.NOSE, PoseLandmark.LEFT_EYE_INNER),
    (PoseLandmark.LEFT_EYE_INNER, PoseLandmark.LEFT_EYE),
    (PoseLandmark.LEFT_EYE, PoseLandmark.LEFT_EYE_OUTER),
    (PoseLandmark.LEFT_EYE_OUTER, PoseLandmark.LEFT_EAR),
    (PoseLandmark.NOSE, PoseLandmark.RIGHT_EYE_INNER),
    (PoseLandmark.RIGHT_EYE_INNER, PoseLandmark.RIGHT_EYE),
    (PoseLandmark.RIGHT_EYE, PoseLandmark.RIGHT_EYE_OUTER),
    (PoseLandmark.RIGHT_EYE_OUTER, PoseLandmark.RIGHT_EAR),
    (PoseLandmark.MOUTH_LEFT, PoseLandmark.MOUTH_RIGHT),
    (PoseLandmark.LEFT_SHOULDER, PoseLandmark.RIGHT_SHOULDER),
    (PoseLandmark.LEFT_SHOULDER, PoseLandmark.LEFT_ELBOW),
    (PoseLandmark.LEFT_ELBOW, PoseLandmark.LEFT_WRIST),
    (PoseLandmark.RIGHT_SHOULDER, PoseLandmark.RIGHT_ELBOW),
    (PoseLandmark.RIGHT_ELBOW, PoseLandmark.RIGHT_WRIST),
    (PoseLandmark.LEFT_SHOULDER, PoseLandmark.LEFT_HIP),
    (PoseLandmark.RIGHT_SHOULDER, PoseLandmark.RIGHT_HIP),
    (PoseLandmark.LEFT_HIP, PoseLandmark.RIGHT_HIP),
    (PoseLandmark.LEFT_HIP, PoseLandmark.LEFT_KNEE),
    (PoseLandmark.LEFT_KNEE, PoseLandmark.LEFT_ANKLE),
    (PoseLandmark.RIGHT_HIP, PoseLandmark.RIGHT_KNEE),
    (PoseLandmark.RIGHT_KNEE, PoseLandmark.RIGHT_ANKLE),
    (PoseLandmark.LEFT_WRIST, PoseLandmark.LEFT_THUMB),
    (PoseLandmark.LEFT_WRIST, PoseLandmark.LEFT_INDEX),
    (PoseLandmark.LEFT_WRIST, PoseLandmark.LEFT_PINKY),
    (PoseLandmark.RIGHT_WRIST, PoseLandmark.RIGHT_THUMB),
    (PoseLandmark.RIGHT_WRIST, PoseLandmark.RIGHT_INDEX),
    (PoseLandmark.RIGHT_WRIST, PoseLandmark.RIGHT_PINKY),
    (PoseLandmark.LEFT_ANKLE, PoseLandmark.LEFT_HEEL),
    (PoseLandmark.LEFT_ANKLE, PoseLandmark.LEFT_FOOT_INDEX),
    (PoseLandmark.LEFT_HEEL, PoseLandmark.LEFT_FOOT_INDEX),
    (PoseLandmark.RIGHT_ANKLE, PoseLandmark.RIGHT_HEEL),
    (PoseLandmark.RIGHT_ANKLE, PoseLandmark.RIGHT_FOOT_INDEX),
    (PoseLandmark.RIGHT_HEEL, PoseLandmark.RIGHT_FOOT_INDEX),
]

# Clinically relevant joint angle definitions
# Each tuple: (point_a, vertex, point_b) - angle measured at vertex
JOINT_ANGLES = {
    "右肘 (R.Elbow)": (
        PoseLandmark.RIGHT_SHOULDER,
        PoseLandmark.RIGHT_ELBOW,
        PoseLandmark.RIGHT_WRIST,
    ),
    "左肘 (L.Elbow)": (
        PoseLandmark.LEFT_SHOULDER,
        PoseLandmark.LEFT_ELBOW,
        PoseLandmark.LEFT_WRIST,
    ),
    "右肩 (R.Shoulder)": (
        PoseLandmark.RIGHT_ELBOW,
        PoseLandmark.RIGHT_SHOULDER,
        PoseLandmark.RIGHT_HIP,
    ),
    "左肩 (L.Shoulder)": (
        PoseLandmark.LEFT_ELBOW,
        PoseLandmark.LEFT_SHOULDER,
        PoseLandmark.LEFT_HIP,
    ),
    "右股関節 (R.Hip)": (
        PoseLandmark.RIGHT_SHOULDER,
        PoseLandmark.RIGHT_HIP,
        PoseLandmark.RIGHT_KNEE,
    ),
    "左股関節 (L.Hip)": (
        PoseLandmark.LEFT_SHOULDER,
        PoseLandmark.LEFT_HIP,
        PoseLandmark.LEFT_KNEE,
    ),
    "右膝 (R.Knee)": (
        PoseLandmark.RIGHT_HIP,
        PoseLandmark.RIGHT_KNEE,
        PoseLandmark.RIGHT_ANKLE,
    ),
    "左膝 (L.Knee)": (
        PoseLandmark.LEFT_HIP,
        PoseLandmark.LEFT_KNEE,
        PoseLandmark.LEFT_ANKLE,
    ),
    "体幹側屈 (Trunk Lat.)": (
        PoseLandmark.LEFT_SHOULDER,
        PoseLandmark.LEFT_HIP,
        PoseLandmark.RIGHT_HIP,
    ),
    "頭部傾斜 (Head Tilt)": (
        PoseLandmark.LEFT_EAR,
        PoseLandmark.NOSE,
        PoseLandmark.RIGHT_EAR,
    ),
}

# Body segment vectors for orientation comparison
BODY_SEGMENTS = {
    "脊柱 (Spine)": (
        PoseLandmark.LEFT_HIP,
        PoseLandmark.RIGHT_HIP,
        PoseLandmark.LEFT_SHOULDER,
        PoseLandmark.RIGHT_SHOULDER,
    ),
    "骨盤 (Pelvis)": (
        PoseLandmark.LEFT_HIP,
        PoseLandmark.RIGHT_HIP,
    ),
    "肩ライン (Shoulder Line)": (
        PoseLandmark.LEFT_SHOULDER,
        PoseLandmark.RIGHT_SHOULDER,
    ),
}


@dataclass
class AngleComparison:
    """Result of comparing a joint angle between reference and target."""

    name: str
    ref_angle: float
    target_angle: float
    difference: float
    severity: str  # "good", "warning", "critical"
    correction_text: str


@dataclass
class PoseResult:
    """Complete pose detection result."""

    landmarks: list
    image_with_pose: np.ndarray
    angles: dict
    detected: bool


def calculate_angle(a: np.ndarray, b: np.ndarray, c: np.ndarray) -> float:
    """Calculate angle at point b given three 2D/3D points."""
    ba = a - b
    bc = c - b
    cosine = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-8)
    cosine = np.clip(cosine, -1.0, 1.0)
    return math.degrees(math.acos(cosine))


def calculate_segment_angle(p1: np.ndarray, p2: np.ndarray) -> float:
    """Calculate angle of a segment relative to horizontal."""
    delta = p2 - p1
    return math.degrees(math.atan2(delta[1], delta[0]))


def _draw_pose_on_image(
    image: np.ndarray,
    landmarks: list,
    color: tuple = (0, 255, 0),
    thickness: int = 2,
    visibility_threshold: float = 0.3,
) -> np.ndarray:
    """Draw pose landmarks and connections on an image (only visible ones)."""
    h, w = image.shape[:2]
    annotated = image.copy()

    # Draw connections (only if both endpoints are visible)
    for start_lm, end_lm in POSE_CONNECTIONS:
        start = landmarks[int(start_lm)]
        end = landmarks[int(end_lm)]
        if not (_is_landmark_visible(start, visibility_threshold) and
                _is_landmark_visible(end, visibility_threshold)):
            continue
        pt1 = (int(start.x * w), int(start.y * h))
        pt2 = (int(end.x * w), int(end.y * h))
        cv2.line(annotated, pt1, pt2, color, thickness)

    # Draw landmarks (only visible ones)
    for lm in landmarks:
        if not _is_landmark_visible(lm, visibility_threshold):
            continue
        pt = (int(lm.x * w), int(lm.y * h))
        cv2.circle(annotated, pt, 4, color, -1)

    return annotated


def _is_landmark_visible(landmark, threshold: float = 0.3) -> bool:
    """Check if a landmark has sufficient visibility/presence confidence."""
    vis = getattr(landmark, "visibility", 1.0)
    presence = getattr(landmark, "presence", 1.0)
    if vis is None:
        vis = 1.0
    if presence is None:
        presence = 1.0
    return vis > threshold and presence > threshold


def detect_pose(
    image: np.ndarray,
    detection_confidence: float = 0.3,
    visibility_threshold: float = 0.3,
) -> PoseResult:
    """Detect pose landmarks in an image using MediaPipe PoseLandmarker.

    Supports partial body detection (e.g., only upper body visible in CT).
    Landmarks with low visibility are excluded from angle calculations.

    Args:
        image: Input BGR image.
        detection_confidence: Min confidence for pose detection (lower = more
            lenient for partial body).
        visibility_threshold: Min visibility score to include a landmark in
            angle calculations.
    """
    _ensure_model()
    options = vision.PoseLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=MODEL_PATH),
        num_poses=1,
        min_pose_detection_confidence=detection_confidence,
        min_pose_presence_confidence=detection_confidence,
    )

    with vision.PoseLandmarker.create_from_options(options) as landmarker:
        # Convert BGR to RGB for MediaPipe
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=image_rgb)

        result = landmarker.detect(mp_image)

        if not result.pose_landmarks or len(result.pose_landmarks) == 0:
            return PoseResult(
                landmarks=[],
                image_with_pose=image.copy(),
                angles={},
                detected=False,
            )

        landmarks = result.pose_landmarks[0]  # First person

        # Draw pose on image (only visible landmarks)
        annotated = _draw_pose_on_image(
            image, landmarks, visibility_threshold=visibility_threshold
        )

        # Calculate joint angles (only if all three landmarks are visible)
        angles = {}
        for name, (pt_a, vertex, pt_b) in JOINT_ANGLES.items():
            lm_a = landmarks[int(pt_a)]
            lm_b = landmarks[int(vertex)]
            lm_c = landmarks[int(pt_b)]

            if not all(
                _is_landmark_visible(lm, visibility_threshold)
                for lm in [lm_a, lm_b, lm_c]
            ):
                continue  # Skip angles where landmarks are not reliably visible

            a = np.array([lm_a.x, lm_a.y])
            b = np.array([lm_b.x, lm_b.y])
            c = np.array([lm_c.x, lm_c.y])
            angles[name] = calculate_angle(a, b, c)

        # Calculate segment orientations (only if landmarks are visible)
        for name, pts in BODY_SEGMENTS.items():
            if len(pts) == 2:
                lm1 = landmarks[int(pts[0])]
                lm2 = landmarks[int(pts[1])]
                if not all(
                    _is_landmark_visible(lm, visibility_threshold)
                    for lm in [lm1, lm2]
                ):
                    continue
                p1 = np.array([lm1.x, lm1.y])
                p2 = np.array([lm2.x, lm2.y])
                angles[f"{name}_orientation"] = calculate_segment_angle(p1, p2)
            elif len(pts) == 4:
                lms = [landmarks[int(p)] for p in pts]
                if not all(
                    _is_landmark_visible(lm, visibility_threshold)
                    for lm in lms
                ):
                    continue
                mid1 = np.array([
                    (lms[0].x + lms[1].x) / 2,
                    (lms[0].y + lms[1].y) / 2,
                ])
                mid2 = np.array([
                    (lms[2].x + lms[3].x) / 2,
                    (lms[2].y + lms[3].y) / 2,
                ])
                angles[f"{name}_orientation"] = calculate_segment_angle(mid1, mid2)

        return PoseResult(
            landmarks=landmarks,
            image_with_pose=annotated,
            angles=angles,
            detected=True,
        )


def compare_poses(
    ref_result: PoseResult,
    target_result: PoseResult,
    threshold_warning: float = 5.0,
    threshold_critical: float = 10.0,
) -> list[AngleComparison]:
    """Compare joint angles between reference and target poses."""
    comparisons = []

    for name in ref_result.angles:
        if name not in target_result.angles:
            continue

        ref_angle = ref_result.angles[name]
        target_angle = target_result.angles[name]
        diff = target_angle - ref_angle

        abs_diff = abs(diff)
        if abs_diff < threshold_warning:
            severity = "good"
        elif abs_diff < threshold_critical:
            severity = "warning"
        else:
            severity = "critical"

        # Generate correction instruction
        if "_orientation" in name:
            base_name = name.replace("_orientation", "")
            if abs_diff < threshold_warning:
                correction = "✓ 良好（許容範囲内）"
            elif diff > 0:
                correction = f"{base_name}を {abs_diff:.1f}° 反時計回りに回転"
            else:
                correction = f"{base_name}を {abs_diff:.1f}° 時計回りに回転"
        else:
            if abs_diff < threshold_warning:
                correction = "✓ 良好（許容範囲内）"
            elif diff > 0:
                correction = f"{abs_diff:.1f}° 閉じる方向に修正"
            else:
                correction = f"{abs_diff:.1f}° 開く方向に修正"

        comparisons.append(
            AngleComparison(
                name=name,
                ref_angle=ref_angle,
                target_angle=target_angle,
                difference=diff,
                severity=severity,
                correction_text=correction,
            )
        )

    return comparisons


def draw_comparison_overlay(
    target_image: np.ndarray,
    ref_result: PoseResult,
    target_result: PoseResult,
    comparisons: list[AngleComparison],
    visibility_threshold: float = 0.3,
) -> np.ndarray:
    """Draw correction arrows and annotations on the target image."""
    overlay = target_image.copy()
    h, w = overlay.shape[:2]

    if not target_result.detected or not ref_result.detected:
        cv2.putText(
            overlay,
            "Pose not detected",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.0,
            (0, 0, 255),
            2,
        )
        return overlay

    ref_landmarks = ref_result.landmarks
    tgt_landmarks = target_result.landmarks

    # Draw reference pose as ghost overlay (semi-transparent blue, visible only)
    ghost = overlay.copy()
    for start_lm, end_lm in POSE_CONNECTIONS:
        start = ref_landmarks[int(start_lm)]
        end = ref_landmarks[int(end_lm)]
        if not (_is_landmark_visible(start, visibility_threshold) and
                _is_landmark_visible(end, visibility_threshold)):
            continue
        pt1 = (int(start.x * w), int(start.y * h))
        pt2 = (int(end.x * w), int(end.y * h))
        cv2.line(ghost, pt1, pt2, (255, 150, 0), 2)  # Blue for reference

    cv2.addWeighted(ghost, 0.4, overlay, 0.6, 0, overlay)

    # Draw target pose (visible landmarks only)
    for start_lm, end_lm in POSE_CONNECTIONS:
        start = tgt_landmarks[int(start_lm)]
        end = tgt_landmarks[int(end_lm)]
        if not (_is_landmark_visible(start, visibility_threshold) and
                _is_landmark_visible(end, visibility_threshold)):
            continue
        pt1 = (int(start.x * w), int(start.y * h))
        pt2 = (int(end.x * w), int(end.y * h))
        cv2.line(overlay, pt1, pt2, (0, 255, 0), 2)  # Green for target

    # Draw correction arrows for critical/warning joints
    for comp in comparisons:
        if comp.severity == "good" or "_orientation" in comp.name:
            continue

        if comp.name in JOINT_ANGLES:
            _, vertex_lm, _ = JOINT_ANGLES[comp.name]
            vertex = tgt_landmarks[int(vertex_lm)]
            pt = (int(vertex.x * w), int(vertex.y * h))

            color = (0, 165, 255) if comp.severity == "warning" else (0, 0, 255)

            # Draw a circle at the joint
            cv2.circle(overlay, pt, 8, color, -1)

            # Add text showing the angle difference
            text_pt = (pt[0] + 10, pt[1] - 10)
            cv2.putText(
                overlay,
                f"{comp.difference:+.1f}",
                text_pt,
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                color,
                2,
            )

    return overlay


def create_side_by_side(
    ref_image: np.ndarray,
    target_image: np.ndarray,
    ref_result: PoseResult,
    target_result: PoseResult,
) -> np.ndarray:
    """Create a side-by-side comparison image."""
    h1, w1 = ref_image.shape[:2]
    h2, w2 = target_image.shape[:2]

    # Resize to same height
    target_h = max(h1, h2)
    scale1 = target_h / h1
    scale2 = target_h / h2
    ref_resized = cv2.resize(ref_image, (int(w1 * scale1), target_h))
    tgt_resized = cv2.resize(target_image, (int(w2 * scale2), target_h))

    # Add labels
    cv2.putText(
        ref_resized,
        "REFERENCE (CT position)",
        (10, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (255, 200, 0),
        2,
    )
    cv2.putText(
        tgt_resized,
        "TARGET (Current)",
        (10, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (0, 255, 0),
        2,
    )

    combined = np.hstack([ref_resized, tgt_resized])
    return combined
