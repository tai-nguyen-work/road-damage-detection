FROM rpi-os-lite-rootfs:trixie-arm64

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    pkg-config \
    libopencv-dev \
    libonnxruntime-dev \
    libprotobuf-dev \
    protobuf-compiler \
    && rm -rf /var/lib/apt/lists/*

# NCNN: CPU-only, ARM64
RUN git clone --depth 1 \
    https://github.com/Tencent/ncnn.git /opt/ncnn \
    && cmake -S /opt/ncnn -B /opt/ncnn/build \
       -DCMAKE_BUILD_TYPE=Release \
       -DCMAKE_INSTALL_PREFIX=/usr/local \
       -DNCNN_VULKAN=OFF \
       -DNCNN_BUILD_EXAMPLES=OFF \
       -DNCNN_BUILD_TESTS=OFF \
       -DNCNN_BUILD_BENCHMARK=OFF \
       -DNCNN_BUILD_TOOLS=OFF \
       -DNCNN_PYTHON=OFF \
    && cmake --build /opt/ncnn/build --parallel 4 \
    && cmake --install /opt/ncnn/build

WORKDIR /workspace
COPY app /workspace/app
CMD ["/bin/bash"]