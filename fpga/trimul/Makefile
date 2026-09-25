# ===== 可調參數 =====
# 平台名稱：用 `ls /opt/xilinx/platforms` 或 `xbutil examine` 確認你們 server 上的實際名稱
PLATFORM ?= xilinx_u55c_gen3x16_xdma_3_202210_1
# sw_emu：純軟體模擬（最快）；hw_emu：RTL 模擬（慢）；hw：實際上板（編譯 1~數小時）
TARGET   ?= hw_emu
KERNEL   ?= trimul_v2
# HBM 連接設定，預設 cfg/$(KERNEL).cfg；可換成 cfg/trimul_v2_onebank.cfg 做對照
CFG      ?= cfg/$(KERNEL).cfg
# 額外編譯定義，例如 DEFS="-DTILE_I=16 -DTILE_J=16"（host 也要用相同設定）
DEFS     ?=
# 輸出檔名標籤（做不同實驗時避免互相覆蓋）
TAG      ?= $(KERNEL)
# make run 的參數
RUN_L    ?= 16
RUN_ARGS ?=
# 真實資料目錄（python/dump_trimul_inputs.py 的輸出）；設定後 RUN_L 會被忽略
DATA     ?=

BUILD  := build/$(TARGET)
XO     := $(BUILD)/$(TAG).xo
XCLBIN := $(BUILD)/$(TAG).xclbin
HOST   := host.exe

VPP_FLAGS := -t $(TARGET) --platform $(PLATFORM) -I kernels $(DEFS) --save-temps --temp_dir $(BUILD)/tmp_$(TAG)
CXXFLAGS  := -std=c++17 -O2 -Wall -Wno-unknown-pragmas -Wno-unused-label $(DEFS)

.PHONY: help csim hls hls-all summary xo xclbin host run clean

help:
	@echo "make csim                               # g++ 功能驗證，不需 Vitis"
	@echo "make hls KERNEL=trimul_v2               # 只跑 HLS 合成，看 latency/resource 報告"
	@echo "make hls-all                            # v0~v4 全部合成（約數十分鐘）"
	@echo "make summary                            # 把所有 HLS 報告整理成比較表（存成 hls_summary.csv）"
	@echo "make xclbin KERNEL=trimul_v2 TARGET=hw  # 產生 FPGA bitstream（xclbin）"
	@echo "make host                               # 編譯 host 程式（需要 XRT）"
	@echo "make run KERNEL=trimul_v2 TARGET=hw_emu # 執行（emulation 或上板）"

# ---- 1. C simulation：只用 g++，任何電腦都能跑 ----
csim:
	g++ $(CXXFLAGS) tb/tb.cpp kernels/*.cpp -o csim.exe
	./csim.exe 32 $(DATA)

# ---- 2. HLS 合成：報告在 hls_prj/$(KERNEL)/sol/syn/report/ ----
# Vitis 2024.2 以後沒有 vitis_hls 指令，改用 vitis-run；這裡自動判斷
HLS_CMD := $(if $(shell command -v vitis_hls 2>/dev/null),vitis_hls -f,vitis-run --mode hls --tcl)
hls:
	KERNEL=$(KERNEL) DEFS="$(DEFS)" $(HLS_CMD) hls/run_hls.tcl

# 一次合成全部版本；某一版失敗不會中斷其他版本
KERNELS ?= trimul_v0 trimul_v1 trimul_v2 trimul_v3 trimul_v4
hls-all:
	@for k in $(KERNELS); do \
		echo "===== $$k ====="; \
		$(MAKE) --no-print-directory hls KERNEL=$$k > hls_$$k.log 2>&1 \
			&& echo "  OK" || echo "  FAILED（看 hls_$$k.log 的最後幾行）"; \
	done
	@$(MAKE) --no-print-directory summary

summary:
	python3 scripts/hls_summary.py --csv hls_summary.csv

# ---- 3. Vitis 編譯 + 連結 ----
$(XO): kernels/$(KERNEL).cpp kernels/trimul.h
	mkdir -p $(BUILD)
	v++ -c $(VPP_FLAGS) -k $(KERNEL) -o $@ $<

$(XCLBIN): $(XO) $(CFG)
	v++ -l $(VPP_FLAGS) --config $(CFG) -o $@ $(XO)

xo: $(XO)
xclbin: $(XCLBIN)

# ---- 4. Host 程式（XRT） ----
host: $(HOST)
$(HOST): host/host.cpp host/common.h kernels/trimul.h
	g++ $(CXXFLAGS) -I$(XILINX_XRT)/include host/host.cpp -L$(XILINX_XRT)/lib -lxrt_coreutil -pthread -o $@

# ---- 5. 執行 ----
run: $(XCLBIN) $(HOST)
ifeq ($(TARGET),hw)
	./$(HOST) $(XCLBIN) $(KERNEL) $(RUN_L) $(if $(DATA),3 token 2000 $(DATA),$(RUN_ARGS))
else
	emconfigutil --platform $(PLATFORM) --od .
	XCL_EMULATION_MODE=$(TARGET) ./$(HOST) $(XCLBIN) $(KERNEL) $(RUN_L) $(if $(DATA),1 token 2000 $(DATA),1 $(RUN_ARGS))
endif

clean:
	rm -rf build hls_prj *.exe emconfig.json *.log *.jou .run .Xil _x xrt.run_summary *.csv
