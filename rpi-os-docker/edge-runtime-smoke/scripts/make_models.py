#!/usr/bin/env python3
"""Generate a minimal ONNX ReLU model and a weightless NCNN ReLU model.
No third-party Python dependencies required.
"""
from pathlib import Path


def varint(n):
    out = bytearray()
    while n >= 128:
        out.append((n & 127) | 128)
        n >>= 7
    out.append(n)
    return bytes(out)


def vi(field, n):
    return varint(field << 3) + varint(n)


def b(field, payload):
    if isinstance(payload, str):
        payload = payload.encode()
    return varint((field << 3) | 2) + varint(len(payload)) + payload


def value_info(name):
    dims = b''.join(b(1, vi(1, d)) for d in [1, 1, 2, 3])
    tensor_type = vi(1, 1) + b(2, dims)  # FLOAT, shape
    type_proto = b(1, tensor_type)
    return b(1, name) + b(2, type_proto)


def main():
    models = Path(__file__).resolve().parent.parent / 'models'
    models.mkdir(exist_ok=True)
    node = b(1, 'input') + b(2, 'output') + b(3, 'relu') + b(4, 'Relu')
    graph = b(1, node) + b(2, 'relu_smoke') + b(11, value_info('input')) + b(12, value_info('output'))
    opset = vi(2, 13)
    model = vi(1, 9) + b(2, 'edge-runtime-smoke') + b(7, graph) + b(8, opset)
    (models / 'relu.onnx').write_bytes(model)
    (models / 'relu.param').write_text('7767517\n2 2\nInput input 0 1 input\nReLU relu 1 1 input output 0=0.000000\n')
    print('Created models/relu.onnx and models/relu.param (no .bin required: no weights)')


if __name__ == '__main__':
    main()
