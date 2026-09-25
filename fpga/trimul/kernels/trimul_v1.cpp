// v1：Tiling + on-chip buffer
// - 一次算 TI x TJ 個 (i, j) 輸出，累加器 acc 留在 on-chip（BRAM）
// - 每個 k 只把 a 的 TI 個 token、b 的 TJ 個 token 搬進來，各重複使用 TJ / TI 次
//   → off-chip 讀取量從 2*L^3*C 降為 L^3*C*(1/TI + 1/TJ)
// - 每次載入 C 個連續 float → 可以形成 burst
// - 仍是 32-bit port、每 cycle 1 個 MAC
#include "trimul.h"

extern "C" void trimul_v1(const float* a, const float* b, float* z, int L) {
#pragma HLS INTERFACE m_axi port = a bundle = gmem0 depth = DEPTH_F32
#pragma HLS INTERFACE m_axi port = b bundle = gmem1 depth = DEPTH_F32
#pragma HLS INTERFACE m_axi port = z bundle = gmem2 depth = DEPTH_F32

    float acc[TI][TJ][C];
    float la[TI][C];
    float lb[TJ][C];

tile_i:
    for (int i0 = 0; i0 < L; i0 += TI) {
#pragma HLS LOOP_TRIPCOUNT min = L_TRIP / TI max = L_TRIP / TI
    tile_j:
        for (int j0 = 0; j0 < L; j0 += TJ) {
#pragma HLS LOOP_TRIPCOUNT min = L_TRIP / TJ max = L_TRIP / TJ
        init:
            for (int ii = 0; ii < TI; ii++)
                for (int jj = 0; jj < TJ; jj++)
                    for (int c = 0; c < C; c++) {
#pragma HLS PIPELINE II = 1
                        acc[ii][jj][c] = 0.0f;
                    }

        loop_k:
            for (int k = 0; k < L; k++) {
#pragma HLS LOOP_TRIPCOUNT min = L_TRIP max = L_TRIP
            load_a:
                for (int ii = 0; ii < TI; ii++)
                    for (int c = 0; c < C; c++) {
#pragma HLS PIPELINE II = 1
                        la[ii][c] = a[((i0 + ii) * L + k) * C + c];
                    }
            load_b:
                for (int jj = 0; jj < TJ; jj++)
                    for (int c = 0; c < C; c++) {
#pragma HLS PIPELINE II = 1
                        lb[jj][c] = b[((j0 + jj) * L + k) * C + c];
                    }
            mac:
                for (int ii = 0; ii < TI; ii++)
                    for (int jj = 0; jj < TJ; jj++)
                        for (int c = 0; c < C; c++) {
#pragma HLS PIPELINE II = 1
// 同一個 acc 位置每 TI*TJ*C 次迭代才被更新一次，遠大於 fadd latency
#pragma HLS DEPENDENCE variable = acc inter false
                            acc[ii][jj][c] += la[ii][c] * lb[jj][c];
                        }
            }

        store:
            for (int ii = 0; ii < TI; ii++)
                for (int jj = 0; jj < TJ; jj++)
                    for (int c = 0; c < C; c++) {
#pragma HLS PIPELINE II = 1
                        z[((i0 + ii) * L + j0 + jj) * C + c] = acc[ii][jj][c];
                    }
        }
    }
}
