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

## Status
- Dataset generation: **done** (12 examples, extend by adding corpus docs).
- Training script: **ready**; execute on the WSL2/Linux 3090 toolchain.
