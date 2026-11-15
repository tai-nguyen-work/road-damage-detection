#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p downloads work
IMAGE_URL="${IMAGE_URL:-https://downloads.raspberrypi.com/raspios_lite_arm64/images/raspios_lite_arm64-2026-10-06/2026-10-06-raspios-trixie-arm64-lite.img.xz}"
EXPECTED_SHA256="${EXPECTED_SHA256:-483db18a48da399b5b7022ffae9a07bc6d99daab30e593aedac09b69ff422843}"
ARCHIVE="downloads/raspios-lite.img.xz"
if [[ ! -s "$ARCHIVE" ]]; then
  echo "Downloading official Raspberry Pi OS Lite ARM64..."
  curl -fL --retry 3 "$IMAGE_URL" -o "$ARCHIVE"
fi
printf '%s  %s\n' "$EXPECTED_SHA256" "$ARCHIVE" | shasum -a 256 -c -
# Run all image extraction operations in a temporary Linux container, avoiding macOS mount/loop requirements.
docker run --rm --platform linux/arm64 -e EXPECTED_SHA256="$EXPECTED_SHA256" \
  -v "$PWD/downloads:/downloads:ro" -v "$PWD/work:/work" \
  alpine:3.21 sh -eu -c '
    apk add --no-cache xz e2fsprogs-extra python3 tar coreutils >/dev/null
    xz -dc /downloads/raspios-lite.img.xz > /work/disk.img
    python3 - <<"PY"
import struct
with open("/work/disk.img", "rb") as f:
    mbr=f.read(512)
if mbr[510:512] != b"\x55\xaa":
    raise SystemExit("Invalid MBR signature")
parts=[]
for i in range(4):
    entry=mbr[446+16*i:446+16*(i+1)]
    typ=entry[4]
    start,count=struct.unpack_from("<II",entry,8)
    if count: parts.append((typ,start,count))
roots=[p for p in parts if p[0]==0x83]
if len(roots)!=1: raise SystemExit(f"Expected one Linux MBR partition, got {parts}")
typ,start,count=roots[0]
print(f"Root partition: start={start}, sectors={count}")
with open("/work/disk.img","rb") as src, open("/work/root.ext4","wb") as dst:
    src.seek(start*512)
    remaining=count*512
    while remaining:
        block=src.read(min(4*1024*1024,remaining))
        if not block: raise SystemExit("Truncated disk image")
        dst.write(block); remaining-=len(block)
PY
    # Keep Unix permissions and symlinks on the container filesystem, not the
    # macOS bind mount. A fresh directory also avoids stale files on reruns.
    rootfs=$(mktemp -d /tmp/rpi-rootfs.XXXXXX)
    debugfs -R "rdump / $rootfs" /work/root.ext4 >/work/debugfs.log 2>&1 || { cat /work/debugfs.log; exit 1; }
    test -f "$rootfs/etc/os-release" || { echo "Rootfs extraction failed"; exit 1; }
    # Clear image-specific machine identity; never run boot services inside Docker.
    # Replace rather than truncate: the image may contain a read-only file or
    # a symlink, which must not be followed outside the extracted rootfs.
    rm -f "$rootfs/etc/machine-id"
    install -m 0444 /dev/null "$rootfs/etc/machine-id"
    rm -f "$rootfs/var/lib/dbus/machine-id"
    tar -C "$rootfs" --numeric-owner -cf /work/rootfs.tar .
  '
echo 'Importing extracted Raspberry Pi OS userland...'
docker import --platform linux/arm64 work/rootfs.tar rpi-os-lite-rootfs:trixie-arm64
printf '\nBase image imported. Build app layer:\n  docker compose build\n  docker compose run --rm pi-os\n'
