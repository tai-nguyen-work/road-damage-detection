# Raspberry Pi OS Lite ARM64 userland on Docker Desktop (Apple Silicon)

This project builds **one** software environment using the root filesystem extracted from the **official Raspberry Pi OS Lite 64-bit (Debian Trixie)** disk image. This is **not** a Pi 5 hardware emulator, and `uname -r` reports the Docker VM kernel.

## Requirements
- macOS Apple Silicon, Docker Desktop running, `curl`, `shasum`, `bash`
- About 10–15 GB free disk space (temporary unpacked disk image, ext4 partition, extracted rootfs, Docker images)
- Internet connection. Initial download is about 525 MB.

## Steps
```bash
chmod +x scripts/build-rootfs.sh app/verify.sh
./scripts/build-rootfs.sh
docker compose build
docker compose run --rm pi-os
```

Expected output includes Raspberry Pi OS identification in `/etc/os-release`, `arm64` / `aarch64`, APT metadata, GCC and OpenCV version, and `PASS: OS / APT / GCC / OpenCV`.

To open a shell:
```bash
docker compose run --rm pi-os /bin/bash
```

**Reproducibility:** This starter pins the official 2026-10-06 Raspberry Pi OS Lite ARM64 image and verifies the compressed image SHA-256 before extraction. To change versions, set both `IMAGE_URL` and `EXPECTED_SHA256`, and delete the cached `downloads/raspios-lite.img.xz`.

**Implementation notes:** The script decompresses the official image in an ARM64 Alpine helper container, parses its MBR partition table, extracts the Linux ext4 partition with `debugfs`, and imports a rootfs tar as a local Docker image. No privileged containers, macOS loop mounts or QEMU system emulation required. Some device/boot-specific Raspberry Pi OS services are irrelevant to container execution. `debugfs rdump` may not preserve every filesystem metadata attribute (e.g. ACLs, xattrs); the resulting container is a userland approximation, not a bit-for-bit bootable OS. Confirm APT and compiler smoke tests on your machine before relying on it.

**Not yet included:** ONNX Runtime, NCNN, GPS replay, model inference, benchmark or dashboard.

**Rootfs extraction permissions:** Extraction uses a fresh directory on the helper container’s Linux filesystem so Unix permissions and symlinks do not depend on macOS bind-mount behavior. The script replaces the image’s potentially read-only `/etc/machine-id` with an empty, mode `0444` file before archiving. Only the resulting `work/rootfs.tar` and intermediate disk images/log are written to the host; an old `work/rootfs` directory is no longer used. Ensure Docker Desktop also has enough disk space for the temporary extracted filesystem.
