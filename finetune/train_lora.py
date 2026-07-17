"""
LoRA / QLoRA fine-tuning of the domain compliance adapter, using unsloth.

Trains a small adapter on finetune/dataset.jsonl so the base model holds the
compliance style with a shorter system prompt. Sized to fit a 24 GB NVIDIA GPU:
4-bit base + LoRA rank 16.

Toolchain note: unsloth's kernels (triton/xformers) target Linux/CUDA. On this
Windows box, run under WSL2 or a Linux host with the GPU passed through. The
script itself is host-agnostic. See finetune/README.md.

Run: python finetune/train_lora.py
"""
from __future__ import annotations
import os
import json

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(_ROOT, "finetune", "dataset.jsonl")
OUT_DIR = os.path.join(_ROOT, "finetune", "adapter")

BASE_MODEL = os.getenv("FT_BASE", "unsloth/Qwen2.5-7B-Instruct-bnb-4bit")
MAX_SEQ = 2048
LORA_RANK = 16


def main():
    from unsloth import FastLanguageModel
    from datasets import load_dataset
    from trl import SFTTrainer
    from transformers import TrainingArguments

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=BASE_MODEL, max_seq_length=MAX_SEQ, load_in_4bit=True,
    )
    model = FastLanguageModel.get_peft_model(
        model, r=LORA_RANK, lora_alpha=LORA_RANK, lora_dropout=0.0, bias="none",
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                        "gate_proj", "up_proj", "down_proj"],
        use_gradient_checkpointing="unsloth", random_state=42,
    )

    ds = load_dataset("json", data_files=DATA, split="train")

    def fmt(ex):
        return {"text": tokenizer.apply_chat_template(
            ex["messages"], tokenize=False, add_generation_prompt=False)}
    ds = ds.map(fmt)

    trainer = SFTTrainer(
        model=model, tokenizer=tokenizer, train_dataset=ds,
        dataset_text_field="text", max_seq_length=MAX_SEQ,
        args=TrainingArguments(
            per_device_train_batch_size=2, gradient_accumulation_steps=4,
            warmup_steps=5, num_train_epochs=3, learning_rate=2e-4,
            logging_steps=1, optim="adamw_8bit", seed=42,
            output_dir=os.path.join(_ROOT, "finetune", "_runs"),
        ),
    )
    trainer.train()
    model.save_pretrained(OUT_DIR)
    tokenizer.save_pretrained(OUT_DIR)
    print("Saved LoRA adapter to", OUT_DIR)


if __name__ == "__main__":
    if not os.path.exists(DATA):
        raise SystemExit("Run finetune/make_dataset.py first.")
    n = sum(1 for _ in open(DATA, encoding="utf-8"))
    print(f"Dataset ready: {n} examples. Base={BASE_MODEL}, rank={LORA_RANK}.")
    main()
