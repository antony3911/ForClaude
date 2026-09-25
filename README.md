# ForClaude

以 LightNobel (ISCA 2025) 指出的 PPM 序列長度與記憶體瓶頸為出發點，
在 AMD Alveo U55C 上比較常見的 memory-bound 優化手法。

- [docs/conversation_notes.md](docs/conversation_notes.md)：**先看這份**，專題在做什麼、各檔案用途、下一步
- [docs/getting_started_u55c.md](docs/getting_started_u55c.md)：U55C 環境設定與開發流程（從零開始看這份）
- [fpga/trimul/](fpga/trimul/)：Triangle Multiplication kernel 的各個優化版本、host 程式、實驗說明
- [docs/real_protein_data.md](docs/real_protein_data.md)：用真實（長鏈）蛋白質產生測試資料，需要的資源
- [python/](python/)：從 ESMFold 擷取 Triangle Multiplication 輸入的腳本
