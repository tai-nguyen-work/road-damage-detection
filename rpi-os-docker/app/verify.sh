#!/usr/bin/env bash
set -euo pipefail
printf '\n=== Raspberry Pi OS identity ===\n'
cat /etc/os-release
printf '\n=== Architecture ===\n'
dpkg --print-architecture
uname -m
printf '\n=== APT ===\n'
apt-get update -qq
apt-cache policy libopencv-dev | head -12
printf '\n=== GCC / G++ ===\n'
gcc --version | head -1
g++ --version | head -1
printf '\n=== OpenCV pkg-config ===\n'
pkg-config --modversion opencv4
printf '\n=== OpenCV C++ compile & runtime test ===\n'
g++ -std=c++17 /workspace/app/opencv_smoke.cpp -o /tmp/opencv_smoke $(pkg-config --cflags --libs opencv4)
/tmp/opencv_smoke
printf '\nPASS: OS / APT / GCC / OpenCV\n'
