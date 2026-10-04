"""量這台 GPU 的實際天花板：矩陣乘法算力（FP32、FP16）、記憶體頻寬、最小 kernel 時間。

不用規格表，因為筆電 GPU 的時脈隨功耗、溫度改變；roofline 模型要用實際量到的數字。
用 CUDA event 計時：先暖機，再重複多次取中位數。
"""
import json
import os
import statistics
import subprocess

import torch

torch.backends.cuda.matmul.allow_tf32 = False  # 和 HF ESMFold 的預設相同：FP32 矩陣乘法不用 TF32


def gpu_time(fn, reps=20, warmup=5):
    for _ in range(warmup):
        fn()
    torch.cuda.synchronize()
    times = []
    for _ in range(reps):
        a, b = torch.cuda.Event(enable_timing=True), torch.cuda.Event(enable_timing=True)
        a.record()
        fn()
        b.record()
        torch.cuda.synchronize()
        times.append(a.elapsed_time(b) / 1e3)
    return statistics.median(times)


def matmul_tflops(dtype, n=4096):
    x = torch.randn(n, n, device="cuda", dtype=dtype)
    y = torch.randn(n, n, device="cuda", dtype=dtype)
    t = gpu_time(lambda: x @ y)
    return 2 * n ** 3 / t / 1e12


def bandwidth_gbs(nbytes=1 << 30):
    x = torch.empty(nbytes // 4, device="cuda", dtype=torch.float32)
    y = torch.empty_like(x)
    t = gpu_time(lambda: y.copy_(x))
    return 2 * nbytes / t / 1e9  # 讀一次、寫一次


def min_kernel_us():
    x = torch.zeros(1, device="cuda")
    t = gpu_time(lambda: [x.add_(1) for _ in range(1000)], reps=10)
    return t / 1000 * 1e6


def clocks():
    q = "clocks.sm,clocks.mem,power.draw,temperature.gpu"
    out = subprocess.run(["nvidia-smi", f"--query-gpu={q}", "--format=csv,noheader"], capture_output=True, text=True)
    return out.stdout.strip()


def main():
    res = {
        "gpu": torch.cuda.get_device_name(),
        "fp32_matmul_tflops": round(matmul_tflops(torch.float32), 2),
        "fp16_matmul_tflops": round(matmul_tflops(torch.float16), 2),
        "bandwidth_gbs": round(bandwidth_gbs(), 1),
        "min_kernel_us": round(min_kernel_us(), 2),
        "clocks_after": clocks(),
    }
    for k, v in res.items():
        print(f"{k}: {v}")
    out = os.path.join(os.path.dirname(__file__), "results", "ceilings.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump(res, open(out, "w"), indent=1)


if __name__ == "__main__":
    main()
