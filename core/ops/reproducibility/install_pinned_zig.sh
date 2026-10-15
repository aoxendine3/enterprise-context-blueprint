#!/bin/bash
# =============================================================================
# ops/reproducibility/install_pinned_zig.sh
# =============================================================================
# XORAS ZERO-TRUST DIGEST-PINNED DUAL-MIRROR ZIG COMPILER INSTALLER
# -----------------------------------------------------------------------------
# Mandate: Zero reliance on Homebrew formula servers or package managers.
# - Primary source: official ziglang.org release tarball
# - Secondary source: independent mirror (pkg.hexops.org) cross-verification
# - Digest enforcement: hardcoded cryptographic SHA-256 check
# - Differential audit: cmp -l assert 0 bit difference between mirrors
# - Fail-closed: job aborts immediately if either digest mismatches.
# =============================================================================

set -eo pipefail

INSTALL_DIR="${1:-$HOME/.zig-0.16.0}"
PINNED_VERSION="0.16.0"

echo "================================================================================"
echo "    XORAS ZERO-TRUST DIGEST-PINNED ZIG INSTALLER (DUAL-MIRROR PROOF)           "
echo "================================================================================"
echo "Target Install Directory: $INSTALL_DIR"

# Platform detection
OS="$(uname -s)"
ARCH="$(uname -m)"

case "$OS" in
    Darwin)
        case "$ARCH" in
            arm64|aarch64)
                PLATFORM="aarch64-macos"
                EXPECTED_SHA="b23d70deaa879b5c2d486ed3316f7eaa53e84acf6fc9cc747de152450d401489"
                TARBALL_NAME="zig-aarch64-macos-${PINNED_VERSION}.tar.xz"
                ;;
            x86_64)
                PLATFORM="x86_64-macos"
                EXPECTED_SHA="0387557ed1877bc6a2e1802c8391953baddba76081876301c522f52977b52ba7"
                TARBALL_NAME="zig-x86_64-macos-${PINNED_VERSION}.tar.xz"
                ;;
            *)
                echo "❌ Unsupported macOS architecture: $ARCH"
                exit 1
                ;;
        esac
        ;;
    Linux)
        case "$ARCH" in
            x86_64)
                PLATFORM="x86_64-linux"
                EXPECTED_SHA="70e49664a74374b48b51e6f3fdfbf437f6395d42509050588bd49abe52ba3d00"
                TARBALL_NAME="zig-x86_64-linux-${PINNED_VERSION}.tar.xz"
                ;;
            aarch64|arm64)
                PLATFORM="aarch64-linux"
                EXPECTED_SHA="ea4b09bfb22ec6f6c6ceac57ab63efb6b46e17ab08d21f69f3a48b38e1534f17"
                TARBALL_NAME="zig-aarch64-linux-${PINNED_VERSION}.tar.xz"
                ;;
            *)
                echo "❌ Unsupported Linux architecture: $ARCH"
                exit 1
                ;;
        esac
        ;;
    *)
        echo "❌ Unsupported operating system: $OS"
        exit 1
        ;;
esac

echo "[*] Detected Target Platform: $PLATFORM"
echo "[*] Hardcoded Cryptographic Digest (SHA-256): $EXPECTED_SHA"

PRIMARY_URL="https://ziglang.org/download/${PINNED_VERSION}/${TARBALL_NAME}"
MIRROR_URL="https://pkg.hexops.org/zig/${TARBALL_NAME}"

STAGE_DIR=$(mktemp -d "/tmp/xoras_zig_install_XXXXXX")
trap 'rm -rf "$STAGE_DIR"' EXIT

PRIMARY_TARBALL="$STAGE_DIR/zig_primary.tar.xz"
MIRROR_TARBALL="$STAGE_DIR/zig_mirror.tar.xz"

# Step 1: Download from Primary Mirror
echo -e "\n[*] Step 1: Fetching Primary Release Tarball (ziglang.org)..."
curl -sSL --retry 3 --max-time 120 "$PRIMARY_URL" -o "$PRIMARY_TARBALL"

PRIMARY_SHA=$(shasum -a 256 "$PRIMARY_TARBALL" | awk '{print $1}')
echo "    - Primary SHA-256: $PRIMARY_SHA"

if [ "$PRIMARY_SHA" != "$EXPECTED_SHA" ]; then
    echo "❌ FATAL: Primary tarball checksum mismatch against hardcoded pin!"
    echo "    - Expected: $EXPECTED_SHA"
    echo "    - Received: $PRIMARY_SHA"
    exit 1
fi
echo "    [PASS] Primary checksum verified bit-for-bit."

# Step 2: Cross-Verification against Independent Mirror
echo -e "\n[*] Step 2: Cross-Verifying Against Independent Mirror (pkg.hexops.org)..."
curl -sSL --retry 3 --max-time 120 "$MIRROR_URL" -o "$MIRROR_TARBALL"

MIRROR_SHA=$(shasum -a 256 "$MIRROR_TARBALL" | awk '{print $1}')
echo "    - Mirror SHA-256:  $MIRROR_SHA"

if [ "$MIRROR_SHA" != "$EXPECTED_SHA" ]; then
    echo "❌ FATAL: Mirror tarball checksum mismatch against hardcoded pin!"
    echo "    - Expected: $EXPECTED_SHA"
    echo "    - Received: $MIRROR_SHA"
    exit 1
fi
echo "    [PASS] Mirror checksum verified bit-for-bit."

# Step 3: Differential Byte Audit between Primary and Mirror
echo -e "\n[*] Step 3: Differential Byte Audit (cmp -l primary vs mirror)..."
DIFF_BYTES=$(cmp -l "$PRIMARY_TARBALL" "$MIRROR_TARBALL" | wc -l | tr -d ' ')
echo "    - cmp -l difference: $DIFF_BYTES differing bytes"

if [ "$DIFF_BYTES" -ne 0 ]; then
    echo "❌ FATAL: Bit divergence detected between primary and mirror tarballs!"
    exit 1
fi
echo "    [PASS] Zero bit divergence across mirrors."

# Step 4: Extract and Deploy Binary
echo -e "\n[*] Step 4: Extracting Verified Bitstring to $INSTALL_DIR..."
rm -rf "$INSTALL_DIR"
mkdir -p "$INSTALL_DIR"

tar -xf "$PRIMARY_TARBALL" -C "$STAGE_DIR"
EXTRACTED_SUBDIR=$(find "$STAGE_DIR" -maxdepth 1 -type d -name "zig-*" | head -n 1)

cp -R "$EXTRACTED_SUBDIR/"* "$INSTALL_DIR/"

INSTALLED_ZIG="$INSTALL_DIR/zig"
chmod +x "$INSTALLED_ZIG"

INSTALLED_VERSION=$("$INSTALLED_ZIG" version)
echo "    - Installed Binary Version: $INSTALLED_VERSION"

if [ "$INSTALLED_VERSION" != "$PINNED_VERSION" ]; then
    echo "❌ FATAL: Executable version $INSTALLED_VERSION != expected $PINNED_VERSION"
    exit 1
fi

echo -e "\n================================================================================"
echo ">>> SUPPLY-CHAIN PROOF VERIFIED: EXACT BITSTRING INSTALLED AND VALIDATED."
echo ">>> Binary Location: $INSTALLED_ZIG"
echo "================================================================================"

# If running inside GitHub Actions, export to GITHUB_PATH
if [ -n "$GITHUB_PATH" ]; then
    echo "$INSTALL_DIR" >> "$GITHUB_PATH"
    echo "    [CI] Appended $INSTALL_DIR to GITHUB_PATH"
fi

exit 0
