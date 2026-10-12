# FLORES-200 tokenizer coverage benchmark

This is a **token-efficiency screen**, not a count of languages understood by a model. It scores original tokenizer artifacts on the same aligned text and publishes both the per-script ratios and summary counts.

## Corpus and method

* Corpus: the [`yash9439/flores200` devtest Parquet mirror](https://huggingface.co/datasets/yash9439/flores200) of [FLORES-200](https://github.com/facebookresearch/flores/tree/main/flores200). The original FLORES repository is the primary source; this benchmark uses a mirror because the original Hugging Face distribution required access in this environment.
* File SHA-256: `37adade6f0174c18b1169721196ae22d6294157c46d9d77f4b2152afa0d5d2b5`.
* Sample: the first 200 aligned `devtest` sentences for each of 204 language/script columns, representing 196 distinct ISO 639-3 language prefixes.
* Metric: sum token IDs from the 200 sentences per variety, with `add_special_tokens=False`, then divide by the sum for `eng_Latn`. We report a language as passing a threshold only if **all** of its available script varieties pass. The page switches between ≤2× and ≤3× English. The 36 priority languages are mapped in [`targets.json`](targets.json); some have two FLORES varieties.
* Mean cost: the arithmetic mean of the 204 English-relative variety ratios. Each variety contributes equally; lower means fewer tokens relative to the tokenizer's own English count. This is a summary of the same FLORES sample, not a cross-domain speed benchmark.
* Artifacts: original tokenizer repos and pinned commits are in [`models.json`](models.json). The runner requires a fast tokenizer, and runs without trusting remote code.

English-normalized token count is a practical context-budget measure, but translation length varies by language. This metric does not isolate tokenizer quality from the length of a translation. It also says nothing about a model's language capabilities. FLORES has only a small, single-domain sample; future work should include news, conversational text, code switching, and low-resource scripts.

## Reproduce

Install the root [`requirements.txt`](../requirements.txt) and download the `devtest` Parquet file from the linked mirror. Verify its SHA-256 above. Then run:

```bash
python3 scripts/coverage_flores.py \
  --parquet /path/to/devtest.parquet \
  --models benchmark/models.json \
  --targets benchmark/targets.json \
  --output benchmark/coverage-flores200.json
```

Use `--offline` only when the tokenizer snapshots at the pinned revisions are already cached. The runner downloads tokenizer/config files, not model weights. [`coverage-flores200.json`](coverage-flores200.json) contains every variety's ratio; [`../site/coverage.json`](../site/coverage.json) holds the count summary used by the dashboard. The FLORES sentence text is not redistributed in this repository.

Llama 3.1 8B and EuroLLM 9B are in the separately sourced five-domain comparison, but their original tokenizer artifacts required access during this run. They are shown as unavailable in the independent coverage table instead of using unverified substitutes.

## NVIDIA variants

The added NVIDIA rows use official, pinned model repositories: Nemotron 3 Nano 4B and 30B, Nemotron Nano 9B v2, Llama Nemotron Super 49B v1.5, and Nemotron Mini 4B. They are scored only on the FLORES coverage benchmark; the separately published five-domain chart has no NVIDIA rows. On this corpus, the first three NVIDIA variants produce the same token counts across all 204 varieties as Mistral NeMo and Apertus. Nemotron 3 Nano 4B and 30B also have identical serialized subword model components in their `tokenizer.json` artifacts. These duplicated coverage results should not be read as independent evidence about model quality or inference speed. Quantized variants and the Nemotron 3 Super/Ultra checkpoints were omitted because their published tokenizer artifacts repeat those already represented here.
