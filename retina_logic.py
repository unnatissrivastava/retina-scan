"""
RetinaScan AI - Formula-based Diabetic Retinopathy Detection
--------------------------------------------------------------
NO external API, NO OpenCV, NO trained ML model.
Pure pixel-math using Pillow + NumPy.
 
Logic:
1. Load fundus image, resize to a fixed size for consistent scoring.
2. Isolate the circular retina area (ignore black corners/background).
3. Detect "hemorrhage/microaneurysm-like" pixels: dark reddish-brown spots.
4. Detect "exudate-like" pixels: bright yellow-white spots.
5. Compute a weighted score from the % area covered by each.
6. Compare score to a threshold -> Healthy / DR Detected + confidence %.
 
This is a heuristic, not a clinically validated diagnostic tool.
Good enough for a hackathon demo with an "explainable" angle.
"""
 
from PIL import Image
import numpy as np
 
 
def _load_and_prep(image_path, size=512):
    img = Image.open(image_path).convert("RGB")
    img = img.resize((size, size))
    arr = np.array(img).astype(np.int16)  # int16 to avoid uint8 overflow in subtraction
    return arr
 
 
def _retina_mask(arr):
    """
    Fundus photos are usually a circular retina on a black background.
    Mask out near-black background pixels so they don't skew the ratios.
    """
    brightness = arr.sum(axis=2) / 3.0
    mask = brightness > 20  # anything darker than this is treated as background
    return mask
 
 
def _detect_hemorrhages(arr, mask):
    """
    Hemorrhages / microaneurysms: dark reddish-brown blobs.
    Formula: R noticeably higher than G and B, but overall darker
    than the average healthy retina red tone.
    """
    R, G, B = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]
    brightness = (R + G + B) / 3.0
 
    red_dominant = (R - G > 25) & (R - B > 25)
    dark_enough = brightness < 90
    hemorrhage_pixels = red_dominant & dark_enough & mask
 
    total_retina_pixels = mask.sum()
    ratio = hemorrhage_pixels.sum() / total_retina_pixels if total_retina_pixels else 0
    return ratio, hemorrhage_pixels
 
 
def _detect_exudates(arr, mask):
    """
    Exudates: bright yellow-white patches.
    Formula: R and G both high (yellow), B relatively lower,
    and overall brightness clearly above the retina's average.
    """
    R, G, B = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]
    brightness = (R + G + B) / 3.0
 
    yellow_white = (R > 180) & (G > 160) & (B < R - 20)
    bright_enough = brightness > 150
    exudate_pixels = yellow_white & bright_enough & mask
 
    total_retina_pixels = mask.sum()
    ratio = exudate_pixels.sum() / total_retina_pixels if total_retina_pixels else 0
    return ratio, exudate_pixels
 
 
def _detect_vessel_irregularity(arr, mask):
    """
    Rough proxy for abnormal/tortuous vessels: high local contrast
    in the green channel (vessels show up best in green).
    Formula: fraction of pixels that are strong local edges.
    """
    G = arr[:, :, 1].astype(np.float32)
    gy, gx = np.gradient(G)
    edge_strength = np.sqrt(gx ** 2 + gy ** 2)
    strong_edges = (edge_strength > 40) & mask
 
    total_retina_pixels = mask.sum()
    ratio = strong_edges.sum() / total_retina_pixels if total_retina_pixels else 0
    return ratio
 
 
def analyze_retina(image_path):
    """
    Main entry point. Returns a dict:
    {
        "result": "Healthy Retina" | "Diabetic Retinopathy Detected",
        "confidence": float (0-100),
        "explanation": str,
        "details": {...}   # raw ratios, useful for debugging/demo
    }
    """
    arr = _load_and_prep(image_path)
    mask = _retina_mask(arr)
 
    hemorrhage_ratio, _ = _detect_hemorrhages(arr, mask)
    exudate_ratio, _ = _detect_exudates(arr, mask)
    vessel_ratio = _detect_vessel_irregularity(arr, mask)
 
    # ---- Weighted formula (tune these weights after testing on sample images) ----
    W_HEMORRHAGE = 60.0
    W_EXUDATE = 50.0
    W_VESSEL = 15.0
 
    raw_score = (
        hemorrhage_ratio * W_HEMORRHAGE
        + exudate_ratio * W_EXUDATE
        + vessel_ratio * W_VESSEL
    )
 
    # Normalize score to a 0-100 "DR likelihood" scale
    dr_likelihood = min(raw_score * 100, 100)
 
    THRESHOLD = 8.0  # tune this after testing on real sample fundus images
 
    findings = []
    if hemorrhage_ratio > 0.001:
        findings.append("dark hemorrhage/microaneurysm-like spots")
    if exudate_ratio > 0.001:
        findings.append("bright exudate-like patches")
    if vessel_ratio > 0.05:
        findings.append("irregular vessel contrast patterns")
 
    if dr_likelihood >= THRESHOLD:
        result = "Diabetic Retinopathy Detected"
        confidence = round(min(60 + dr_likelihood, 97), 1)
        if findings:
            explanation = "Detected " + ", ".join(findings) + " consistent with diabetic retinopathy."
        else:
            explanation = "Overall pixel pattern crossed the DR-risk threshold."
    else:
        result = "Healthy Retina"
        confidence = round(min(60 + (THRESHOLD - dr_likelihood) * 4, 97), 1)
        explanation = "No significant hemorrhages, exudates, or vessel irregularities detected."
 
    return {
        "result": result,
        "confidence": confidence,
        "explanation": explanation,
        "details": {
            "hemorrhage_ratio": round(hemorrhage_ratio, 5),
            "exudate_ratio": round(exudate_ratio, 5),
            "vessel_irregularity_ratio": round(vessel_ratio, 5),
            "dr_likelihood_score": round(dr_likelihood, 2),
        },
    }
 
 
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python retina_logic.py <path_to_fundus_image>")
    else:
        result = analyze_retina(sys.argv[1])
        print(result)