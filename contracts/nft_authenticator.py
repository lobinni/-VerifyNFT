# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
import json
from genlayer import *

# ─────────────────────────────────────────────────────────────
# Normalized similar_found values that mean "no infringing source".
# ─────────────────────────────────────────────────────────────
_NO_SOURCE = ("", "none", "none found", "no similar sources found", "n/a", "not found")

# Marketplaces used for cross-reference provenance checks.
# Each validator independently fetches these to corroborate (or contradict)
# what the caller-supplied listing page claims.
_MARKETPLACE_TEMPLATES = [
    "https://opensea.io/collection/{slug}",
    "https://magiceden.io/collection/{slug}",
]


def _slugify(name: str) -> str:
    """Best-effort collection name → URL slug."""
    import re
    s = name.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-") or "unknown"


def _fetch(url: str) -> str:
    """Fetch a URL via gl.nondet.web.render, return up to 4000 chars or ''."""
    try:
        raw = gl.nondet.web.render(url, mode="text")
        text = str(raw)[:4000]
        if len(text.strip()) > 50:
            return text
    except Exception:
        pass
    return ""


def _canonicalize_evidence_quality(raw: str) -> str:
    eq = raw.strip().lower()
    if eq in ("strong", "moderate", "weak", "none"):
        return eq
    return "weak"


def _canonicalize_confidence(raw: str) -> str:
    c = raw.strip().lower()
    if c in ("high", "medium", "low"):
        return c
    return "low"


def _has_real_source(sf: str) -> bool:
    return sf.strip().lower() not in _NO_SOURCE


def _fingerprint(text: str, length: int = 64) -> str:
    """Deterministic content fingerprint for cross-validator comparison."""
    # Simple rolling-hash–style fingerprint: take evenly-spaced chars.
    if not text:
        return ""
    t = text.strip().lower()
    if len(t) <= length:
        return t
    step = len(t) / length
    return "".join(t[int(i * step)] for i in range(length))


# ─────────────────────────────────────────────────────────────
class NFTAuthenticator(gl.Contract):
    """
    On-chain NFT authenticity verifier with **independent validator
    provenance acquisition and comparative evidence checking**.

    Key design decisions addressing review feedback:

    1. Validators independently fetch the listing AND cross-reference
       marketplaces — they never trust the leader's evidence alone.
    2. A failed or empty fetch forces authentic=False, confidence=low,
       evidence_quality=none — the prompt CANNOT decide originality
       from absent evidence.
    3. The validator runs its own LLM on independently acquired evidence
       and REJECTS if the core verdict (authentic vs not) conflicts.
    4. The validator caps the leader's confidence to what its own evidence
       supports — preventing inflated confidence claims.
    """

    verifications: TreeMap[str, str]
    verify_count: u256

    def __init__(self):
        self.verify_count = u256(0)

    # ─── PUBLIC WRITE ───────────────────────────────────────
    @gl.public.write
    def verify_nft(self, image_url: str, collection_name: str, claimed_creator: str) -> str:
        image_url = str(image_url).strip()
        if not image_url:
            raise Exception("image_url required")

        verdict = self._check_authenticity(image_url, collection_name, claimed_creator)
        key = str(int(self.verify_count))
        record = {
            "requester": str(gl.message.sender_address),
            "image_url": image_url,
            "collection": str(collection_name).strip(),
            "claimed_creator": str(claimed_creator).strip(),
            "authentic": verdict["authentic"],
            "confidence": verdict["confidence"],
            "similar_found": verdict["similar_found"],
            "reasoning": verdict["reasoning"],
            "evidence_quality": verdict["evidence_quality"],
        }
        self.verifications[key] = json.dumps(record)
        self.verify_count += u256(1)
        return key

    # ─── CONSENSUS CORE ────────────────────────────────────
    def _check_authenticity(self, image_url: str, collection: str, creator: str) -> dict:

        # ── LEADER ──────────────────────────────────────────
        def leader_fn() -> str:
            # --- Phase 1: Acquire provenance from MULTIPLE sources ---
            # 1a. Caller-provided listing page
            primary_page = _fetch(image_url)

            # 1b. Cross-reference on known marketplaces
            slug = _slugify(collection)
            corrob_pages = []
            for tmpl in _MARKETPLACE_TEMPLATES:
                url = tmpl.format(slug=slug)
                page = _fetch(url)
                if page:
                    corrob_pages.append({"url": url, "content": page[:2000]})

            # --- Phase 2: Evidence quality gate ---
            has_primary = len(primary_page) > 100
            has_corrob = len(corrob_pages) > 0

            if not has_primary and not has_corrob:
                # NO evidence from ANY source — cannot verify anything.
                return json.dumps({
                    "authentic": False,
                    "confidence": "low",
                    "similar_found": "none",
                    "reasoning": "No evidence could be acquired from the provided URL or marketplace cross-references. Authenticity cannot be determined.",
                    "evidence_quality": "none",
                    "fp_primary": "",
                    "fp_corrob": [],
                })

            if has_primary and not has_corrob:
                evidence_quality = "weak"   # only caller's page — untrusted
            elif has_primary and has_corrob:
                evidence_quality = "strong" # corroborated
            else:
                evidence_quality = "moderate"  # marketplace only

            # --- Phase 3: Content fingerprints for validator comparison ---
            fp_primary = _fingerprint(primary_page) if has_primary else ""
            fp_corrob = [_fingerprint(p["content"]) for p in corrob_pages]

            # --- Phase 4: LLM analysis with ALL acquired evidence ---
            corrob_text = "\n".join(
                f"MARKETPLACE ({p['url']}):\n{p['content'][:1000]}"
                for p in corrob_pages
            )

            prompt = f"""You are an NFT authenticity expert. Analyze this NFT listing for originality using ALL available evidence.

=== CALLER-PROVIDED LISTING ===
URL: {image_url}
CONTENT:
{primary_page[:3000] if has_primary else "(not fetched)"}

=== MARKETPLACE CROSS-REFERENCE ===
{corrob_text if corrob_text else "(no marketplace data found)"}

=== CLAIMS TO VERIFY ===
Collection: {collection}
Claimed Creator: {creator}

=== VERIFICATION RULES ===
1. CREATOR MATCH: Does ANY evidence mention the claimed creator as the actual creator?
2. COLLECTION MATCH: Does the collection exist on marketplaces? Does metadata match?
3. CONFLICT CHECK: Do marketplace records CONTRADICT the caller's listing?
   - Different creator listed on OpenSea/MagicEden = strong plagiarism signal
   - Collection exists but this NFT isn't in it = suspicious
4. ORIGINALITY: Signs of copying, stolen art, AI-generated without disclosure?
5. EVIDENCE QUALITY (already determined): {evidence_quality}

=== CRITICAL RULES ===
- If marketplace shows DIFFERENT creator than claimed → authentic MUST be false
- If no evidence mentions the claimed creator at all → authentic MUST be false
- If evidence_quality is "weak" (only caller's page) → be very skeptical
- If similar_found has a real source → authentic MUST be false
- If evidence_quality is "weak" → confidence MUST be "low"

Reply ONLY valid JSON:
{{"authentic": true/false, "confidence": "high"/"medium"/"low", "similar_found": "<url or 'none'>", "reasoning": "<2-3 sentences>"}}"""

            raw = gl.nondet.exec_prompt(prompt, response_format="json")
            data = raw if isinstance(raw, dict) else json.loads(str(raw).strip())

            # --- Phase 5: Normalize + enforce hard invariants ---
            confidence = _canonicalize_confidence(str(data.get("confidence", "")))
            evidence_quality = _canonicalize_evidence_quality(evidence_quality)
            similar_found = str(data.get("similar_found", "")).strip()
            reasoning = str(data.get("reasoning", "")).strip()
            if not reasoning or len(reasoning) < 10:
                reasoning = "Analysis completed but detailed reasoning was not provided."
            authentic = bool(data.get("authentic"))

            # INVARIANT: real similar source → not authentic
            if _has_real_source(similar_found):
                authentic = False
            # INVARIANT: no/weak evidence → not authentic, low confidence
            if evidence_quality in ("none", "weak"):
                authentic = False
                confidence = "low"
            # INVARIANT: moderate evidence caps at medium confidence
            if evidence_quality == "moderate" and confidence == "high":
                confidence = "medium"

            return json.dumps({
                "authentic": authentic,
                "confidence": confidence,
                "similar_found": similar_found,
                "reasoning": reasoning,
                "evidence_quality": evidence_quality,
                "fp_primary": fp_primary,
                "fp_corrob": fp_corrob,
            })

        # ── VALIDATOR ───────────────────────────────────────
        def validator_fn(leader_result) -> bool:
            """
            INDEPENDENTLY acquires provenance, runs own LLM, then checks
            for conflicting verdicts. Rejects if core judgment disagrees.
            """
            if not isinstance(leader_result, gl.vm.Return):
                return False
            try:
                leader = json.loads(leader_result.calldata)

                # === STRUCTURAL CHECKS ===
                if leader.get("confidence") not in ("high", "medium", "low"):
                    return False
                if not isinstance(leader.get("authentic"), bool):
                    return False
                if not isinstance(leader.get("similar_found"), str):
                    return False
                reasoning = leader.get("reasoning", "")
                if not isinstance(reasoning, str) or len(reasoning.strip()) < 10:
                    return False
                leader_eq = leader.get("evidence_quality", "unknown")
                if leader_eq not in ("strong", "moderate", "weak", "none"):
                    return False

                # === CROSS-FIELD INVARIANTS ===
                if leader["authentic"] and _has_real_source(leader["similar_found"]):
                    return False
                if leader_eq == "none" and leader["authentic"]:
                    return False
                if leader_eq in ("weak", "none") and leader["confidence"] != "low":
                    return False
                if leader_eq == "moderate" and leader["confidence"] == "high":
                    return False

                # === INDEPENDENT EVIDENCE ACQUISITION ===
                # Validator fetches the SAME sources independently.
                my_primary = _fetch(image_url)
                slug = _slugify(collection)
                my_corrob = []
                for tmpl in _MARKETPLACE_TEMPLATES:
                    url = tmpl.format(slug=slug)
                    page = _fetch(url)
                    if page:
                        my_corrob.append(page[:2000])

                my_has_primary = len(my_primary) > 100
                my_has_corrob = len(my_corrob) > 0

                # === EVIDENCE GATE ===
                # If leader claims strong evidence but validator can't acquire any,
                # reject — the leader's evidence claim is unverifiable.
                if leader_eq in ("strong", "moderate") and not my_has_primary and not my_has_corrob:
                    return False

                # === FINGERPRINT COMPARISON ===
                # If both fetched the primary page, fingerprints must roughly agree.
                leader_fp = leader.get("fp_primary", "")
                if my_has_primary and len(leader_fp) > 10:
                    my_fp = _fingerprint(my_primary)
                    # Character-level overlap (allow network-induced variance)
                    overlap = sum(1 for a, b in zip(leader_fp, my_fp) if a == b)
                    if overlap / len(leader_fp) < 0.4:
                        return False  # Pages are fundamentally different

                # === INDEPENDENT LLM VERDICT ===
                # Run our own analysis and check for CONFLICTING verdicts.
                if my_has_primary or my_has_corrob:
                    my_evidence = f"PRIMARY PAGE:\n{my_primary[:2000]}\n\n"
                    my_evidence += "\n".join(
                        f"MARKETPLACE:\n{p[:1000]}" for p in my_corrob
                    )

                    my_prompt = f"""You are an NFT authenticity verifier. Give your OWN verdict from this evidence.

EVIDENCE:
{my_evidence}

CLAIMS: Collection={collection}, Creator={creator}

RULES:
- If marketplace shows a DIFFERENT creator → authentic=false
- If claimed creator not found in any evidence → authentic=false
- If evidence is only the caller's page (no marketplace) → confidence=low

Reply ONLY: {{"authentic": true/false, "confidence": "high"/"medium"/"low"}}"""

                    try:
                        my_raw = gl.nondet.exec_prompt(my_prompt, response_format="json")
                        my_data = my_raw if isinstance(my_raw, dict) else json.loads(str(my_raw).strip())
                        my_authentic = bool(my_data.get("authentic"))
                        my_confidence = _canonicalize_confidence(str(my_data.get("confidence", "")))

                        # === CONFLICTING VERDICT CHECK ===
                        # If validator and leader DISAGREE on the core judgment,
                        # the verdict is unreliable — reject.
                        if leader["authentic"] != my_authentic:
                            return False

                        # === CONFIDENCE CEILING ===
                        # Leader's confidence cannot exceed what validator supports.
                        _conf_order = {"low": 0, "medium": 1, "high": 2}
                        if _conf_order.get(leader["confidence"], 0) > _conf_order.get(my_confidence, 0):
                            return False

                    except Exception:
                        # LLM failed — only accept conservative verdicts
                        if leader["authentic"] or leader["confidence"] != "low":
                            return False

                return True

            except Exception:
                return False

        return json.loads(gl.vm.run_nondet_unsafe(leader_fn, validator_fn))

    # ─── PUBLIC VIEWS ───────────────────────────────────────
    @gl.public.view
    def get_verification(self, key: str) -> dict:
        key = str(key)
        if key not in self.verifications:
            return {"exists": False}
        return json.loads(self.verifications[key])

    @gl.public.view
    def read_authenticity(self, key: str) -> dict:
        key = str(key)
        if key not in self.verifications:
            return {"verified": False}
        v = json.loads(self.verifications[key])
        return {
            "verified": True,
            "authentic": v["authentic"],
            "confidence": v["confidence"],
            "evidence_quality": v.get("evidence_quality", "unknown"),
        }

    @gl.public.view
    def stats(self) -> dict:
        return {"total_verifications": int(self.verify_count)}
