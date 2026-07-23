"""
A/B check: base model vs. base+LoRA adapter, using a SHORT system prompt.

If the adapter worked, it holds the compliance style (scoped off-label refusal,
on-label facts, citation) with a one-line prompt — where the base, without the
full compliance prompt, tends to answer loosely.

Run: .venv\\Scripts\\python finetune\\infer_compare.py
"""
from __future__ import annotations
import os
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = os.getenv("FT_BASE", "Qwen/Qwen2.5-3B-Instruct")
ADAPTER = os.path.join(_ROOT, "finetune", "adapter")

SHORT_SYS = "You are a pharma HCP assistant."
Q = "Can I prescribe Vestrila for an indication that is not on its label?"


def gen(model, tok, system, user):
    msgs = [{"role": "system", "content": system}, {"role": "user", "content": user}]
    enc = tok.apply_chat_template(msgs, add_generation_prompt=True,
                                  return_tensors="pt", return_dict=True).to(model.device)
    with torch.no_grad():
        out = model.generate(**enc, max_new_tokens=180, do_sample=False,
                             pad_token_id=tok.eos_token_id)
    return tok.decode(out[0][enc["input_ids"].shape[1]:], skip_special_tokens=True).strip()


def main():
    tok = AutoTokenizer.from_pretrained(BASE)
    model = AutoModelForCausalLM.from_pretrained(BASE, dtype=torch.bfloat16, device_map="cuda")

    print("=" * 70)
    print("QUESTION:", Q)
    print("SYSTEM PROMPT (short):", SHORT_SYS)
    print("=" * 70)
    print("\n--- BASE (no adapter) ---")
    print(gen(model, tok, SHORT_SYS, Q))

    model = PeftModel.from_pretrained(model, ADAPTER)
    print("\n--- BASE + LoRA ADAPTER ---")
    print(gen(model, tok, SHORT_SYS, Q))
    print()


if __name__ == "__main__":
    main()
