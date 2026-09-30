// v0：最直白的 baseline
// - 每次 MAC 都直接從 HBM 讀 a、b（沒有任何 on-chip reuse）
// - 存取 stride = C，無法形成有效的 burst
// - k 迴圈是 float 累加，受限於 fadd latency，II 會 > 1
#include "trimul.h"

extern "C" void trimul_v0(const float* a, const float* b, float* z, int L) {
#pragma HLS INTERFACE m_axi port = a bundle = gmem0 depth = DEPTH_F32
#pragma HLS INTERFACE m_axi port = b bundle = gmem1 depth = DEPTH_F32
#pragma HLS INTERFACE m_axi port = z bundle = gmem2 depth = DEPTH_F32

loop_i:
    for (int i = 0; i < L; i++) {
#pragma HLS LOOP_TRIPCOUNT min = L_TRIP max = L_TRIP
    loop_j:
        for (int j = 0; j < L; j++) {
#pragma HLS LOOP_TRIPCOUNT min = L_TRIP max = L_TRIP
        loop_c:
            for (int c = 0; c < C; c++) {
                float acc = 0.0f;
            loop_k:
                for (int k = 0; k < L; k++) {
#pragma HLS LOOP_TRIPCOUNT min = L_TRIP max = L_TRIP
#pragma HLS PIPELINE
                    acc += a[(i * L + k) * C + c] * b[(j * L + k) * C + c];
                }
                z[(i * L + j) * C + c] = acc;
            }
        }
    }
}
