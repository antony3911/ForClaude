// host 與 testbench 共用：產生測試資料、量化、CPU 參考答案、誤差計算
#pragma once
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <random>
#include <vector>

#include "../kernels/trimul.h"

// 產生 L x L x C 的 activation。outlier_ratio 比例的 token 會被放大 outlier_scale 倍，
// 模擬 PPM activation 中少數 token 數值特別大的情況（這正是 token-wise 量化要處理的問題）
inline std::vector<float> make_activation(int L, unsigned seed, double outlier_ratio = 0.01,
                                          float outlier_scale = 30.0f) {
    std::mt19937 rng(seed);
    std::normal_distribution<float> nd(0.0f, 1.0f);
    std::uniform_real_distribution<double> ud(0.0, 1.0);
    std::vector<float> x((size_t)L * L * C);
    for (size_t t = 0; t < (size_t)L * L; t++) {
        float s = ud(rng) < outlier_ratio ? outlier_scale : 1.0f;
        for (int c = 0; c < C; c++) x[t * C + c] = nd(rng) * s;
    }
    return x;
}

// 對稱 INT8 量化。per_token = true：每個 token 一個 scale；false：整個 tensor 一個 scale
inline void quantize(const std::vector<float>& x, int L, bool per_token, std::vector<int8_t>& q,
                     std::vector<float>& s) {
    size_t T = (size_t)L * L;
    q.resize(T * C);
    s.resize(T);
    float gmax = 0.0f;
    if (!per_token)
        for (float v : x) gmax = std::max(gmax, std::fabs(v));
    for (size_t t = 0; t < T; t++) {
        float m = gmax;
        if (per_token) {
            m = 0.0f;
            for (int c = 0; c < C; c++) m = std::max(m, std::fabs(x[t * C + c]));
        }
        float sc = m > 0.0f ? m / 127.0f : 1.0f;
        s[t] = sc;
        for (int c = 0; c < C; c++) {
            float r = std::round(x[t * C + c] / sc);
            q[t * C + c] = (int8_t)std::max(-127.0f, std::min(127.0f, r));
        }
    }
}

// CPU 參考答案（單一輸出元素）；用 double 累加
inline double ref_elem(const std::vector<float>& a, const std::vector<float>& b, int L, int i,
                       int j, int c) {
    double acc = 0.0;
    for (int k = 0; k < L; k++)
        acc += (double)a[((size_t)i * L + k) * C + c] * b[((size_t)j * L + k) * C + c];
    return acc;
}

struct ErrStat {
    double max_abs = 0.0;
    double rel_l2 = 0.0;  // ||z - ref|| / ||ref||
};

// 隨機抽樣 n 個輸出位置比對（L 大時完整 CPU 參考答案太慢）；n <= 0 表示全部比對
inline ErrStat compare(const std::vector<float>& z, const std::vector<float>& a,
                       const std::vector<float>& b, int L, int n, unsigned seed = 123) {
    std::mt19937 rng(seed);
    double num = 0.0, den = 0.0;
    ErrStat e;
    auto one = [&](int i, int j, int c) {
        double r = ref_elem(a, b, L, i, j, c);
        double d = z[((size_t)i * L + j) * C + c] - r;
        e.max_abs = std::max(e.max_abs, std::fabs(d));
        num += d * d;
        den += r * r;
    };
    if (n <= 0) {
        for (int i = 0; i < L; i++)
            for (int j = 0; j < L; j++)
                for (int c = 0; c < C; c++) one(i, j, c);
    } else {
        std::uniform_int_distribution<int> ul(0, L - 1), uc(0, C - 1);
        for (int t = 0; t < n; t++) one(ul(rng), ul(rng), uc(rng));
    }
    e.rel_l2 = std::sqrt(num / std::max(den, 1e-30));
    return e;
}
