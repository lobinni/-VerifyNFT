"""
Example: Verify a single NFT using the NFTAuthenticator contract.

Usage:
    python examples/basic_verify.py

Requires: genlayer-js SDK or direct RPC calls to GenLayer Studio.
"""
import json

# Contract address on GenLayer Studio
CONTRACT = "0x87Fcb84379Ce2c7e4798A4A0787cf019Ae36B715"

# Example NFT to verify
EXAMPLE = {
    "image_url": "https://i.seadn.io/gcs/files/01de28a78ad0d3c4e2ab4fab8eaa2da3.png",
    "collection": "Bored Ape Yacht Club",
    "claimed_creator": "Yuga Labs",
}


def main():
    print("=" * 60)
    print("NFT Authenticator — Basic Verification Example")
    print("=" * 60)
    print()
    print(f"Contract: {CONTRACT}")
    print(f"Network:  GenLayer Studio")
    print()
    print("Submitting verification:")
    print(f"  Image URL:    {EXAMPLE['image_url'][:60]}…")
    print(f"  Collection:   {EXAMPLE['collection']}")
    print(f"  Claimed Creator: {EXAMPLE['claimed_creator']}")
    print()
    print("This would call: verify_nft(image_url, collection_name, claimed_creator)")
    print()
    print("Expected flow:")
    print("  1. Leader fetches listing + OpenSea/MagicEden cross-references")
    print("  2. Leader runs LLM analysis → verdict")
    print("  3. Validator INDEPENDENTLY fetches the same sources")
    print("  4. Validator runs its own LLM → checks for conflicts")
    print("  5. If verdicts agree → accepted; if conflicting → rejected")
    print()
    print("Expected result format:")
    result = {
        "authentic": True,
        "confidence": "high",
        "similar_found": "none",
        "reasoning": "OpenSea confirms Yuga Labs as creator of BAYC. Listing metadata matches.",
        "evidence_quality": "strong",
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
