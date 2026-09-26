// v3：v2 + double buffering（ping-pong）
// - 兩組 la/lb buffer 輪流使用：計算第 k 步的同時載入第 k+1 步
// - 讓「搬資料」與「計算」時間重疊，隱藏 memory latency
#include "trimul.h"

static void load_ab(const f16* a, const f16* b, int i0, int j0, int k, int L,
                    float la[TI * CW][LANES], float lb[TJ * CW][LANES]) {
#pragma HLS INLINE off
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
}

static void mac(float la[TI * CW][LANES], float lb[TJ * CW][LANES],
                float acc[TI * TJ * CW][LANES]) {
#pragma HLS INLINE off
mac:
    for (int r = 0; r < TI * TJ * CW; r++) {
#pragma HLS PIPELINE II = 1
#pragma HLS DEPENDENCE variable = acc inter false
        int ii = r / (TJ * CW), jj = (r / CW) % TJ, w = r % CW;
        for (int l = 0; l < LANES; l++)
            acc[r][l] += la[ii * CW + w][l] * lb[jj * CW + w][l];
    }
}

extern "C" void trimul_v3(const f16* a, const f16* b, f16* z, int L) {
#pragma HLS INTERFACE m_axi port = a bundle = gmem0 depth = DEPTH_F16
#pragma HLS INTERFACE m_axi port = b bundle = gmem1 depth = DEPTH_F16
#pragma HLS INTERFACE m_axi port = z bundle = gmem2 depth = DEPTH_F16

    float acc[TI * TJ * CW][LANES];
    float la0[TI * CW][LANES], lb0[TJ * CW][LANES];
    float la1[TI * CW][LANES], lb1[TJ * CW][LANES];
#pragma HLS ARRAY_PARTITION variable = acc dim = 2 complete
#pragma HLS ARRAY_PARTITION variable = la0 dim = 2 complete
#pragma HLS ARRAY_PARTITION variable = lb0 dim = 2 complete
#pragma HLS ARRAY_PARTITION variable = la1 dim = 2 complete
#pragma HLS ARRAY_PARTITION variable = lb1 dim = 2 complete

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

            load_ab(a, b, i0, j0, 0, L, la0, lb0);
        loop_k:
            for (int k = 0; k < L; k++) {
#pragma HLS LOOP_TRIPCOUNT min = L_TRIP max = L_TRIP
                // 兩個呼叫之間沒有資料相依 → HLS 會讓它們同時執行
                if (k % 2 == 0) {
                    if (k + 1 < L) load_ab(a, b, i0, j0, k + 1, L, la1, lb1);
                    mac(la0, lb0, acc);
                } else {
                    if (k + 1 < L) load_ab(a, b, i0, j0, k + 1, L, la0, lb0);
                    mac(la1, lb1, acc);
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
