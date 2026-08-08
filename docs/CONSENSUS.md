# Consensus Design

## Overview

NFTAuthenticator uses GenLayer's **Optimistic Democracy** with a strengthened validator that independently acquires provenance and performs comparative evidence checking.

## Leader Function

The leader acquires evidence from **multiple sources** and runs LLM analysis:

```
┌─────────────────────────────────────────────────┐
│  LEADER                                          │
│                                                  │
│  1. Fetch caller-provided URL                    │
│     └─ gl.nondet.web.render(image_url)           │
│                                                  │
│  2. Cross-reference on marketplaces              │
│     ├─ OpenSea: /collection/{slug}               │
│     └─ MagicEden: /collection/{slug}             │
│                                                  │
│  3. Determine evidence quality                   │
│     ├─ caller + marketplace = strong             │
│     ├─ marketplace only = moderate               │
│     ├─ caller only = weak                        │
│     └─ nothing fetched = none                    │
│                                                  │
│  4. Generate content fingerprints                │
│                                                  │
│  5. LLM analysis with ALL evidence              │
│                                                  │
│  6. Enforce hard invariants                      │
│     ├─ similar_found → authentic=false           │
│     ├─ evidence=none/weak → authentic=false      │
│     └─ evidence=moderate → confidence≤medium     │
└─────────────────────────────────────────────────┘
```

## Validator Function

The validator **independently** performs the same evidence acquisition and runs its own LLM analysis:

```
┌─────────────────────────────────────────────────┐
│  VALIDATOR                                       │
│                                                  │
│  1. Structural validation                        │
│     ├─ confidence ∈ {high, medium, low}          │
│     ├─ authentic ∈ {true, false}                 │
│     └─ reasoning.length ≥ 10                    │
│                                                  │
│  2. Cross-field invariant checks                 │
│     ├─ authentic + real source = REJECT          │
│     ├─ none evidence + authentic = REJECT        │
│     ├─ weak evidence + high conf = REJECT        │
│     └─ moderate evidence + high conf = REJECT    │
│                                                  │
│  3. INDEPENDENT evidence acquisition             │
│     ├─ Re-fetch caller URL                       │
│     └─ Re-fetch marketplace pages                │
│                                                  │
│  4. Evidence gate                                │
│     └─ Leader claims strong but I can't fetch    │
│        → REJECT                                  │
│                                                  │
│  5. Fingerprint comparison                       │
│     └─ overlap < 40% → REJECT                   │
│                                                  │
│  6. Independent LLM verdict                      │
│     ├─ Run own analysis on my evidence           │
│     ├─ CONFLICTING verdict → REJECT              │
│     └─ Leader confidence exceeds mine → REJECT   │
└─────────────────────────────────────────────────┘
```

## Key Design Decisions

### 1. Multiple Evidence Sources

The caller provides a URL, but the contract also fetches from OpenSea and MagicEden. This prevents the prompt from "deciding originality from only a caller-selected page."

### 2. Failed Fetch = No Authenticity

If NO evidence can be acquired (neither caller page nor marketplaces), the verdict is forced to `authentic: false, confidence: low, evidence_quality: none`. The LLM cannot override this.

### 3. Conflicting Verdict Rejection

If the leader says authentic=true but the validator's independent LLM says authentic=false (or vice versa), the validator **rejects**. This prevents accepting contradictory conclusions.

### 4. Confidence Ceiling

The leader's confidence cannot exceed what the validator's independent evidence supports. If the validator only supports low confidence, the leader cannot claim high confidence.

### 5. Evidence Quality Constrains Confidence

| Evidence Quality | Can be Authentic? | Max Confidence |
|-----------------|-------------------|----------------|
| `strong` | Yes | high |
| `moderate` | Yes | medium |
| `weak` | No (always false) | low |
| `none` | No (always false) | low |

## Addressing Review Feedback

| Feedback | Solution |
|----------|----------|
| "validators independently verify" | Validator independently fetches ALL sources and runs its own LLM |
| "from acquired provenance and comparative evidence" | Leader + validator both fetch caller page AND marketplace cross-references |
| "accepts conflicting verdicts" | Validator rejects if its LLM disagrees with leader's core judgment |
| "prompt can decide from caller-selected page only" | Multiple evidence sources; caller-only page = weak evidence = authentic=false |
| "or even a failed fetch" | Failed fetch forces authentic=false, confidence=low, evidence_quality=none |
