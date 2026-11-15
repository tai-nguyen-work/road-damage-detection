cmake_minimum_required(VERSION 3.16)
project(edge_runtime_smoke LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_path(ONNXRUNTIME_INCLUDE_DIR onnxruntime_cxx_api.h
    PATHS /usr/include/onnxruntime /usr/include/onnxruntime/core/session
    PATH_SUFFIXES onnxruntime/core/session)
find_library(ONNXRUNTIME_LIBRARY NAMES onnxruntime REQUIRED)
if(NOT ONNXRUNTIME_INCLUDE_DIR)
    message(FATAL_ERROR "ONNX Runtime C++ header not found; check libonnxruntime-dev")
endif()

find_package(ncnn CONFIG REQUIRED)
add_executable(runtime_smoke src/main.cpp)
target_include_directories(runtime_smoke PRIVATE ${ONNXRUNTIME_INCLUDE_DIR})
target_link_libraries(runtime_smoke PRIVATE ${ONNXRUNTIME_LIBRARY} ncnn)
