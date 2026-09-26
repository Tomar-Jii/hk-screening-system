import cv2
import numpy as np
from typing import Dict, Any, List, Tuple

class CopyMoveDetector:
    """
    Detects copy-move forgery (cloning of text digits, stamps, or security patterns)
    using ORB/SIFT keypoints and spatial distance filtering.
    """

    @staticmethod
    def detect(image_bytes: bytes, min_match_distance: float = 40.0) -> Dict[str, Any]:
        try:
            np_arr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            if img is None:
                return {"tamper_detected": False, "score": 0.0, "details": "Image decoding failed."}

            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Use ORB feature extractor
            orb = cv2.ORB_create(nfeatures=1500)
            keypoints, descriptors = orb.detectAndCompute(gray, None)

            if descriptors is None or len(keypoints) < 10:
                return {
                    "tamper_detected": False,
                    "score": 0.0,
                    "matched_pairs": 0,
                    "summary": "Insufficient keypoints found for copy-move comparison."
                }

            # Brute Force Matcher with Hamming distance
            bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)
            matches = bf.knnMatch(descriptors, descriptors, k=3)

            valid_cloned_pairs = 0
            # Filter matches: match[0] is self-match. Look at match[1] and match[2]
            for m in matches:
                if len(m) >= 2:
                    m1 = m[1]
                    pt1 = keypoints[m1.queryIdx].pt
                    pt2 = keypoints[m1.trainIdx].pt

                    # Spatial distance between matched keypoints
                    dist = np.sqrt((pt1[0] - pt2[0])**2 + (pt1[1] - pt2[1])**2)
                    
                    # If descriptor distance is low but physical distance is sufficiently far
                    if m1.distance < 35 and dist > min_match_distance:
                        valid_cloned_pairs += 1

            # Determine tampering confidence
            score = min(1.0, valid_cloned_pairs / 25.0)
            is_tampered = valid_cloned_pairs >= 12

            return {
                "tamper_detected": is_tampered,
                "score": round(score, 3),
                "matched_pairs": valid_cloned_pairs,
                "summary": f"Detected {valid_cloned_pairs} non-local duplicated keypoints (probable cloned stamp or number)." if is_tampered else f"Low keypoint duplication ({valid_cloned_pairs} pairs)."
            }
        except Exception as e:
            return {
                "tamper_detected": False,
                "score": 0.0,
                "error": str(e),
                "summary": f"Copy-move detector encountered error: {str(e)}"
            }
