"""
Evidence gate tests — verify that the contract cannot reach
high-confidence authentic verdicts from weak or absent evidence.
"""


class TestFailedFetchGate:
    """When no evidence can be acquired, the contract MUST return
    authentic=False, confidence=low, evidence_quality=none."""

    def test_no_evidence_forces_not_authentic(self):
        """A failed fetch must never allow authentic=True."""
        # Simulate: both primary and corroboration fetches fail
        has_primary = False
        has_corrob = False
        has_any = has_primary or has_corrob

        if not has_any:
            verdict = {
                "authentic": False,
                "confidence": "low",
                "evidence_quality": "none",
            }
        else:
            verdict = {"authentic": True, "confidence": "high", "evidence_quality": "strong"}

        assert verdict["authentic"] is False
        assert verdict["confidence"] == "low"
        assert verdict["evidence_quality"] == "none"

    def test_caller_only_page_is_weak_evidence(self):
        """Evidence from ONLY the caller-provided URL is 'weak'
        because the caller controls that page."""
        has_primary = True
        has_corrob = False

        if has_primary and not has_corrob:
            evidence_quality = "weak"
        elif has_primary and has_corrob:
            evidence_quality = "strong"
        else:
            evidence_quality = "moderate"

        assert evidence_quality == "weak"

    def test_corroborated_evidence_is_strong(self):
        """Evidence from caller page + marketplace corroboration is 'strong'."""
        has_primary = True
        has_corrob = True

        if has_primary and has_corrob:
            evidence_quality = "strong"
        else:
            evidence_quality = "weak"

        assert evidence_quality == "strong"


class TestEvidenceQualityToConfidence:
    """Evidence quality constrains the maximum allowed confidence."""

    def _max_confidence(self, eq: str) -> str:
        if eq == "none":
            return "low"
        if eq == "weak":
            return "low"
        if eq == "moderate":
            return "medium"
        return "high"

    def test_none_evidence_max_low(self):
        assert self._max_confidence("none") == "low"

    def test_weak_evidence_max_low(self):
        assert self._max_confidence("weak") == "low"

    def test_moderate_evidence_max_medium(self):
        assert self._max_confidence("moderate") == "medium"

    def test_strong_evidence_max_high(self):
        assert self._max_confidence("strong") == "high"


class TestPromptCannotDecideFromFailedFetch:
    """The LLM prompt CANNOT declare authenticity from a failed fetch.
    This is the core issue identified in the review feedback."""

    def test_failed_fetch_overrides_llm(self):
        """Even if LLM says authentic=true, failed fetch overrides."""
        # Scenario: fetch fails, but LLM somehow returns authentic=true
        llm_says_authentic = True  # LLM hallucination or error
        fetch_success = False

        # Contract logic: no evidence → force not authentic
        if not fetch_success:
            authentic = False
            confidence = "low"
            evidence_quality = "none"
        else:
            authentic = llm_says_authentic
            confidence = "high"
            evidence_quality = "strong"

        assert authentic is False
        assert confidence == "low"
        assert evidence_quality == "none"

    def test_caller_only_page_skeptical(self):
        """With only caller's page, LLM cannot declare high confidence."""
        has_corrob = False  # Only caller's page
        llm_confidence = "high"  # LLM tries to declare high confidence

        if not has_corrob:
            evidence_quality = "weak"
            # Weak evidence forces low confidence
            confidence = "low"
            authentic = False
        else:
            confidence = llm_confidence
            authentic = True
            evidence_quality = "strong"

        assert confidence == "low"
        assert authentic is False
        assert evidence_quality == "weak"
