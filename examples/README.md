# Examples

## basic_verify.py

Verify a single NFT's authenticity against the contract.

```bash
python examples/basic_verify.py
```

## Interacting via GenLayer Studio

### Verify an NFT

```python
# In GenLayer Studio console:
result = contract.verify_nft(
    "https://i.seadn.io/gcs/files/example.png",
    "Bored Ape Yacht Club",
    "Yuga Labs"
)
```

### Get verification result

```python
# Full record:
record = contract.get_verification("0")

# Simplified result (for badge contracts):
auth = contract.read_authenticity("0")
# → {"verified": True, "authentic": True, "confidence": "high", "evidence_quality": "strong"}
```

### Get statistics

```python
stats = contract.stats()
# → {"total_verifications": 5}
```

## Evidence Quality Levels

| Level | Meaning | Authentic? | Max Confidence |
|-------|---------|-----------|----------------|
| `strong` | Caller page + marketplace corroboration | Can be true | high |
| `moderate` | Marketplace only, no caller page | Can be true | medium |
| `weak` | Only caller-provided page | Always false | low |
| `none` | No evidence acquired | Always false | low |
