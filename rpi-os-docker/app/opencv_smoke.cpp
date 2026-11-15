#include <opencv2/core.hpp>
#include <iostream>
int main() {
    cv::Mat image(48, 64, CV_8UC3, cv::Scalar(10, 20, 30));
    if (image.empty() || image.rows != 48 || image.cols != 64) return 1;
    std::cout << "OpenCV " << CV_VERSION << " OK; pixels=" << image.total() << '\n';
    return 0;
}
