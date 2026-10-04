# 試跑：ESM-2 放 CPU（FP16，與檔案相同），其餘放 GPU（FP32），量時間與 GPU 峰值記憶體
import glob, os, random, sys, time
import torch
from transformers import EsmForProteinFolding

L = int(sys.argv[1]) if len(sys.argv) > 1 else 100
random.seed(0)
seq = "".join(random.choice("ACDEFGHIKLMNPQRSTVWY") for _ in range(L))

ckpt = glob.glob(os.path.expanduser("~/.cache/huggingface/hub/models--facebook--esmfold_v1/snapshots/*/pytorch_model.bin"))[0]
m = EsmForProteinFolding.from_pretrained("facebook/esmfold_v1", torch_dtype=torch.float16, low_cpu_mem_usage=True)
n_esm = sum(p.numel() for p in m.esm.parameters())
n_all = sum(p.numel() for p in m.parameters())
print(f"params: ESM-2 {n_esm/1e9:.2f} B, others {(n_all-n_esm)/1e9:.2f} B")

# 其他部分先搬上 GPU 再轉 FP32，再從原檔填回 FP32 權重（避免 FP16 截斷）
for name, child in m.named_children():
    if name != "esm":
        child.cuda().float()
m.esm_s_combine.data = m.esm_s_combine.data.cuda().float()
sd = torch.load(ckpt, map_location="cpu", mmap=True, weights_only=True)
print("ckpt dtypes: esm", {str(v.dtype) for k, v in sd.items() if k.startswith("esm.")},
      "others", {str(v.dtype) for k, v in sd.items() if not k.startswith("esm.")})
missing, unexpected = m.load_state_dict({k: v for k, v in sd.items() if not k.startswith("esm.")}, strict=False)
print("non-esm missing:", [k for k in missing if not k.startswith("esm.")], "unexpected:", unexpected)
del sd
m.eval()
m.trunk.set_chunk_size(64)

orig = m.compute_language_model_representations
def lm_on_cpu(esmaa):
    t = time.time()
    out = orig(esmaa.cpu()).cuda()
    print(f"ESM-2 on CPU: {time.time()-t:.1f} s")
    return out
m.compute_language_model_representations = lm_on_cpu

print("infer device:", next(m.parameters()).device)
print(f"GPU weights: {torch.cuda.memory_allocated()/1e9:.2f} GB")
torch.cuda.reset_peak_memory_stats()
with torch.no_grad():
    t = time.time()
    out = m.infer(seq)
    torch.cuda.synchronize()
print(f"L={L}: total {time.time()-t:.1f} s, GPU peak {torch.cuda.max_memory_allocated()/1e9:.2f} GB, pLDDT {out['plddt'].mean().item():.3f}")
