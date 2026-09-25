// v4：v2 + INT8 token-wise 量化（呼應 LightNobel 的 activation quantization）
// - a, b 以 int8 存放，每個 token（每個 (row, col) 位置）有自己的 float scale：
//     a[i][k][c] ≈ sa[i][k] * qa[i][k][c]
// - 512-bit 一次搬 64 個 int8 → 同樣頻寬下，搬的資料量是 FP32 的 4 倍
// - HBM 占用量變成 1/4 → 同一塊記憶體可以放更長的序列
// - 若 host 把所有 scale 設成同一個值，就等同 per-tensor 量化（可用來比較精度）
#include "trimul.h"

extern "C" void trimul_v4(const q64* qa, const q64* qb, const float* sa, const float* sb,
                          f16* z, int L) {
#pragma HLS INTERFACE m_axi port = qa bundle = gmem0 depth = DEPTH_Q64
#pragma HLS INTERFACE m_axi port = qb bundle = gmem1 depth = DEPTH_Q64
#pragma HLS INTERFACE m_axi port = sa bundle = gmem3 depth = DEPTH_SCALE
#pragma HLS INTERFACE m_axi port = sb bundle = gmem4 depth = DEPTH_SCALE
#pragma HLS INTERFACE m_axi port = z bundle = gmem2 depth = DEPTH_F16

    float acc[TI * TJ * QW][QLANES];
    int8_t la[TI * QW][QLANES];
    int8_t lb[TJ * QW][QLANES];
    float lsa[TI], lsb[TJ];
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
            for (int r = 0; r < TI * TJ * QW; r++) {
#pragma HLS PIPELINE II = 1
                for (int l = 0; l < QLANES; l++) acc[r][l] = 0.0f;
            }

        loop_k:
            for (int k = 0; k < L; k++) {
#pragma HLS LOOP_TRIPCOUNT min = L_TRIP max = L_TRIP
            load_a:
                for (int r = 0; r < TI * QW; r++) {
#pragma HLS PIPELINE II = 1
                    int ii = r / QW, w = r % QW;
                    q64 t = qa[((i0 + ii) * L + k) * QW + w];
                    for (int l = 0; l < QLANES; l++) la[r][l] = t.v[l];
                }
            load_b:
                for (int r = 0; r < TJ * QW; r++) {
#pragma HLS PIPELINE II = 1
                    int jj = r / QW, w = r % QW;
                    q64 t = qb[((j0 + jj) * L + k) * QW + w];
                    for (int l = 0; l < QLANES; l++) lb[r][l] = t.v[l];
                }
            load_s:
                for (int ii = 0; ii < TI; ii++) {
#pragma HLS PIPELINE II = 1
                    lsa[ii] = sa[(i0 + ii) * L + k];
                }
                for (int jj = 0; jj < TJ; jj++) {
#pragma HLS PIPELINE II = 1
                    lsb[jj] = sb[(j0 + jj) * L + k];
                }
            mac:
                for (int r = 0; r < TI * TJ * QW; r++) {
#pragma HLS PIPELINE II = 1
#pragma HLS DEPENDENCE variable = acc inter false
                    int ii = r / (TJ * QW), jj = (r / QW) % TJ, w = r % QW;
                    float s = lsa[ii] * lsb[jj];
                    for (int l = 0; l < QLANES; l++) {
                        int16_t p = (int16_t)la[ii * QW + w][l] * (int16_t)lb[jj * QW + w][l];
                        acc[r][l] += (float)p * s;
                    }
                }
            }

        // 每個 acc row 有 64 個 float = 4 個 512-bit 輸出 word
        store:
            for (int r = 0; r < TI * TJ * QW; r++) {
                for (int q = 0; q < QLANES / LANES; q++) {
#pragma HLS PIPELINE II = 1
                    int ii = r / (TJ * QW), jj = (r / QW) % TJ, w = r % QW;
                    f16 t;
                    for (int l = 0; l < LANES; l++) t.v[l] = acc[r][q * LANES + l];
                    z[((i0 + ii) * L + j0 + jj) * CW + w * (QLANES / LANES) + q] = t;
                }
            }
        }
    }
}
