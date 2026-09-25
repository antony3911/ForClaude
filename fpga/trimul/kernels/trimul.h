// 共用定義：Triangle Multiplication (outgoing) 的核心運算
//
//   z[i][j][c] = sum_k a[i][k][c] * b[j][k][c]
//
// a, b, z 都是 pair representation，形狀 L x L x C，記憶體排列為 [row][col][channel]，
// 也就是 index = (row * L + col) * C + c。
// 這裡只做 einsum 本身（最吃記憶體的部分），不含 LayerNorm / gating / linear projection。
#pragma once
#include <cstdint>

// ESMFold 的 pair dimension = 128
constexpr int C = 128;

// Tile 大小可在編譯時覆寫，例如 -DTILE_I=16 -DTILE_J=16，用來做 tile size sweep
#ifndef TILE_I
#define TILE_I 8
#endif
#ifndef TILE_J
#define TILE_J 8
#endif
constexpr int TI = TILE_I;
constexpr int TJ = TILE_J;

// 512-bit AXI word = 16 個 float
constexpr int LANES = 16;
constexpr int CW = C / LANES;  // 每個 token 佔幾個 512-bit word（= 8）
struct f16 {
    float v[LANES];
};

// 512-bit AXI word = 64 個 int8
constexpr int QLANES = 64;
constexpr int QW = C / QLANES;  // = 2
struct q64 {
    int8_t v[QLANES];
};

// 只影響 HLS 報告中的 latency 估計，不影響功能
constexpr int L_TRIP = 256;

// m_axi depth 只給 C/RTL co-simulation 用（決定模擬時的記憶體大小），不影響上板。
// 這裡對應 cosim 時 L = 16；如果 cosim 要用更大的 L，要跟著改。
#define L_COSIM 16
#define DEPTH_F32 (L_COSIM * L_COSIM * 128)
#define DEPTH_F16 (L_COSIM * L_COSIM * 128 / 16)
#define DEPTH_Q64 (L_COSIM * L_COSIM * 128 / 64)
#define DEPTH_SCALE (L_COSIM * L_COSIM)

extern "C" {
void trimul_v0(const float* a, const float* b, float* z, int L);
void trimul_v1(const float* a, const float* b, float* z, int L);
void trimul_v2(const f16* a, const f16* b, f16* z, int L);
void trimul_v3(const f16* a, const f16* b, f16* z, int L);
void trimul_v4(const q64* qa, const q64* qb, const float* sa, const float* sb, f16* z, int L);
}
