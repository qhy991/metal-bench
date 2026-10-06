#!/bin/sh
# Explicit matching Xcode/SDK; never change global xcode-select.
set -eu
: "${DEVELOPER_DIR:?Set the approved Xcode Developer directory}"
: "${SDKROOT:?Set the matching macOS SDK path}"
out=${1:?Pass a new external build directory}
test ! -e "$out"
mkdir -p "$out/module-cache"
root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
"$DEVELOPER_DIR/Toolchains/XcodeDefault.xctoolchain/usr/bin/swiftc" \
  -sdk "$SDKROOT" -target arm64-apple-macosx15.0 -module-cache-path "$out/module-cache" \
  -O "$root/native/runner.swift" -framework Metal -o "$out/metal-bench-runner"
echo "$out/metal-bench-runner"
