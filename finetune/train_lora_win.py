"""
LoRA fine-tuning — native Windows / local GPU path (no unsloth, no bitsandbytes).

bf16 LoRA on a small instruct base so it trains reliably on native Windows with
just torch + transformers + peft + trl. Produces a real adapter in
finetune/adapter/. For the 4-bit unsloth path (Linux/WSL) see train_lora.py.

Goal of the adapter: hold the compliance *style* (fair balance, scoped off-label
refusal, citations) so the base needs a shorter system prompt. RAG still supplies
the facts.

Run (inside the repo venv):
    .venv\\Scripts\\python finetune\\train_lora_win.py
"""
from __future__ import annotations
import os
# NOTE: on native Windows, importing `datasets` (pyarrow) AFTER torch crashes the
# process (native DLL clash). Importing datasets first fixes it — keep this order.
from datasets import load_dataset
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import LoraConfig
from trl import SFTTrainer, SFTConfig

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(_ROOT, "finetune", "dataset.jsonl")
OUT_DIR = os.path.join(_ROOT, "finetune", "adapter")

BASE_MODEL = os.getenv("FT_BASE", "Qwen/Qwen2.5-3B-Instruct")
MAX_SEQ = 1024
LORA_RANK = 16
EPOCHS = float(os.getenv("FT_EPOCHS", "8"))


def main():
    n = sum(1 for _ in open(DATA, encoding="utf-8"))
    print(f"Dataset: {n} examples | base={BASE_MODEL} | rank={LORA_RANK} | epochs={EPOCHS}")
    print("CUDA:", torch.cuda.is_available(), torch.cuda.get_device_name(0) if torch.cuda.is_available() else "")

    tok = AutoTokenizer.from_pretrained(BASE_MODEL)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL, dtype=torch.bfloat16, device_map="cuda",
    )
    model.config.use_cache = False
    model.gradient_checkpointing_enable()

    ds = load_dataset("json", data_files=DATA, split="train")

    def fmt(ex):
        return {"text": tok.apply_chat_template(
            ex["messages"], tokenize=False, add_generation_prompt=False)}
    ds = ds.map(fmt, remove_columns=ds.column_names)

    peft_cfg = LoraConfig(
        r=LORA_RANK, lora_alpha=LORA_RANK * 2, lora_dropout=0.05, bias="none",
        task_type="CAUSAL_LM",
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                        "gate_proj", "up_proj", "down_proj"],
    )

    args = SFTConfig(
        output_dir=os.path.join(_ROOT, "finetune", "_runs"),
        per_device_train_batch_size=1, gradient_accumulation_steps=8,
        num_train_epochs=EPOCHS, learning_rate=2e-4, warmup_ratio=0.05,
        logging_steps=1, save_strategy="no", bf16=True,
        max_length=MAX_SEQ, report_to=[], optim="adamw_torch",
        gradient_checkpointing=True,
        gradient_checkpointing_kwargs={"use_reentrant": False},
    )

    trainer = SFTTrainer(model=model, args=args, train_dataset=ds,
                         peft_config=peft_cfg, processing_class=tok)
    trainer.train()
    trainer.save_model(OUT_DIR)
    tok.save_pretrained(OUT_DIR)
    print("Saved LoRA adapter ->", OUT_DIR)


if __name__ == "__main__":
    if not os.path.exists(DATA):
        raise SystemExit("Run finetune/make_dataset.py first.")
    main()
