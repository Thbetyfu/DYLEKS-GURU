import os
import sys

# Tambahkan direktori root BE ke sys.path agar pytest dapat menemukan app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.scoring_service import ScoringService

def test_calculate_risk_correct():
    result = ScoringService.calculate_risk("BA", "ba")
    assert result["score"] == 0
    assert len(result["errors"]) == 0

def test_calculate_risk_inversion():
    result = ScoringService.calculate_risk("BA", "da")
    assert result["score"] == 62.0
    assert any("inversi" in err.lower() for err in result["errors"])

def test_calculate_risk_deletion():
    result = ScoringService.calculate_risk("BAN", "ba")
    assert result["score"] == 27.0
    assert any("hilang" in err for err in result["errors"])

def test_calculate_risk_insertion():
    result = ScoringService.calculate_risk("A", "ba")
    assert result["score"] == 40.3
    assert any("tambahan" in err for err in result["errors"])
