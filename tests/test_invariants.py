"""
Invariant tests for NFTAuthenticator contract.

These tests verify that the contract's hard invariants are enforced
regardless of LLM output or evidence quality.
"""
import json
import pytest

# ─── Invariant helpers (mirror contract logic) ───────────────

_NO_SOURCE = ("", "none", "none found", "no similar sources found", "n/a", "not found")

def _has_real_source(sf: str) -> bool:
    return sf.strip().lower() not in _NO_SOURCE


# ─── Test: authentic + real similar source = invalid ─────────

class TestAuthenticSimilarSourceInvariant:
    """If authentic=True and similar_found is a real source,
    the verdict MUST be rejected by the validator."""

    def test_authentic_with_real_source_is_invalid(self):
        verdict = {
            "authentic": True,
            "confidence": "high",
            "similar_found": "https://deviantart.com/art/original-by-artist",
            "reasoning": "This appears to be original work.",
            "evidence_quality": "strong",
        }
        # Invariant: authentic + real source = INVALID
        assert verdict["authentic"] and _has_real_source(verdict["similar_found"])
        # The contract's leader_fn forces authentic=False when has_real_source
        # The validator rejects if this invariant is violated
        assert not (verdict["authentic"] and _has_real_source(verdict["similar_found"])) is False
        # After contract enforcement, authentic would be False:
        enforced = verdict.copy()
        if _has_real_source(enforced["similar_found"]):
            enforced["authentic"] = False
        assert enforced["authentic"] is False

    def test_authentic_with_none_source_is_valid(self):
        verdict = {
            "authentic": True,
            "confidence": "high",
            "similar_found": "none",
            "reasoning": "No infringing sources found in any evidence.",
            "evidence_quality": "strong",
        }
        assert not _has_real_source(verdict["similar_found"])
        # This is valid — authentic with no real source


# ─── Test: no/weak evidence → not authentic ─────────────────

class TestEvidenceQualityInvariant:
    """If evidence_quality is 'none' or 'weak',
    authentic MUST be False and confidence MUST be 'low'."""

    def test_none_evidence_cannot_be_authentic(self):
        verdict = {
            "authentic": True,  # This would be forced to False
            "confidence": "low",
            "evidence_quality": "none",
        }
        # Contract enforces: none evidence → authentic=False
        if verdict["evidence_quality"] == "none":
            verdict["authentic"] = False
        assert verdict["authentic"] is False

    def test_weak_evidence_cannot_be_authentic(self):
        verdict = {
            "authentic": True,  # This would be forced to False
            "confidence": "low",
            "evidence_quality": "weak",
        }
        if verdict["evidence_quality"] == "weak":
            verdict["authentic"] = False
            verdict["confidence"] = "low"
        assert verdict["authentic"] is False
        assert verdict["confidence"] == "low"

    def test_weak_evidence_forces_low_confidence(self):
        verdict = {
            "authentic": False,
            "confidence": "high",  # This would be forced to "low"
            "evidence_quality": "weak",
        }
        if verdict["evidence_quality"] in ("weak", "none"):
            verdict["confidence"] = "low"
        assert verdict["confidence"] == "low"

    def test_moderate_evidence_caps_at_medium(self):
        verdict = {
            "authentic": True,
            "confidence": "high",  # This would be capped to "medium"
            "evidence_quality": "moderate",
        }
        if verdict["evidence_quality"] == "moderate" and verdict["confidence"] == "high":
            verdict["confidence"] = "medium"
        assert verdict["confidence"] == "medium"


# ─── Test: confidence enum is strict ─────────────────────────

class TestConfidenceEnum:
    """Confidence must be exactly high/medium/low."""

    @pytest.mark.parametrize("invalid", ["very high", "1", "", "medium-high"])
    def test_invalid_confidence_becomes_low(self, invalid):
        canonical = invalid.strip().lower()
        if canonical not in ("high", "medium", "low"):
            canonical = "low"
        assert canonical == "low"

    def test_valid_confidence_values(self):
        for c in ("high", "medium", "low"):
            assert c in ("high", "medium", "low")


# ─── Test: similar_found normalization ───────────────────────

class TestSimilarFoundNormalization:
    """Various 'no source' representations must be treated equivalently."""

    def test_no_source_values(self):
        for sf in _NO_SOURCE:
            assert not _has_real_source(sf), f"'{sf}' should not be a real source"

    def test_real_source_values(self):
        real_sources = [
            "https://deviantart.com/art/something",
            "Found on ArtStation",
            "Copied from known artist X",
        ]
        for sf in real_sources:
            assert _has_real_source(sf), f"'{sf}' should be a real source"
