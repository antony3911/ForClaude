# 只跑 HLS（不需要板子，幾分鐘內可完成），用來拿 latency / resource 報告
# 用法（在 fpga/trimul 目錄下）：
#   KERNEL=trimul_v2 vitis_hls -f hls/run_hls.tcl
#   （Vitis 2024.2 以後：KERNEL=trimul_v2 vitis-run --mode hls --tcl hls/run_hls.tcl）
# 環境變數：
#   KERNEL  要合成的 kernel（trimul_v0 ~ trimul_v4）
#   COSIM   設為 1 會多跑 C/RTL co-simulation（較慢）
#   DEFS    額外的編譯定義，例如 "-DTILE_I=16 -DTILE_J=16"
set kernel $::env(KERNEL)
set defs ""
if {[info exists ::env(DEFS)]} { set defs $::env(DEFS) }

open_project -reset hls_prj/$kernel
set_top $kernel
add_files kernels/$kernel.cpp -cflags "-Ikernels $defs"
# testbench 會呼叫所有版本，所以其他 kernel 也要加入（當成一般 C++）
foreach f [glob kernels/trimul_v*.cpp] {
    if {[file tail $f] ne "$kernel.cpp"} { add_files -tb $f -cflags "-Ikernels $defs -Wno-unknown-pragmas" }
}
add_files -tb tb/tb.cpp -cflags "-Ikernels $defs -Wno-unknown-pragmas"

open_solution -reset sol -flow_target vitis
set_part xcu55c-fsvh2892-2L-e
create_clock -period 3.33 -name default

csim_design -argv "16"
csynth_design
if {[info exists ::env(COSIM)] && $::env(COSIM) == 1} {
    cosim_design -argv "16"
}
exit
