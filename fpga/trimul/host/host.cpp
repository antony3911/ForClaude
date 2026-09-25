// 上板（或 emulation）用的 host 程式，使用 XRT native C++ API
//
// 用法：
//   ./host.exe <xclbin> <kernel> <L> [reps=3] [quant=token|tensor] [samples=2000]
// 例：
//   ./host.exe build/hw/trimul_v2.xclbin trimul_v2 512
//   ./host.exe build/hw/trimul_v4.xclbin trimul_v4 512 3 tensor
//
// 最後一行會印出 CSV，方便收集成表格：
//   CSV,kernel,L,time_ms,gflops,est_traffic_GB,est_GBps,hbm_footprint_MB,rel_l2,max_abs
#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>

#include "common.h"
#include "xrt/xrt_bo.h"
#include "xrt/xrt_device.h"
#include "xrt/xrt_kernel.h"

int main(int argc, char** argv) {
    if (argc < 4) {
        std::printf("usage: %s <xclbin> <kernel> <L> [reps] [token|tensor] [samples]\n", argv[0]);
        return 1;
    }
    std::string xclbin = argv[1], kname = argv[2];
    int L = std::atoi(argv[3]);
    int reps = argc > 4 ? std::atoi(argv[4]) : 3;
    bool per_token = argc > 5 ? std::string(argv[5]) != "tensor" : true;
    int samples = argc > 6 ? std::atoi(argv[6]) : 2000;
    if (L % TI || L % TJ) {
        std::printf("L 必須是 TILE_I(%d) 與 TILE_J(%d) 的倍數\n", TI, TJ);
        return 1;
    }
    bool quant = kname == "trimul_v4";

    size_t T = (size_t)L * L;
    size_t f32_bytes = T * C * sizeof(float);
    std::printf("kernel=%s L=%d C=%d tile=%dx%d quant=%s\n", kname.c_str(), L, C, TI, TJ,
                quant ? (per_token ? "per-token" : "per-tensor") : "none");

    std::printf("產生測試資料...\n");
    auto a = make_activation(L, 1);
    auto b = make_activation(L, 2);
    std::vector<float> z(T * C);

    xrt::device dev(0);
    auto uuid = dev.load_xclbin(xclbin);
    xrt::kernel krnl(dev, uuid, kname);

    double footprint = 0.0;
    xrt::run run;
    xrt::bo bo_z;
    std::vector<xrt::bo> keep;  // 保持 buffer 存活

    if (!quant) {
        xrt::bo bo_a(dev, f32_bytes, krnl.group_id(0));
        xrt::bo bo_b(dev, f32_bytes, krnl.group_id(1));
        bo_z = xrt::bo(dev, f32_bytes, krnl.group_id(2));
        bo_a.write(a.data());
        bo_b.write(b.data());
        bo_a.sync(XCL_BO_SYNC_BO_TO_DEVICE);
        bo_b.sync(XCL_BO_SYNC_BO_TO_DEVICE);
        run = xrt::run(krnl);
        run.set_arg(0, bo_a);
        run.set_arg(1, bo_b);
        run.set_arg(2, bo_z);
        run.set_arg(3, L);
        keep = {bo_a, bo_b};
        footprint = 3.0 * f32_bytes;
    } else {
        // 量化在 host 端做（不計入 kernel 時間）
        std::vector<int8_t> qa, qb;
        std::vector<float> sa, sb;
        quantize(a, L, per_token, qa, sa);
        quantize(b, L, per_token, qb, sb);
        xrt::bo bo_qa(dev, T * C, krnl.group_id(0));
        xrt::bo bo_qb(dev, T * C, krnl.group_id(1));
        xrt::bo bo_sa(dev, T * sizeof(float), krnl.group_id(2));
        xrt::bo bo_sb(dev, T * sizeof(float), krnl.group_id(3));
        bo_z = xrt::bo(dev, f32_bytes, krnl.group_id(4));
        bo_qa.write(qa.data());
        bo_qb.write(qb.data());
        bo_sa.write(sa.data());
        bo_sb.write(sb.data());
        for (auto* bo : {&bo_qa, &bo_qb, &bo_sa, &bo_sb}) bo->sync(XCL_BO_SYNC_BO_TO_DEVICE);
        run = xrt::run(krnl);
        run.set_arg(0, bo_qa);
        run.set_arg(1, bo_qb);
        run.set_arg(2, bo_sa);
        run.set_arg(3, bo_sb);
        run.set_arg(4, bo_z);
        run.set_arg(5, L);
        keep = {bo_qa, bo_qb, bo_sa, bo_sb};
        footprint = 2.0 * T * C + 2.0 * T * sizeof(float) + f32_bytes;
    }

    // 執行 reps 次取最小值（第一次可能包含暖機開銷）
    double best_ms = 1e30;
    for (int r = 0; r < reps; r++) {
        auto t0 = std::chrono::high_resolution_clock::now();
        run.start();
        run.wait();
        auto t1 = std::chrono::high_resolution_clock::now();
        double ms = std::chrono::duration<double, std::milli>(t1 - t0).count();
        std::printf("  run %d: %.3f ms\n", r, ms);
        best_ms = std::min(best_ms, ms);
    }

    bo_z.sync(XCL_BO_SYNC_BO_FROM_DEVICE);
    bo_z.read(z.data());

    // 理論 off-chip 流量（依各版本的資料重用方式估算），用來畫 roofline
    double L3C = (double)L * L * L * C;
    double traffic;
    if (kname == "trimul_v0")
        traffic = 2.0 * L3C * 4;
    else if (!quant)
        traffic = L3C * 4 * (1.0 / TI + 1.0 / TJ);
    else
        traffic = L3C * 1 * (1.0 / TI + 1.0 / TJ) + (double)L * L * L * 4 * (1.0 / TI + 1.0 / TJ);
    traffic += (double)f32_bytes;  // 寫回 z

    double flops = 2.0 * L3C;
    double gflops = flops / (best_ms * 1e6);
    double gbps = traffic / (best_ms * 1e6);
    ErrStat e = compare(z, a, b, L, samples);

    std::printf("best: %.3f ms, %.2f GFLOP/s, 估計流量 %.3f GB (%.2f GB/s), HBM 占用 %.1f MB\n",
                best_ms, gflops, traffic / 1e9, gbps, footprint / 1e6);
    std::printf("error (抽樣 %d 點): rel_l2=%.3e max_abs=%.3e\n", samples, e.rel_l2, e.max_abs);
    std::printf("CSV,%s%s,%d,%.3f,%.3f,%.4f,%.3f,%.1f,%.3e,%.3e\n", kname.c_str(),
                quant ? (per_token ? "_token" : "_tensor") : "", L, best_ms, gflops,
                traffic / 1e9, gbps, footprint / 1e6, e.rel_l2, e.max_abs);
    return 0;
}
