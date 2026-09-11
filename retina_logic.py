from PIL import Image
import numpy as np


# =========================================================
# LOAD AND PREPARE IMAGE
# =========================================================

def _load_and_prep(image_path, size=512):

    try:
        img = Image.open(image_path).convert("RGB")
    except Exception:
        raise ValueError(
            "Please upload a valid retinal fundus image."
        )

    width, height = img.size

    if width < 200 or height < 200:
        raise ValueError(
            "Please upload a valid retinal fundus image. "
            "The image resolution is too low."
        )

    img = img.resize((size, size))

    arr = np.array(img).astype(np.float32)

    return arr


# =========================================================
# FUNDUS IMAGE VALIDATION
# =========================================================

def _validate_fundus_image(arr):

    h, w, _ = arr.shape

    R = arr[:, :, 0]
    G = arr[:, :, 1]
    B = arr[:, :, 2]

    brightness = (R + G + B) / 3.0

    # -----------------------------------------------------
    # 1. Aspect ratio
    # -----------------------------------------------------

    aspect_ratio = w / float(h)

    if aspect_ratio > 1.45 or aspect_ratio < 0.68:
        return False

    # -----------------------------------------------------
    # 2. Dark border
    # -----------------------------------------------------

    border = np.concatenate([
        brightness[:40, :].flatten(),
        brightness[-40:, :].flatten(),
        brightness[:, :40].flatten(),
        brightness[:, -40:].flatten()
    ])

    dark_border_ratio = np.mean(
        border < 75
    )

    border_ok = dark_border_ratio > 0.18

    # -----------------------------------------------------
    # 3. Center retinal content
    # -----------------------------------------------------

    center = brightness[
        int(h * 0.20):int(h * 0.80),
        int(w * 0.20):int(w * 0.80)
    ]

    center_mean = float(
        np.mean(center)
    )

    center_std = float(
        np.std(center)
    )

    center_ok = (
        center_mean > 45
        and center_std > 12
    )

    # -----------------------------------------------------
    # 4. Red / orange fundus characteristics
    # -----------------------------------------------------

    red_dominance = np.mean(
        (R > G + 8) &
        (R > B + 12)
    )

    warm_color_ok = (
        red_dominance > 0.12
    )

    # -----------------------------------------------------
    # 5. Texture
    # -----------------------------------------------------

    gy, gx = np.gradient(G)

    edge_strength = np.sqrt(
        gx ** 2 +
        gy ** 2
    )

    texture_ratio = np.mean(
        edge_strength > 18
    )

    texture_ok = (
        texture_ratio > 0.025
    )

    # -----------------------------------------------------
    # 6. White background detection
    # -----------------------------------------------------

    white_ratio = np.mean(
        (R > 220) &
        (G > 220) &
        (B > 220)
    )

    white_background_ok = (
        white_ratio < 0.55
    )

    # -----------------------------------------------------
    # 7. Useful image content
    # -----------------------------------------------------

    useful_pixels = np.mean(
        brightness > 25
    )

    useful_content_ok = (
        useful_pixels > 0.35
    )

    # -----------------------------------------------------
    # FINAL VALIDATION
    # -----------------------------------------------------

    checks = [
        border_ok,
        center_ok,
        warm_color_ok,
        texture_ok,
        white_background_ok,
        useful_content_ok
    ]

    passed = sum(checks)

    # Require at least 5/6 checks
    return passed >= 5


# =========================================================
# RETINA MASK
# =========================================================

def _retina_mask(arr):

    brightness = (
        arr[:, :, 0]
        + arr[:, :, 1]
        + arr[:, :, 2]
    ) / 3.0

    mask = brightness > 20

    return mask


# =========================================================
# HEMORRHAGE DETECTION
# =========================================================

def _detect_hemorrhages(arr, mask):

    R = arr[:, :, 0]
    G = arr[:, :, 1]
    B = arr[:, :, 2]

    brightness = (
        R + G + B
    ) / 3.0

    red_dominant = (
        (R - G > 25)
        &
        (R - B > 25)
    )

    dark_enough = (
        brightness < 90
    )

    hemorrhage_pixels = (
        red_dominant
        &
        dark_enough
        &
        mask
    )

    total_retina_pixels = mask.sum()

    if total_retina_pixels:
        ratio = (
            hemorrhage_pixels.sum()
            / total_retina_pixels
        )
    else:
        ratio = 0

    return float(ratio)


# =========================================================
# EXUDATE DETECTION
# =========================================================

def _detect_exudates(arr, mask):

    R = arr[:, :, 0]
    G = arr[:, :, 1]
    B = arr[:, :, 2]

    brightness = (
        R + G + B
    ) / 3.0

    yellow_white = (
        (R > 180)
        &
        (G > 160)
        &
        (B < R - 20)
    )

    bright_enough = (
        brightness > 150
    )

    exudate_pixels = (
        yellow_white
        &
        bright_enough
        &
        mask
    )

    total_retina_pixels = mask.sum()

    if total_retina_pixels:
        ratio = (
            exudate_pixels.sum()
            / total_retina_pixels
        )
    else:
        ratio = 0

    return float(ratio)


# =========================================================
# VESSEL IRREGULARITY
# =========================================================

def _detect_vessel_irregularity(arr, mask):

    G = arr[:, :, 1]

    gy, gx = np.gradient(G)

    edge_strength = np.sqrt(
        gx ** 2 +
        gy ** 2
    )

    strong_edges = (
        edge_strength > 40
    ) & mask

    total_retina_pixels = mask.sum()

    if total_retina_pixels:
        ratio = (
            strong_edges.sum()
            / total_retina_pixels
        )
    else:
        ratio = 0

    return float(ratio)


# =========================================================
# SCREENING SCORE
# =========================================================

def _calculate_screening_score(
    hemorrhage_ratio,
    exudate_ratio,
    vessel_ratio
):

    # -----------------------------------------------------
    # Hemorrhage contribution
    # -----------------------------------------------------

    hemorrhage_score = min(
        hemorrhage_ratio / 0.008,
        1.0
    )

    # -----------------------------------------------------
    # Exudate contribution
    # -----------------------------------------------------

    exudate_score = min(
        exudate_ratio / 0.015,
        1.0
    )

    # -----------------------------------------------------
    # Vessel contribution
    # -----------------------------------------------------

    vessel_score = min(
        max(
            (vessel_ratio - 0.055) / 0.12,
            0.0
        ),
        1.0
    )

    # -----------------------------------------------------
    # Weighted score
    # -----------------------------------------------------

    dr_score = (
        hemorrhage_score * 0.45
        +
        exudate_score * 0.40
        +
        vessel_score * 0.15
    )

    dr_likelihood = (
        dr_score * 100
    )

    return round(
        dr_likelihood,
        2
    )


# =========================================================
# CONFIDENCE
# =========================================================

def _calculate_confidence(
    dr_likelihood,
    threshold
):

    if dr_likelihood >= threshold:

        confidence = (
            58
            +
            (dr_likelihood - threshold)
            * 0.65
        )

    else:

        confidence = (
            58
            +
            (threshold - dr_likelihood)
            * 0.75
        )

    # Keep confidence in a reasonable
    # prototype/demo range.

    confidence = min(
        max(confidence, 55),
        94
    )

    return round(
        confidence,
        1
    )


# =========================================================
# MAIN RETINAL ANALYSIS
# =========================================================

def analyze_retina(image_path):

    # -----------------------------------------------------
    # LOAD IMAGE
    # -----------------------------------------------------

    arr = _load_and_prep(
        image_path
    )

    # -----------------------------------------------------
    # VALIDATE FUNDUS IMAGE
    # -----------------------------------------------------

    if not _validate_fundus_image(arr):

        raise ValueError(
            "Please upload a valid retinal fundus image. "
            "The uploaded image does not appear to be an "
            "eye/fundus photograph."
        )

    # -----------------------------------------------------
    # CREATE RETINAL MASK
    # -----------------------------------------------------

    mask = _retina_mask(
        arr
    )

    # -----------------------------------------------------
    # DETECT FEATURES
    # -----------------------------------------------------

    hemorrhage_ratio = (
        _detect_hemorrhages(
            arr,
            mask
        )
    )

    exudate_ratio = (
        _detect_exudates(
            arr,
            mask
        )
    )

    vessel_ratio = (
        _detect_vessel_irregularity(
            arr,
            mask
        )
    )

    # -----------------------------------------------------
    # CALCULATE SCREENING SCORE
    # -----------------------------------------------------

    dr_likelihood = (
        _calculate_screening_score(
            hemorrhage_ratio,
            exudate_ratio,
            vessel_ratio
        )
    )

    # -----------------------------------------------------
    # SCREENING THRESHOLD
    # -----------------------------------------------------

    THRESHOLD = 42.0

    # -----------------------------------------------------
    # FINDINGS
    # -----------------------------------------------------

    findings = []

    if hemorrhage_ratio > 0.001:

        findings.append(
            "dark hemorrhage/microaneurysm-like spots"
        )

    if exudate_ratio > 0.001:

        findings.append(
            "bright exudate-like patches"
        )

    if vessel_ratio > 0.05:

        findings.append(
            "irregular vessel contrast patterns"
        )

    # -----------------------------------------------------
    # DETERMINE RESULT
    # -----------------------------------------------------

    if dr_likelihood >= THRESHOLD:

        result = (
            "Diabetic Retinopathy Detected"
        )

        confidence = (
            _calculate_confidence(
                dr_likelihood,
                THRESHOLD
            )
        )

        if findings:

            explanation = (
                "Detected "
                + ", ".join(findings)
                + " consistent with diabetic "
                  "retinopathy screening indicators."
            )

        else:

            explanation = (
                "The retinal image contains visual "
                "patterns that crossed the screening "
                "threshold and require further clinical "
                "review."
            )

    else:

        result = (
            "Healthy Retina"
        )

        confidence = (
            _calculate_confidence(
                dr_likelihood,
                THRESHOLD
            )
        )

        if findings:

            explanation = (
                "Minor visual patterns were detected, "
                "but the overall screening score remained "
                "below the diabetic retinopathy threshold."
            )

        else:

            explanation = (
                "No significant hemorrhages, exudates, "
                "or vessel irregularities were detected "
                "by the screening system."
            )

    # -----------------------------------------------------
    # RETURN RESULT
    # -----------------------------------------------------

    return {

        "result": result,

        "confidence": confidence,

        "explanation": explanation,

        "details": {

            "hemorrhage_ratio": round(
                hemorrhage_ratio,
                5
            ),

            "exudate_ratio": round(
                exudate_ratio,
                5
            ),

            "vessel_irregularity_ratio": round(
                vessel_ratio,
                5
            ),

            "dr_likelihood_score": round(
                dr_likelihood,
                2
            )
        }
    }