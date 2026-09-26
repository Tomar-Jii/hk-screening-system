import cv2
import numpy as np
from PIL import Image, ImageEnhance
import io
import base64
from typing import Dict, Any, Tuple

class ErrorLevelAnalysis:
    """
    Error Level Analysis (ELA):
    Recompresses the image at a standard JPEG quality (90-95%) and takes the absolute
    difference with the original. Spliced or digitally manipulated patches exhibit
    differing error compression levels.
    """

    @staticmethod
    def analyze(image_bytes: bytes, quality: int = 90, scale: int = 15) -> Dict[str, Any]:
        try:
            orig_pil = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            
            # Save to temporary buffer with fixed JPEG quality
            buffer = io.BytesIO()
            orig_pil.save(buffer, 'JPEG', quality=quality)
            buffer.seek(0)
            
            resaved_pil = Image.open(buffer)
            
            # Compute difference
            orig_arr = np.array(orig_pil, dtype=np.float32)
            resaved_arr = np.array(resaved_pil, dtype=np.float32)
            
            diff = np.abs(orig_arr - resaved_arr) * scale
            diff = np.clip(diff, 0, 255).astype(np.uint8)
            
            # Compute statistical metrics
            gray_diff = cv2.cvtColor(diff, cv2.COLOR_RGB2GRAY)
            mean_diff = float(np.mean(gray_diff))
            max_diff = float(np.max(gray_diff))
            std_diff = float(np.std(gray_diff))
            
            # High standard deviation or localized maximum points to potential splicing
            tamper_score = min(1.0, max(0.0, (std_diff / 45.0) * 0.7 + (mean_diff / 30.0) * 0.3))
            is_flagged = tamper_score > 0.45

            # Convert ELA visual to Base64 data URL for frontend rendering
            ela_pil = Image.fromarray(diff)
            out_buf = io.BytesIO()
            ela_pil.save(out_buf, format="JPEG")
            b64_ela = f"data:image/jpeg;base64,{base64.b64encode(out_buf.getvalue()).decode('utf-8')}"

            return {
                "tamper_detected": is_flagged,
                "score": round(tamper_score, 3),
                "mean_error": round(mean_diff, 2),
                "max_error": round(max_diff, 2),
                "std_deviation": round(std_diff, 2),
                "ela_heatmap_b64": b64_ela,
                "summary": "High compression error variance detected; indicates localized digital modification." if is_flagged else "Uniform compression error levels observed across image."
            }
        except Exception as e:
            return {
                "tamper_detected": False,
                "score": 0.0,
                "error": str(e),
                "ela_heatmap_b64": None,
                "summary": f"ELA analysis error: {str(e)}"
            }
