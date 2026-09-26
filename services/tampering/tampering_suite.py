from typing import Dict, Any, List
from .ela_analyzer import ErrorLevelAnalysis
from .copy_move import CopyMoveDetector
from .font_consistency import FontConsistencyAnalyzer
from .cnn_classifier import CNNTamperClassifier

class TamperingSuite:
    """
    Stage 4 Multi-Layer Tampering Detection Suite:
    Fuses ELA, Copy-Move, Font-Consistency, and CNN Classifier results.
    """

    def __init__(self):
        self.cnn_classifier = CNNTamperClassifier()

    def run_all(self, image_bytes: bytes) -> Dict[str, Any]:
        flags: List[Dict[str, Any]] = []

        # 1. Error Level Analysis
        ela_res = ErrorLevelAnalysis.analyze(image_bytes)
        if ela_res.get("tamper_detected"):
            flags.append({
                "module": "tampering_detection",
                "check": "error_level_analysis",
                "triggered": True,
                "severity": "HIGH",
                "score": ela_res.get("score", 0.0),
                "detail": f"ELA flagged localized compression anomaly (Score: {ela_res.get('score')}). {ela_res.get('summary')}"
            })

        # 2. Copy-Move Forgery Check
        copy_res = CopyMoveDetector.detect(image_bytes)
        if copy_res.get("tamper_detected"):
            flags.append({
                "module": "tampering_detection",
                "check": "copy_move_forgery",
                "triggered": True,
                "severity": "HIGH",
                "score": copy_res.get("score", 0.0),
                "detail": f"Copy-Move detected {copy_res.get('matched_pairs')} duplicated keypoint clusters."
            })

        # 3. Font & Glyph Typography Consistency
        font_res = FontConsistencyAnalyzer.analyze(image_bytes)
        if font_res.get("tamper_detected"):
            flags.append({
                "module": "tampering_detection",
                "check": "font_consistency",
                "triggered": True,
                "severity": "MEDIUM",
                "score": font_res.get("score", 0.0),
                "detail": f"Font metrics disparity detected across text fields (Aspect std: {font_res.get('aspect_ratio_std')})."
            })

        # 4. CNN Tamper Probability Classifier
        cnn_res = self.cnn_classifier.predict_tamper_probability(image_bytes)
        if cnn_res.get("tamper_detected"):
            flags.append({
                "module": "tampering_detection",
                "check": "cnn_tamper_classifier",
                "triggered": True,
                "severity": "MEDIUM",
                "score": cnn_res.get("probability", 0.0),
                "detail": f"CNN tamper probability: {cnn_res.get('probability')}"
            })

        # Weighted Tampering Composite Score:
        # ELA: 35%, Copy-Move: 30%, Font: 20%, CNN: 15%
        comp_score = (
            ela_res.get("score", 0.0) * 0.35 +
            copy_res.get("score", 0.0) * 0.30 +
            font_res.get("score", 0.0) * 0.20 +
            cnn_res.get("probability", 0.0) * 0.15
        )

        return {
            "overall_tamper_score": round(comp_score, 3),
            "tamper_detected": len(flags) > 0,
            "flags": flags,
            "components": {
                "ela": ela_res,
                "copy_move": copy_res,
                "font_consistency": font_res,
                "cnn_classifier": cnn_res
            }
        }
