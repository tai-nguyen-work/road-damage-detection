#include <array>
#include <onnxruntime_cxx_api.h>
#include <net.h>
#include <algorithm>
#include <cmath>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

static const std::vector<float> input{-3.f, -1.f, 0.f, .5f, 2.f, 5.f};
static const std::vector<float> expected{0.f, 0.f, 0.f, .5f, 2.f, 5.f};

std::vector<float> run_onnx(const std::string& path) {
    Ort::Env env(ORT_LOGGING_LEVEL_WARNING, "smoke");
    Ort::SessionOptions options;
    options.SetIntraOpNumThreads(1);
    options.SetInterOpNumThreads(1);
    options.SetGraphOptimizationLevel(GraphOptimizationLevel::ORT_ENABLE_ALL);
    Ort::Session session(env, path.c_str(), options);
    Ort::MemoryInfo memory = Ort::MemoryInfo::CreateCpu(OrtArenaAllocator, OrtMemTypeDefault);
    const std::array<int64_t, 4> shape{1, 1, 2, 3};
    auto tensor = Ort::Value::CreateTensor<float>(memory, const_cast<float*>(input.data()), input.size(), shape.data(), shape.size());
    const char* names_in[] = {"input"};
    const char* names_out[] = {"output"};
    auto result = session.Run(Ort::RunOptions{nullptr}, names_in, &tensor, 1, names_out, 1);
    if (result.size() != 1 || !result[0].IsTensor()) throw std::runtime_error("ORT returned no output tensor");
    auto info = result[0].GetTensorTypeAndShapeInfo();
    if (info.GetElementCount() != input.size()) throw std::runtime_error("ORT output size mismatch");
    const float* ptr = result[0].GetTensorData<float>();
    return {ptr, ptr + input.size()};
}

std::vector<float> run_ncnn(const std::string& path) {
    ncnn::Net net;
    net.opt.use_vulkan_compute = false;
    // Compare scalar float32 values rather than NCNN packed tensor storage.
    net.opt.use_packing_layout = false;
    net.opt.use_fp16_packed = false;
    net.opt.use_fp16_storage = false;
    net.opt.use_fp16_arithmetic = false;
    net.opt.num_threads = 1;
    if (net.load_param(path.c_str()) != 0) throw std::runtime_error("NCNN load_param failed");
    // The ReLU network contains no learned weights; load_model() is unnecessary.
    ncnn::Mat tensor(3, 2, 1);
    std::copy(input.begin(), input.end(), static_cast<float*>(tensor.data));
    ncnn::Extractor ex = net.create_extractor();
    if (ex.input("input", tensor) != 0) throw std::runtime_error("NCNN input failed");
    ncnn::Mat out;
    if (ex.extract("output", out) != 0) throw std::runtime_error("NCNN extract failed");
    // total() includes channel alignment padding (cstep), not just values.
    if (out.w != 3 || out.h != 2 || out.c != 1 || out.elempack != 1 || out.elemsize != sizeof(float))
        throw std::runtime_error("NCNN output shape/precision mismatch");
    const float* ptr = static_cast<const float*>(out.data);
    return {ptr, ptr + input.size()};
}

void check(const char* name, const std::vector<float>& values) {
    if (values.size() != expected.size()) throw std::runtime_error(std::string(name) + " wrong count");
    std::cout << name << ": [";
    for (size_t i = 0; i < values.size(); ++i) {
        if (i) std::cout << ", ";
        std::cout << values[i];
        if (!std::isfinite(values[i]) || std::abs(values[i] - expected[i]) > 1e-6f)
            throw std::runtime_error(std::string(name) + " wrong value at index " + std::to_string(i));
    }
    std::cout << "] PASS\n";
}

int main(int argc, char** argv) {
    try {
        const std::string dir = argc > 1 ? argv[1] : "models";
        auto ort = run_onnx(dir + "/relu.onnx");
        auto ncnn = run_ncnn(dir + "/relu.param");
        check("ONNX Runtime", ort);
        check("NCNN", ncnn);
        for (size_t i = 0; i < ort.size(); ++i)
            if (std::abs(ort[i] - ncnn[i]) > 1e-6f) throw std::runtime_error("Runtime outputs differ");
        std::cout << "PASS: ONNX Runtime and NCNN C++ inference agree\n";
        return 0;
    } catch (const std::exception& e) {
        std::cerr << "FAIL: " << e.what() << "\n";
        return 1;
    }
}
