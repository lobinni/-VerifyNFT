# NFT Authenticator — Tests

## Test Structure

Tests validate the contract's consensus logic, invariant enforcement, and edge cases.

### Running Tests

Tests run against the GenLayer Studio Simulator:

```bash
# Ensure GenLayer Studio is running
python -m pytest tests/ -v
```

### Test Categories

| File | What it tests |
|------|--------------|
| `test_invariants.py` | Cross-field invariant enforcement |
| `test_evidence_gates.py` | Evidence quality → confidence → authentic constraints |
| `test_validator_independence.py` | Validator independently acquires and verifies evidence |
| `test_conflict_detection.py` | Conflicting verdict rejection |
| `test_fingerprint.py` |G| Content fingerprint comparison |
