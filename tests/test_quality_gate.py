import pytest
import numpy as np
import cv2
from services.quality_gate.quality_checker import QualityGateService

def test_quality_gate_clean_image():
    # Generate sharp synthetic image
    img = np.zeros((400, 600, 3), dtype=np.uint8) + 120
    # Add sharp text patterns
    cv2.putText(img, "PASSPORT REPUBLIC OF INDIA", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 0), 2)
    cv2.rectangle(img, (50, 150), (300, 350), (255, 255, 255), -1)
    
    _, enc = cv2.imencode('.png', img)
    checker = QualityGateService(blur_threshold=50.0)
    res = checker.assess_image(enc.tobytes(), "test_doc")

    assert res["passed"] is True
    assert res["blur_score"] > 0.0
    assert len(res["issues"]) == 0

def test_quality_gate_blurred_image():
    # Generate completely uniform/blurred image
    img = np.zeros((400, 600, 3), dtype=np.uint8) + 120
    _, enc = cv2.imencode('.png', img)
    
    checker = QualityGateService(blur_threshold=50.0)
    res = checker.assess_image(enc.tobytes(), "test_blur")

    assert res["passed"] is False
    assert any("blurry" in issue.lower() for issue in res["issues"])
