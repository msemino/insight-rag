# Fine-tuning — domain compliance LoRA adapter

## Purpose
Train a small LoRA adapter so the base model holds the compliance *style* (fair
balance, scoped off-label refusal, source citation) with a shorter system
prompt. RAG still supplies the facts; the adapter supplies the behavior.

## Pipeline
1. `python finetune/make_dataset.py` → builds `dataset.jsonl` (chat format) from
   the corpus + knowledge graph. **Runs anywhere, no GPU.** ✅
2. `python finetune/train_lora.py` → 4-bit base + LoRA rank 16, sized for a
   single RTX 3090 (24 GB). Saves the adapter to `finetune/adapter/`.

## Hardware / toolchain
Training uses **unsloth**, whose kernels (Triton, xformers) target **Linux/CUDA**.
On the RTX 3090 host (Windows 11) run training under **WSL2** or a Linux boot with
the GPU passed through:

```bash
# inside WSL2 (Ubuntu) with CUDA:
pip install unsloth trl datasets transformers
python finetune/train_lora.py
```

Native Windows is not supported for the training step (Triton JIT does not build
here). Everything else in InsightRAG — RAG, graph, observability, API — runs
natively on Windows.

## Serving the adapter
After training, merge or load the adapter and expose it through Ollama
(`ollama create` from the GGUF export) or vLLM, then point `INSIGHT_MODEL` at it.
The rest of the stack is backend-agnostic and needs no code change.

## Two paths
- **`train_lora.py`** — 4-bit QLoRA via **unsloth** (Linux/WSL2 toolchain).
- **`train_lora_win.py`** — bf16 LoRA via torch + transformers + peft + trl,
  **runs natively on Windows / RTX 3090** (no Triton, no bitsandbytes). This is the
  one actually executed. See [`AB_RESULT.md`](AB_RESULT.md).

  > Native-Windows gotcha: importing `datasets` (pyarrow) *after* torch crashes the
  > process — import `datasets` first. Handled at the top of `train_lora_win.py`.

## Status — DONE
- Dataset generation: **done** (12 examples).
- Adapter: **trained on the RTX 3090** (bf16 LoRA rank 16, Qwen2.5-3B, ~77 s).
  A/B vs. base with a one-line prompt shows the compliance style held. See
  [`AB_RESULT.md`](AB_RESULT.md).
