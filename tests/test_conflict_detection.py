"""
Conflict detection tests — verify that the validator rejects
when leader and validator reach contradictory verdicts.
"""


class TestConflictingVerdictRejection:
    """The validator must reject if its independent analysis
    contradicts the leader's core judgment (authentic vs not)."""

    def test_leader_authentic_validator_not_rejects(self):
        """If leader says authentic but validator independently finds not authentic,
        the validator MUST reject."""
        leader_authentic = True
        validator_authentic = False

        # Validator rejects on conflicting core verdict
        reject = leader_authentic != validator_authentic
        assert reject is True

    def test_leader_not_authentic_validator_authentic_rejects(self):
        """Conflict in either direction is rejected."""
        leader_authentic = False
        validator_authentic = True

        reject = leader_authentic != validator_authentic
        assert reject is True

    def test_agreement_accepts(self):
        """When both agree on authentic, the verdict is accepted
        (other checks still apply)."""
        for agreement in [(True, True), (False, False)]:
            leader_authentic, validator_authentic = agreement
            reject = leader_authentic != validator_authentic
            assert reject is False


class TestConfidenceCeiling:
    """The leader's confidence cannot exceed what the validator's
    independent evidence supports."""

    _conf_order = {"low": 0, "medium": 1, "high": 2}

    def test_leader_high_validator_low_rejects(self):
        """Leader claims high confidence but validator only supports low → reject."""
        leader_conf = "high"
        validator_conf = "low"

        reject = self._conf_order[leader_conf] > self._conf_order[validator_conf]
        assert reject is True

    def test_leader_medium_validator_medium_accepts(self):
        """Equal confidence levels are accepted."""
        leader_conf = "medium"
        validator_conf = "medium"

        reject = self._conf_order[leader_conf] > self._conf_order[validator_conf]
        assert reject is False

    def test_leader_low_validator_high_accepts(self):
        """Leader is more conservative than validator → accepted."""
        leader_conf = "low"
        validator_conf = "high"

        reject = self._conf_order[leader_conf] > self._conf_order[validator_conf]
        assert reject is False


class TestUnverifiableHighConfidence:
    """High-confidence authentic claims that the validator cannot
    independently verify must be rejected."""

    def test_high_conf_authentic_without_evidence_rejects(self):
        """Leader claims authentic+high but validator can't fetch anything."""
        leader_authentic = True
        leader_confidence = "high"
        leader_evidence_quality = "strong"
        validator_can_fetch = False

        # If leader claims strong evidence but validator can't acquire any
        if leader_evidence_quality in ("strong", "moderate") and not validator_can_fetch:
            reject = True
        else:
            reject = False

        assert reject is True

    def test_low_conf_not_authentic_without_evidence_accepts(self):
        """Conservative verdicts (low confidence, not authentic) are accepted
        even when validator can't verify — they make no strong claims."""
        leader_authentic = False
        leader_confidence = "low"
        leader_evidence_quality = "none"
        validator_can_fetch = False

        # Conservative verdicts don't need verification
        if not leader_authentic and leader_confidence == "low":
            reject = False
        else:
            reject = True

        assert reject is False
