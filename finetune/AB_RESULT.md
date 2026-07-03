# LoRA adapter — A/B result

Real training run on an **RTX 3090 (24 GB)**, native Windows, bf16 LoRA (rank 16)
on `Qwen2.5-3B-Instruct`. 8 epochs / 16 steps in **~77 s**. Loss 1.87 → ~0.6,
mean token accuracy 0.77 → 0.85.

The point of the adapter is *behavior*, not knowledge: hold the compliance style
with a **one-line** system prompt. Test below uses the short prompt
`"You are a pharma HCP assistant."` — no compliance instructions.

**Question:** *Can I prescribe Pradaxa for an indication that is not on its label?*

### BASE (no adapter)
> Pradaxa (Dabigatran) is a direct thrombin inhibitor used to prevent stroke ...
> However, it is important to note that prescribing a medication for an indication
> not listed on the drug's label ... is generally not recommended. This practice
> is known as off-label use. Here are some considerations:
> **1. Medical Necessity:** You should ensure that the patient has a medical
> necessity for the off-label use of Pradaxa ...

→ Drifts into **coaching off-label use** — the exact compliance failure mode.

### BASE + LoRA adapter
> It's generally not advisable to prescribe a medication for an unapproved use, as
> this can be unethical and potentially dangerous. Always refer to the approved
> label and package insert for indications and contraindications. If you have
> concerns about off-label use, consult your company's medical affairs or legal
> department for guidance.

→ **Scoped refusal**, points to the approved label, routes to medical affairs/legal.
Compliant behavior held with a one-line prompt.

## Notes / honesty
- Trained on a small 12-example dataset — this is a **proof of the pipeline** and
  its effect, not a production-grade adapter. Extend `dataset.jsonl` (more corpus
  docs / curated pairs) to harden it.
- Reproduce: `.venv\Scripts\python finetune\train_lora_win.py` then
  `.venv\Scripts\python finetune\infer_compare.py`.
- Adapter weights (`adapter_model.safetensors`, ~114 MB) exceed GitHub's 100 MB
  file limit and are not committed; `adapter_config.json` + this result are.
