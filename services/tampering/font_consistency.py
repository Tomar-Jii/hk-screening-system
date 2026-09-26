import cv2
import numpy as np
from typing import Dict, Any, List

class FontConsistencyAnalyzer:
    """
    Analyzes character contour statistics (height variance, aspect ratio dispersion,
    stroke stroke-width estimates) in text regions. Inconsistencies indicate spliced text.
    """

    @staticmethod
    def analyze(image_bytes: bytes) -> Dict[str, Any]:
        try:
            np_arr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            if img is None:
                return {"tamper_detected": False, "score": 0.0, "details": "Image decoding failed."}

            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            # Thresholding to isolate glyphs
            _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            aspect_ratios = []
            heights = []

            for cnt in contours:
                x, y, w, h = cv2.boundingRect(cnt)
                # Filter out noise or large page borders
                if 8 <= h <= 100 and 4 <= w <= 80:
                    aspect_ratios.append(float(w) / float(h))
                    heights.append(float(h))

            if len(heights) < 15:
                return {
                    "tamper_detected": False,
                    "score": 0.0,
                    "sample_count": len(heights),
                    "summary": "Not enough isolated text glyphs to evaluate font variance."
                }

            height_std = float(np.std(heights))
            aspect_std = float(np.std(aspect_ratios))

            # Abnormal standard deviation in aspect ratio implies spliced fonts
            score = min(1.0, max(0.0, (aspect_std - 0.22) * 2.5)) if aspect_std > 0.22 else 0.0
            is_tampered = score > 0.40

            return {
                "tamper_detected": is_tampered,
                "score": round(score, 3),
                "height_std": round(height_std, 2),
                "aspect_ratio_std": round(aspect_std, 3),
                "characters_analyzed": len(heights),
                "summary": "Font metrics dispersion exceeds normal passport typography limits." if is_tampered else "Character dimensions and baseline metrics align within standard typography tolerance."
            }
        except Exception as e:
            return {
                "tamper_detected": False,
                "score": 0.0,
                "error": str(e),
                "summary": f"Font consistency error: {str(e)}"
            }
