# Tokenizer Atlas

An evidence-led comparison of multilingual tokenizers for OpenEuroLLM, with a static GitHub Pages dashboard and a reproducible evaluation runner.

## View locally

```bash
cd site
python3 -m http.server 8000
```

Open <http://localhost:8000>. The dashboard reads `site/data.json`; the five-domain and 36-language fertility metrics are labeled as **source-reported**. The language-coverage table is independently measured with pinned tokenizers and a shared FLORES-200 sample.

## Run a common evaluation

Install the listed dependencies, then create a JSONL corpus with `language`, `script`, `domain`, and `text` fields. Use comparable held-out samples for every tokenizer.

```bash
python3 -m pip install -r requirements.txt
python3 scripts/evaluate.py --corpus corpus.jsonl --output results.json \
  --tokenizer openeurollm/tokenizer-128k-v2 \
  --tokenizer openeurollm/tokenizer-256k-v2 \
  --tokenizer swiss-ai/Apertus-8B-2509
```

For reproducible results, pass `--revision MODEL=COMMIT_SHA` for each tokenizer. The runner reports exact round-trip rate, tokens per UTF-8 byte, bytes per token, token counts and p95 length by language/script/domain. It uses `add_special_tokens=False` to compare text encoding only. Its output is deliberately separate from `site/data.json` until reviewed.

## Compare language coverage

The dashboard shows an independently measured count for each accessible original tokenizer artifact, including five NVIDIA Nemotron variants. Use its NVIDIA filter to compare those rows. See the [benchmark method and results](benchmark/README.md) to reproduce it. Its ≤2× and ≤3× English-relative counts measure token budgets over aligned translations; they do not measure model language competence.

## Interpretation

* **Encodable**: the tokenizer can represent the text, often through byte fallback. This is not evidence that a model understands the language.
* **Efficient**: a held-out sample uses relatively few tokens. Compare tokenizers on identical text and report each language and script; cross-language whitespace-word counts alone are imperfect.
* **Supported by a model**: requires training data and downstream evaluation. A tokenizer cannot establish that on its own.

The source-reported OpenEuroLLM table covers 36 catalogue languages and five domains. The Swiss AI v2 figures use a different 60-language corpus and should not be ranked directly against it. Source links and caveats are in the dashboard.

## GitHub Pages

The included workflow publishes `site/` on pushes to `main`. In repository Settings → Pages, select **GitHub Actions** as the source once.

## Sources

* [Apertus v1 technical report](https://arxiv.org/html/2509.14233)
* [Swiss AI tokenizer development](https://github.com/swiss-ai/apertus-tokenizer-development)
* [OpenEuroLLM 256k v2 model card](https://huggingface.co/openeurollm/tokenizer-256k-v2)
* [OpenEuroLLM 128k v2 model card](https://huggingface.co/openeurollm/tokenizer-128k-v2)
* [OpenEuroLLM language catalogue](https://github.com/OpenEuroLLM/training-data-catalogue/blob/main/languages)

## License

MIT for this repository's code and site. External model cards and tokenizers retain their own licenses.
