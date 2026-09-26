# 附錄 B　自我檢測參考答案

> 先自己想過再看答案。答不出來的題目，回到括號裡標示的章節重讀。

---

## 速覽　LightNobel 與本專題

1. ① **token-wise 自適應量化**：每個 token 一個 scale，activation 依位置分 A、B、C 三組給不同精度（INT8／INT4）；② **outlier 另外存**：執行時用 top-k 挑出、以 INT16 存放，資料格式對硬體友善；③ **專用硬體**：RMPU（4-bit 小塊、多精度）、VVPU（執行時量化、top-k）、Token Aligner 有效率地處理不同格式的 token。（速覽第 2、3 節）
2. 他們觀察到同一個 token 的 channel 之間差異小、token 之間差異大，outlier 也集中在特定 token；以 token 為單位，既能讓每個 token 用適合自己的 scale，又不需要像 per-element 那樣存大量 scale。（速覽第 2 節、1.6 節）
3. **繼承**：問題定義、以 ESMFold 為對象、token-wise 量化、管線化與執行時量化（中間值不落地）的原則、以峰值記憶體與序列長度為指標、模擬器＋交叉驗證的評估方法。**新增**：FPGA 上的實作、v0～v5 逐步 ablation、真實資料驗證量化假設、完整 Triangle Multiplication 的融合設計（含重算 g）、分析模型與設計空間探索。（速覽第 6 節）
4. 平台（ASIC 模擬 vs FPGA）和範圍（整個模型 vs 一個運算）都不同，直接比較不公平；而且融合與執行時量化 LightNobel 都已經做了。較好的說法：「以 LightNobel 的原則為基礎，在現成硬體上實作其中一個運算，並量化每一招各自的貢獻。」（速覽第 6 節）
5. a、b 是 linear 之後的值，依定義屬於 **C 組**（平均 outlier 少於 1 個），論文對 C 組用 INT4、不處理 outlier。所以我們的 INT8 是保守的選擇，INT4（v5）是下一步，但要先用真實資料確認。（速覽第 2、3 節、6.7）

## 第 1 章　為何而做

1. **512 MB → 2 GB（4 倍）。** 大小是 `L² × 128 × 4 bytes`，L 變 2 倍，L² 變 4 倍。（1.4）
2. 權重大小**固定**（ESMFold 的 FP16 權重約 7.90 GB），和 L 無關；activation 隨 **L²**（pair representation）甚至 **L³**（Triangle Attention 的中間值）成長。L 一大，activation 就遠超過權重：L = 2,034 時已經是權重的 24 倍（144 GB）。（1.4）
3. **0.25 FLOP/byte**：每做 2 次運算要讀 8 bytes。以 GPU 約 10 FLOP/byte 的平衡點來看，運算單元大約 97% 的時間都在等資料。（1.5）
4. **`z = a × bᵀ`**：a 的第 i 列和 b 的第 j 列做內積，就是 z 的 (i, j)。（1.3）
5. per-tensor 整份資料共用一個 scale；per-token 每個 token 各自一個 scale。有 outlier 時，per-tensor 的 scale 被 outlier 撐大，一般的數值只能用到很少幾個整數，誤差變大。模擬結果：per-token 約 1%，per-tensor 約 11%。（1.6、2.8）
6. **Triangle Attention**（1,410 aa 時佔 75.9%），因為它的 score matrix 是 L³。先做 Triangle Multiplication 是因為它結構單純（矩陣乘法、沒有 softmax）、容易驗證，而且 tiling、量化、分析模型等方法都能直接沿用到 Triangle Attention；後者列為未來工作。（1.3、1.7）

## 第 2 章　為何可做

1. 沒有重疊：`T ≈ T_compute + T_memory`；完全重疊：`T ≈ max(T_compute, T_memory)`。Double buffering 把「相加」變成「取最大值」。（2.1、2.6）
2. v0 讀取量 `2·L³·C`；tiling 後 `L³·C·(1/16 + 1/16) = L³·C / 8`，是 v0 的 **1/16**。算術強度 `16·16 ÷ (2·32) =` **4 FLOP/byte**。（2.4）
3. 每輪最多從 671 降到約 530 cycles，**約快 1.27 倍**。因為載入只佔 21%，就算完全藏起來也只能省下這 21%（Amdahl's Law）。（2.6、2.10）
4. 頻寬是「每秒能搬多少」，延遲是「從請求到拿到第一筆要等多久」。寬位元提高**頻寬**（每 cycle 搬 16 個 float）；burst 減少**延遲**的影響（一次請求連續拿很多筆，延遲只付一次）。（2.5）
5. **√2 ≈ 1.41 倍**。記憶體和 L² 成正比，所以 L 和記憶體的平方根成正比。（2.8、6.10）

## 第 3 章　工具原理

1. LUT 本質上是一塊 64 格的小記憶體，6 個輸入當作地址、存在裡面的 0/1 就是輸出，所以寫入不同的內容就能變成任何 6 輸入的邏輯函數。（3.1）
2. II 是連續兩次迭代開始的間隔。v0 的 `acc += a*b` 下一次要等上一次的浮點加法做完（loop-carried dependency），所以 II 至少等於加法的延遲。（3.3）
3. 一塊 BRAM 只有 2 個讀寫埠，一個 cycle 最多讀寫 2 次；v2 每個 cycle 要同時讀寫 16 個值，必須把陣列切成 16 塊，讓每塊各自存取。（3.3）
4. 代表**演算法（功能）是對的**；不代表時序正確、也不代表 pragma 宣告（例如 `DEPENDENCE`）沒有錯。要靠 cosim 或 hw_emu 驗證。（3.4）
5. `.xo`：kernel 編譯後的結果（RTL ＋ 參數描述）；`.xclbin`：可以燒進 FPGA 的檔案（bitstream ＋ metadata）；platform：卡上預先做好的基礎設施（PCIe、DMA、HBM 控制器），kernel 要接在它上面。（3.6）

## 第 4 章　整體流程

1. 同一個 token 的 128 個 channel 在記憶體中是連續的，一次 burst 就能讀完，而且剛好是 8 個 512-bit word。這也和 PyTorch 的排列一致，真實資料不用轉換。（4.3）
2. `rel_l2 = ‖z − z_ref‖ ÷ ‖z_ref‖`。v4 使用量化，本來就會有誤差，所以只檢查誤差在合理範圍內（功能正確），而不是要求和浮點結果一樣。（4.5）
3. 專案名稱含有 `/`（`hls_prj/trimul_v2`，在目前資料夾下兩層），但 2025.2 改寫來源路徑時假設專案只在下一層，算出錯的 `../kernels/...`。修法是先 `cd hls_prj`，再建立名稱不含 `/` 的專案。（4.10）
4. 載入 a、b **141**（兩個 port 並行，只算一次）＋ 計算 **526**（512 ＋ pipeline 深度 14）＋ 額外 **4** = **671**。（4.11）
5. `bo.sync(XCL_BO_SYNC_BO_TO_DEVICE)`：透過 PCIe DMA 把資料從主機記憶體複製到 HBM。（4.6、3.7）

## 第 5 章　指令手冊

1. `|` 把 `lspci` 的輸出交給 `grep`，只留下含 xilinx 的行；`-i` 表示不分大小寫。（5.1）
2. `make -n hls KERNEL=trimul_v3`。（5.6）
3. 在 `tmux` 裡執行；按 `Ctrl + B` 再按 `D` 可以暫時離開，重新登入後用 `tmux attach` 回來。（5.5）
4. `make hls KERNEL=trimul_v4 DEFS="-DTILE_I=16 -DTILE_J=16" TAG=trimul_v4_t16`，或 `make hls-sweep SWEEP_KERNEL=trimul_v4 TILES="16"`。（5.6）
5. 把要保留的結果（例如 `hls_summary.csv`、報告）複製到別的地方，因為 `make clean` 會刪除 `hls_prj/`、log 和 csv。（5.6）

## 第 6 章　新策略

1. LayerNorm、linear、sigmoid、gating、量化都是「**每個 token 只用自己的 128 個數**」的運算，一個 token 可以在晶片內一路處理完；只有 einsum 需要跨 token 的資料，才必須把 a、b 寫出去。（6.4）
2. 比例是 `128 ÷ L`，L = 512 時約 **25%**。（6.5）
3. 省下「把 FP32 的 a、b 寫出去、再讀回來量化」的兩趟搬運：a 的 128 個數剛算完還在暫存器裡，就順便算 scale、轉成 INT8。這就是 LightNobel VVPU 的執行時量化。（6.7）
4. 同一份資料校正又驗證，當然會很準，無法證明模型能**預測**沒看過的情況。應該用 v2 8×8 校正，去預測 16×16、32×32，以及 v3、v4 的報告，看誤差是否在 10% 以內。（6.8）
5. 找不到另一個設計在**所有指標都一樣好、而且至少一項更好**。（6.9）
6. `√(3,584 ÷ 1,288) ≈ √2.78 ≈` **1.67 倍**（約 2,190 → 3,650）。（6.10）
7. 論文的比較基準（ESMFold）是 FP16。用 FP32 當基準，原始資料大了一倍，量化「看起來」省更多，會高估效果：同樣的融合 ＋ INT8，FP32 基準是 1.67 倍，FP16 基準只有 1.52 倍。（6.10、1.4）
8. INT4 的前提是「a、b 屬於論文的 C 組（outlier 很少）」，這個假設要用真實資料確認，否則 v5 可能白做。要看 `paper_group_C_check`（平均絕對值、每個 token 的 3σ outlier 數，和論文的 3.85、0.64 比）與 `rel_l2_grid`（INT8／INT4 × token／channel／tensor 的誤差）。（6.7）

## 第 7 章　研究方法

1. **問題是什麼、他們觀察到什麼、解法是什麼、怎麼證明有效。**（7.2）
2. 這樣 v4 和 v2 之間**只差「量化」一件事**，才能把效果歸因給量化；如果從 v3 改，差異就混進了 double buffering。（7.5）
3. 預測逼你先想清楚「為什麼會有效」；量測後比對預測，吻合代表理解正確，不吻合就是新的發現（例如 v3 應該快約 1.27 倍）。（7.5、2.6）
4. 代表**假設錯了**（例如路徑 bug 改成絕對路徑後仍失敗），要回頭找新的線索，例如比較日誌中「加入時的路徑」和「合成時的路徑」。（7.9）
5. ① **瓶頸的數據**與量測條件：我們以為 Triangle Multiplication 最花時間，其實長序列時是 Triangle Attention（Fig. 3）。② **比較基準**：我們用 FP32，論文是 FP16（Table 1）。③ **論文已經做了什麼**：我們以為融合是新角度，其實 RMPU → VVPU 管線已經做到（Sec. 5）。（7.11）
