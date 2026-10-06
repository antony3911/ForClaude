// v2：v1 + 512-bit 寬位元 port
// - 每個 AXI beat 搬 16 個 float（一個 f16 struct），頻寬是 v1 的 16 倍
// - 16 個 channel 平行計算：每 cycle 16 個 MAC
#include "trimul.h"

extern "C" void trimul_v2(const f16* a, const f16* b, f16* z, int L) {
#pragma HLS INTERFACE m_axi port = a bundle = gmem0 depth = DEPTH_F16
#pragma HLS INTERFACE m_axi port = b bundle = gmem1 depth = DEPTH_F16
#pragma HLS INTERFACE m_axi port = z bundle = gmem2 depth = DEPTH_F16

    // 第 2 維（lane）完全切開，才能一個 cycle 同時讀寫 16 個值
    float acc[TI * TJ * CW][LANES];
    float la[TI * CW][LANES];
    float lb[TJ * CW][LANES];
#pragma HLS ARRAY_PARTITION variable = acc dim = 2 complete
#pragma HLS ARRAY_PARTITION variable = la dim = 2 complete
#pragma HLS ARRAY_PARTITION variable = lb dim = 2 complete

tile_i:
    for (int i0 = 0; i0 < L; i0 += TI) {
#pragma HLS LOOP_TRIPCOUNT min = L_TRIP / TI max = L_TRIP / TI
    tile_j:
        for (int j0 = 0; j0 < L; j0 += TJ) {
#pragma HLS LOOP_TRIPCOUNT min = L_TRIP / TJ max = L_TRIP / TJ
        init:
            for (int r = 0; r < TI * TJ * CW; r++) {
#pragma HLS PIPELINE II = 1
                for (int l = 0; l < LANES; l++) acc[r][l] = 0.0f;
            }

        loop_k:
            for (int k = 0; k < L; k++) {
#pragma HLS LOOP_TRIPCOUNT min = L_TRIP max = L_TRIP
            load_a:
                for (int r = 0; r < TI * CW; r++) {
#pragma HLS PIPELINE II = 1
                    int ii = r / CW, w = r % CW;
                    f16 t = a[((i0 + ii) * L + k) * CW + w];
                    for (int l = 0; l < LANES; l++) la[r][l] = t.v[l];
                }
            load_b:
                for (int r = 0; r < TJ * CW; r++) {
#pragma HLS PIPELINE II = 1
                    int jj = r / CW, w = r % CW;
                    f16 t = b[((j0 + jj) * L + k) * CW + w];
                    for (int l = 0; l < LANES; l++) lb[r][l] = t.v[l];
                }
            mac:
                for (int r = 0; r < TI * TJ * CW; r++) {
#pragma HLS PIPELINE II = 1
#pragma HLS DEPENDENCE variable = acc inter false
                    int ii = r / (TJ * CW), jj = (r / CW) % TJ, w = r % CW;
                    for (int l = 0; l < LANES; l++)
                        acc[r][l] += la[ii * CW + w][l] * lb[jj * CW + w][l];
                }
            }

        store:
            for (int r = 0; r < TI * TJ * CW; r++) {
#pragma HLS PIPELINE II = 1
                int ii = r / (TJ * CW), jj = (r / CW) % TJ, w = r % CW;
                f16 t;
                for (int l = 0; l < LANES; l++) t.v[l] = acc[r][l];
                z[((i0 + ii) * L + j0 + jj) * CW + w] = t;
            }
        }
    }
}
