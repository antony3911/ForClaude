// C simulation testbench：不需要 FPGA，也不需要 Vitis，一般 g++ 就能跑
//   make csim
// 在 Vitis HLS 裡也可以當 testbench 用（csim_design / cosim_design）
#include <cstdio>
#include <cstring>

#include "../host/common.h"

int main(int argc, char** argv) {
    // 用法：csim.exe [L] [資料目錄]
    //   給資料目錄時改用真實 ESMFold 資料（L 由檔案決定）
    int L = argc > 1 ? std::atoi(argv[1]) : 16;  // cosim 時必須 <= L_COSIM
    std::vector<float> a, b;
    if (argc > 2) {
        L = load_real_data(argv[2], a, b);
        if (!L) return 1;
        std::printf("使用真實資料 %s，L = %d\n", argv[2], L);
    } else {
        a = make_activation(L, 1);
        b = make_activation(L, 2);
    }
    if (L % TI || L % TJ) {
        std::printf("L 必須是 TILE_I(%d) 與 TILE_J(%d) 的倍數\n", TI, TJ);
        return 1;
    }
    std::vector<float> z((size_t)L * L * C);
    int fail = 0;

    auto check = [&](const char* name, double tol) {
        ErrStat e = compare(z, a, b, L, 0);
        bool ok = e.rel_l2 < tol;
        fail += !ok;
        std::printf("%-28s rel_l2=%.3e max_abs=%.3e  %s\n", name, e.rel_l2, e.max_abs,
                    ok ? "PASS" : "FAIL");
    };

    std::fill(z.begin(), z.end(), 0.0f);
    trimul_v0(a.data(), b.data(), z.data(), L);
    check("v0 naive", 1e-5);

    std::fill(z.begin(), z.end(), 0.0f);
    trimul_v1(a.data(), b.data(), z.data(), L);
    check("v1 tiled", 1e-5);

    std::fill(z.begin(), z.end(), 0.0f);
    trimul_v2((const f16*)a.data(), (const f16*)b.data(), (f16*)z.data(), L);
    check("v2 tiled+wide", 1e-5);

    std::fill(z.begin(), z.end(), 0.0f);
    trimul_v3((const f16*)a.data(), (const f16*)b.data(), (f16*)z.data(), L);
    check("v3 tiled+wide+pingpong", 1e-5);

    for (int per_token = 1; per_token >= 0; per_token--) {
        std::vector<int8_t> qa, qb;
        std::vector<float> sa, sb;
        quantize(a, L, per_token, qa, sa);
        quantize(b, L, per_token, qb, sb);
        std::fill(z.begin(), z.end(), 0.0f);
        trimul_v4((const q64*)qa.data(), (const q64*)qb.data(), sa.data(), sb.data(),
                  (f16*)z.data(), L);
        // 量化本來就有誤差，這裡只檢查功能正確（誤差在合理範圍）
        check(per_token ? "v4 int8 per-token" : "v4 int8 per-tensor", per_token ? 2e-2 : 1.0);
    }

    std::printf(fail ? "\n有 %d 項 FAIL\n" : "\nALL PASS\n", fail);
    return fail ? 1 : 0;
}
