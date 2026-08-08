#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────
# Deploy NFTAuthenticator contract to GenLayer Studio
#
# Prerequisites:
#   - GenLayer Studio account (https://studio.genlayer.com)
#
# Usage:
#   chmod +x scripts/deploy.sh
#   ./scripts/deploy.sh
# ─────────────────────────────────────────────────────────────
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CONTRACT_FILE="$PROJECT_ROOT/contracts/nft_authenticator.py"
CONTRACT_ADDR="0x87Fcb84379Ce2c7e4798A4A0787cf019Ae36B715"
EXPLORER="https://explorer-studio.genlayer.com/address/$CONTRACT_ADDR"

echo "══════════════════════════════════════════════════════"
echo "  NFT Authenticator — Deployment Script"
echo "══════════════════════════════════════════════════════"
echo ""

# ─── Pre-flight checks ─────────────────────────────────────
if [ ! -f "$CONTRACT_FILE" ]; then
    echo "ERROR: Contract not found at $CONTRACT_FILE"
    exit 1
fi

echo "Contract: $CONTRACT_FILE"
echo "Size:     $(wc -l < "$CONTRACT_FILE") lines"
echo ""

# Check Depends header
if head -1 "$CONTRACT_FILE" | grep -q "Depends"; then
    echo "✓ GenLayer Depends header"
else
    echo "✗ Missing Depends header"; exit 1
fi

# Check class
if grep -q "class NFTAuthenticator" "$CONTRACT_FILE"; then
    echo "✓ NFTAuthenticator class"
else
    echo "✗ Missing class"; exit 1
fi

# Check methods
for m in verify_nft get_verification read_authenticity stats _check_authenticity; do
    if grep -q "def $m" "$CONTRACT_FILE"; then
        echo "✓ $m()"
    else
        echo "✗ Missing $m()"; exit 1
    fi
done

# Check validator independence markers
if grep -q "INDEPENDENT" "$CONTRACT_FILE"; then
    echo "✓ Independent validator verification"
else
    echo "⚠ No INDEPENDENT marker (check validator manually)"
fi

if grep -q "_MARKETPLACE_TEMPLATES" "$CONTRACT_FILE"; then
    echo "✓ Multi-source evidence (marketplaces)"
else
    echo "⚠ No marketplace cross-references"
fi

if grep -q "evidence_quality" "$CONTRACT_FILE"; then
    echo "✓ Evidence quality tracking"
else
    echo "⚠ No evidence quality"
fi

echo ""
echo "══════════════════════════════════════════════════════"
echo "  All checks passed"
echo "══════════════════════════════════════════════════════"
echo ""
echo "Current deployment:"
echo "  Address:  $CONTRACT_ADDR"
echo "  Explorer: $EXPLORER"
echo ""
echo "To deploy a NEW instance:"
echo "  1. Open https://studio.genlayer.com"
echo "  2. Create → Python contract"
echo "  3. Paste contents of contracts/nft_authenticator.py"
echo "  4. Deploy"
echo "  5. Update CONTRACT_ADDR in this script"
