# ONNX Runtime + NCNN smoke test (C++17, Raspberry Pi OS ARM64)

This test runs an identical ReLU computation in both runtimes, validates against
known values, then compares outputs element by element. It is **not** a performance
benchmark or a YOLO test.

## Run from the existing `rpi-os-docker` project

1. Extract this folder as `edge-runtime-smoke` **inside** your `rpi-os-docker`
   project directory (next to Dockerfile and compose.yaml).
2. Open a shell in the existing container:

```sh
docker compose run --rm pi-os bash
```

3. Inside the container, assuming your compose file mounts the project directory
   at `/workspace`:

```sh
cd /workspace/edge-runtime-smoke
python3 scripts/make_models.py
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j 4
./build/runtime_smoke models
```

If `python3` is missing: `apt-get update && apt-get install -y python3` (prefer
adding python3 to Dockerfile for persistence).

If `/workspace/edge-runtime-smoke` is not visible, your Compose configuration does
not bind-mount the project. Add `volumes: [".:/workspace"]` under service `pi-os`,
or copy the files into the image and rebuild.

If CMake cannot find NCNN, pass its config directory explicitly:

```sh
find /usr/local -name ncnnConfig.cmake
cmake -S . -B build -Dncnn_DIR=/usr/local/lib/cmake/ncnn
```

Expected final line:

```
PASS: ONNX Runtime and NCNN C++ inference agree
```

The NCNN model is a text `.param` file only; ReLU has no learned weights so a
`.bin` is not needed. The ONNX model is generated using Python's standard
library, without pip dependencies.

For later benchmarking, pin the NCNN source commit, record ONNX Runtime package
version, and compare models converted from identical trained weights.
