# NFTAuthenticator

**On-chain NFT authenticity verification — an Intelligent Contract where validators independently acquire provenance and comparative evidence, then reach consensus on whether the work is original.**

## Contract

| | |
|---|---|
| **Address** | `0x8853D0bC9385eA640dE70c87FeaF544676678FB1` |
| **Network** | GenLayer Studio |
| **Explorer** | [explorer-studio.genlayer.com](https://explorer-studio.genlayer.com/address/0x8853D0bC9385eA640dE70c87FeaF544676678FB1) |
| **Deploy TX** | [0x6ab87f…](https://explorer-studio.genlayer.com/tx/0xf5bd2755d2c07919e63545b701aa2c241d397948f8c99b33a716a39b298b7769) |

---

## What It Does

NFTAuthenticator answers **"is this NFT genuinely the claimed creator's original work?"** without centralized authentication.

A requester submits the image/listing URL, collection name, and claimed creator. The contract then:

1. **Acquires evidence from multiple sources** — the caller's listing page AND marketplace cross-references (OpenSea, MagicEden)
2. **Runs LLM authenticity analysis** on all gathered evidence
3. **Each validator independently** re-fetches the same sources, runs its own LLM, and **rejects conflicting verdicts**
4. Records the verdict permanently on-chain

### Methods

| Method | Type | Description |
|--------|------|-------------|
| `verify_nft(url, collection, creator)` | `@gl.public.write` | Submit NFT for verification → returns key |
| `get_verification(key)` | `@gl.public.view` | Full record |
| `read_authenticity(key)` | `@gl.public.view` | `{verified, authentic, confidence, evidence_quality}` |
| `stats()` | `@gl.public.view` | `{total_verifications}` |

---

## Why This Contract Is Strong

### The Problem It Solves

A naive authenticity contract has three weaknesses:

1. **Format-only validators** — they check JSON structure but not whether the verdict is semantically correct
2. **Single-source evidence** — the LLM decides from only the caller-provided page (which the caller controls)
3. **Failed-fetch tolerance** — the LLM can hallucinate authenticity even when no page was fetched

This contract fixes all three.

### How Validators Independently Verify

```
LEADER                                        VALIDATOR
──────                                        ─────────
1. Fetch caller URL                           1. Re-fetch caller URL independently
2. Cross-ref OpenSea / MagicEden              2. Re-fetch marketplaces independently
3. Determine evidence quality                 3. Compare page fingerprints
4. LLM analysis on ALL evidence               4. Run own LLM on own evidence
5. Enforce hard invariants                    5. REJECT if verdict conflicts
6. Return verdict                             6. REJECT if confidence inflated
```

### Evidence Quality Gates

The contract never trusts caller-provided evidence alone:

| Evidence Quality | Sources Acquired | Can be Authentic? | Max Confidence |
|-----------------|-----------------|-------------------|----------------|
| `strong` | Caller page + marketplace | Yes | high |
| `moderate` | Marketplace only | Yes | medium |
| `weak` | Caller page only | **No** | low |
| `none` | Nothing fetched | **No** | low |

### Hard Invariants (enforced by both leader and validator)

```python
# 1. Real similar source found → NOT authentic
if has_real_source(similar_found): authentic = False

# 2. No/weak evidence → NOT authentic, LOW confidence
if evidence_quality in ("none", "weak"): authentic = False; confidence = "low"

# 3. Moderate evidence → confidence capped at medium
if evidence_quality == "moderate" and confidence == "high": confidence = "medium"

# 4. Validator LLM disagrees on core verdict → REJECT
if leader.authentic != validator.authentic: return False

# 5. Leader confidence exceeds validator's support → REJECT
if conf_order[leader.confidence] > conf_order[validator.confidence]: return False

# 6. Page fingerprints differ drastically → REJECT
if fingerprint_overlap < 0.4: return False

# 7. Leader claims strong evidence, validator can't fetch → REJECT
if leader_eq in ("strong","moderate") and not validator_fetched: return False
```

---

## Project Structure

```
NFTAuthenticator/
├── contracts/
│   └── nft_authenticator.py          ← GenLayer Intelligent Contract
├── tests/
│   ├── test_invariants.py             ← Cross-field invariant enforcement
│   ├── test_evidence_gates.py         ← Evidence quality → confidence constraints
│   ├── test_conflict_detection.py     ← Conflicting verdict rejection
│   └── README.md
├── examples/
│   ├── basic_verify.py                ← Usage example
│   └── README.md
├── scripts/
│   ├── deploy.sh                      ← Deployment helper
│   └── verify.sh                      ← Interaction helper
├── docs/
│   ├── CONSENSUS.md                   ← Consensus design (full)
│   └── API.md                         ← Contract API reference
├── pyproject.toml
├── LICENSE
└── README.md
```

---

## Quick Start

### Deploy

```bash
./scripts/deploy.sh
```

Or manually:
1. Open [GenLayer Studio](https://studio.genlayer.com)
2. Create new Python contract
3. Paste `contracts/nft_authenticator.py`
4. Deploy

### Interact

```bash
./scripts/verify.sh <image_url> <collection> <creator>
```

### Run Tests

```bash
pip install pytest
python -m pytest tests/ -v
```

### Example

```python
# In GenLayer Studio console:

# Verify an NFT
key = contract.verify_nft(
    "https://i.seadn.io/gcs/files/example.png",
    "Bored Ape Yacht Club",
    "Yuga Labs"
)

# Read the result
result = contract.get_verification(key)
# → {"authentic": True, "confidence": "high", "evidence_quality": "strong", ...}

# Simplified check (for badge contracts)
auth = contract.read_authenticity(key)
# → {"verified": True, "authentic": True, "confidence": "high", "evidence_quality": "strong"}

# Stats
stats = contract.stats()
# → {"total_verifications": 42}
```

---

## Why GenLayer

A deterministic EVM cannot judge originality — it requires interpretation and non-deterministic page fetching. GenLayer's **Optimistic Democracy** lets each validator independently acquire evidence and vote on whether the leader's verdict is acceptable.

Use NFTAuthenticator when authenticity hinges on interpreting visual/listing evidence against a claim. Use a backend signature check when provenance is already cryptographically attestable — that is mechanical and does not need a validator network.

---

## Engineering Notes

- **Multiple evidence sources** prevent the LLM from deciding originality based only on a caller-controlled page
- **Failed fetch degrades gracefully** — forces `authentic=false` rather than allowing hallucination
- **Conflicting verdict detection** — validator rejects if its independent analysis contradicts the leader's core judgment
- **Confidence ceiling** — leader cannot claim higher confidence than what validator's evidence supports
- **Evidence is untrusted (greybox)** — caller's page alone is `weak`; marketplace corroboration upgrades to `strong`
- **Cross-field invariants** enforced by BOTH leader (normalization) and validator (rejection)
- **Integers, not floats** — `verify_count` is `u256`, confidence is an enum band — discrete values keep agreement stable
- **ACCEPTED ≠ executed** — consensus means validators accepted validity; external contracts must act separately
- **Optimistic finality has appeal window** — verification is provisional until the appeal window elapses

---

## License

MIT
