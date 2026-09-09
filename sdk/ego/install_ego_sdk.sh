#!/bin/bash
set -e

cd "$(dirname "$0")"

git submodule update --init --recursive edgelessrt ego

# ----------------------------------------------------------------------
echo "[ patching Edgeless RT's Open Enclave ]"
./patch_sdk.sh
echo "Edgeless RT successfully patched with SGX-Step bindings!"

# ----------------------------------------------------------------------
echo "[ installing prerequisites ]"
sudo apt-get -yqq install build-essential clang-11 cmake gdb libssl-dev ninja-build libelf-dev

# ----------------------------------------------------------------------
echo "[ building Edgeless RT (patched Open Enclave, OEDEV) ]"
cd edgelessrt
mkdir -p build
cd build
# OEDEV=ON builds the in-place patched OE submodule instead of copying it and
# re-applying ert.patch, so our SGX-Step bindings survive into liboehost.
cmake -GNinja -DOEDEV=ON ..
ninja
sudo ninja install
cd ../..

ERT_ENV=$(find /opt/edgelessrt -name openenclaverc 2>/dev/null | head -1)
echo "source Edgeless RT env with: source $ERT_ENV"

# ----------------------------------------------------------------------
echo "[ building EGo against patched Edgeless RT ]"
# shellcheck disable=SC1090
source "$ERT_ENV"
cd ego
mkdir -p build
cd build
cmake -GNinja ..
ninja
sudo ninja install
cd ../..

echo "EGo SDK succesfully installed (with SGX-Step bindings)!"
