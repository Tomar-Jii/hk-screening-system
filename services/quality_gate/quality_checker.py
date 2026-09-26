import cv2
import numpy as np
from typing import Dict, Any, Tuple, Optional
import io
from PIL import Image

class QualityGateService:
    """
    Stage 1: Document & Capture Quality Gate.
    Analyzes uploaded or webcam-captured images for blur (Laplacian variance)
    and exposure anomalies (brightness histogram / mean intensity).
    """

    def __init__(self, blur_threshold: float = 100.0, min_brightness: float = 40.0, max_brightness: float = 220.0):
        self.blur_threshold = blur_threshold
        self.min_brightness = min_brightness
        self.max_brightness = max_brightness

    def assess_image(self, image_bytes: bytes, image_name: str = "document") -> Dict[str, Any]:
        """
        Evaluates raw image bytes and returns structured quality assessment.
        """
        try:
            np_arr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            if img is None:
                return {
                    "passed": False,
                    "target": image_name,
                    "blur_score": 0.0,
                    "brightness_score": 0.0,
                    "issues": ["Unreadable or corrupted image format."],
                    "details": "Failed to decode image buffer."
                }

            # Convert to grayscale for metrics
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            h, w = gray.shape

            # 1. Blur evaluation via Laplacian variance
            laplacian_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
            is_blurry = laplacian_var < self.blur_threshold

            # 2. Brightness evaluation (mean grayscale intensity)
            mean_brightness = float(np.mean(gray))
            is_too_dark = mean_brightness < self.min_brightness
            is_too_bright = mean_brightness > self.max_brightness

            # 3. Resolution sanity check
            is_low_res = (w < 300 or h < 300)

            issues = []
            if is_blurry:
                issues.append(f"Image is blurry (Laplacian variance: {laplacian_var:.1f} < threshold {self.blur_threshold:.1f}).")
            if is_too_dark:
                issues.append(f"Image is underexposed/too dark (Mean brightness: {mean_brightness:.1f} < {self.min_brightness:.1f}).")
            if is_too_bright:
                issues.append(f"Image is overexposed/too bright (Mean brightness: {mean_brightness:.1f} > {self.max_brightness:.1f}).")
            if is_low_res:
                issues.append(f"Low resolution: {w}x{h}px. Minimum recommended is 300x300px.")

            passed = len(issues) == 0

            return {
                "passed": passed,
                "target": image_name,
                "width": w,
                "height": h,
                "blur_score": round(laplacian_var, 2),
                "blur_threshold": self.blur_threshold,
                "brightness_score": round(mean_brightness, 2),
                "brightness_range": [self.min_brightness, self.max_brightness],
                "issues": issues,
                "details": "Quality check passed." if passed else "Quality check failed. Please re-capture or upload a clearer image."
            }
        except Exception as e:
            return {
                "passed": False,
                "target": image_name,
                "blur_score": 0.0,
                "brightness_score": 0.0,
                "issues": [f"Exception during quality analysis: {str(e)}"],
                "details": str(e)
            }
