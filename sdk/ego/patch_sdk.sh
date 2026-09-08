#!/bin/bash
set -e

# Layer the SGX-Step AEP/TCS bindings on top of Edgeless RT's ert.patch, following
# its OEDEV workflow (edgelessrt/3rdparty/openenclave/HACKING.md): patch the
# vendored Open Enclave tree in place and build it with -DOEDEV=ON.

HERE="$(cd "$(dirname "$0")" && pwd)"
OE_DIR="$HERE/edgelessrt/3rdparty/openenclave/openenclave"
# Reuse the Open Enclave bindings patch; it applies on top of ert.patch.
BINDINGS="$HERE/../oe/0001-Minimal-SGX-Step-bindings.patch"

if grep -Rq "sgx_set_aep" "$OE_DIR"; then
    echo "SGX-Step bindings already present; nothing to patch."
    exit 0
fi

cd "$OE_DIR"

if ! grep -q "ert_join_threads_created_inside_enclave" include/openenclave/host.h; then
    echo "=== applying Edgeless RT ert.patch ==="
    patch -p1 < "$OE_DIR/../ert.patch"
fi

echo "=== applying SGX-Step AEP/TCS bindings ==="
patch -p1 < "$BINDINGS"
