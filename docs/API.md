# Contract API Reference

## Write Methods

### `verify_nft(image_url, collection_name, claimed_creator) → str`

Submit an NFT for on-chain authenticity verification.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `image_url` | `str` | Yes | URL of the NFT image/listing |
| `collection_name` | `str` | No | Name of the collection |
| `claimed_creator` | `str` | No | Claimed creator of the work |

**Returns:** Verification key (string) for lookups.

**Process:**
1. Leader fetches listing page + OpenSea/MagicEden cross-references
2. Leader runs LLM analysis with all evidence
3. Validator independently fetches the same sources
4. Validator runs its own LLM and checks for conflicts
5. Consensus reached → result stored on-chain

**Stored Record:**
```json
{
  "requester": "0x...",
  "image_url": "https://...",
  "collection": "Collection Name",
  "claimed_creator": "Artist Name",
  "authentic": true,
  "confidence": "high",
  "similar_found": "none",
  "reasoning": "...",
  "evidence_quality": "strong"
}
```

---

## View Methods

### `get_verification(key) → dict`

Returns the full verification record.

```python
result = contract.get_verification("0")
# → {"requester": "0x...", "image_url": "...", "authentic": true, ...}
# or {"exists": False} if key not found
```

### `read_authenticity(key) → dict`

Returns a simplified result for badge contracts to act on.

```python
result = contract.read_authenticity("0")
# → {"verified": True, "authentic": true, "confidence": "high", "evidence_quality": "strong"}
# or {"verified": False} if key not found
```

### `stats() → dict`

Returns verification statistics.

```python
result = contract.stats()
# → {"total_verifications": 42}
```

---

## Data Types

### Confidence

Enum: `"high"` | `"medium"` | `"low"`

### Evidence Quality

Enum: `"strong"` | `"moderate"` | `"weak"` | `"none"`

| Value | Meaning |
|-------|---------|
| `strong` | Caller page + marketplace corroboration |
| `moderate` | Marketplace only, no caller page |
| `weak` | Only caller-provided page (untrusted) |
| `none` | No evidence acquired from any source |

### Similar Found

String. If not in the set `{"", "none", "none found", "no similar sources found", "n/a", "not found"}`, it represents a real infringing source and forces `authentic = false`.
