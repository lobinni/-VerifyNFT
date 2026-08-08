#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────
# Interact with the deployed NFTAuthenticator contract
#
# Usage:
#   chmod +x scripts/verify.sh
#   ./scripts/verify.sh <image_url> [collection] [creator]
# ─────────────────────────────────────────────────────────────
set -euo pipefail

CONTRACT="0x87Fcb84379Ce2c7e4798A4A0787cf019Ae36B715"
EXPLORER="https://explorer-studio.genlayer.com/address/$CONTRACT"

if [ $# -lt 1 ]; then
    echo "Usage: $0 <image_url> [collection] [creator]"
    echo ""
    echo "Example:"
    echo "  $0 https://i.seadn.io/gcs/files/example.png 'Bored Ape Yacht Club' 'Yuga Labs'"
    exit 1
fi

IMAGE_URL="$1"
COLLECTION="${2:-}"
CREATOR="${3:-}"

echo "══════════════════════════════════════════════════════"
echo "  NFT Authenticator — Verify"
echo "══════════════════════════════════════════════════════"
echo ""
echo "Contract:   $CONTRACT"
echo "Explorer:   $EXPLORER"
echo ""
echo "Image URL:  $IMAGE_URL"
echo "Collection: $COLLECTION"
echo "Creator:    $CREATOR"
echo ""
echo "Calling: verify_nft(image_url, collection, creator)"
echo ""
echo "Flow:"
echo "  1. Leader fetches listing + OpenSea + MagicEden"
echo "  2. Leader runs LLM → verdict + evidence_quality"
echo "  3. Validator independently fetches all# sources"
echo "  4. Validator runs own LLM, checks for conflicts"
echo "  5. If agree → accepted; if conflict → rejected"
echo ""
echo "Execute via GenLayer Studio console or SDK."
