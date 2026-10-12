"""Count efficiently encoded FLORES language/script varieties per tokenizer.

The metric is an operational token-cost threshold, not model language support.
Use the same 200 aligned devtest sentences per language. A language passes only
when all its available script variants are within the threshold.
"""

import argparse
import hashlib
import json
import re
from pathlib import Path

import pyarrow.parquet as pq
from huggingface_hub import snapshot_download
from transformers import AutoTokenizer

LANGUAGE_COLUMN = re.compile(r"^[a-z]{3}_[A-Za-z]{4}$")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parquet", required=True, type=Path)
    parser.add_argument("--models", required=True, type=Path, help="JSON list of {name, repo, revision} objects")
    parser.add_argument("--targets", required=True, type=Path, help="JSON map of priority languages to FLORES variants")
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--sentences", type=int, default=200)
    parser.add_argument("--offline", action="store_true", help="Use tokenizer files already present in the Hugging Face cache")
    args = parser.parse_args()

    table = pq.read_table(args.parquet)
    columns = sorted(c for c in table.column_names if LANGUAGE_COLUMN.fullmatch(c))
    if "eng_Latn" not in columns:
        parser.error("FLORES parquet must contain eng_Latn")
    corpus = {}
    for code in columns:
        values = table[code].slice(0, args.sentences).to_pylist()
        if len(values) != args.sentences or any(not isinstance(v, str) or not v for v in values):
            parser.error(f"Incomplete aligned sample for {code}")
        corpus[code] = values

    models = json.loads(args.models.read_text())
    targets = json.loads(args.targets.read_text())
    for name, variants in targets.items():
        if not variants or any(code not in columns for code in variants):
            parser.error(f"Missing FLORES variant for priority language {name}: {variants}")
    output = {
        "method": "Mean token count per aligned sentence divided by English; no special tokens. A distinct language passes only if all its FLORES script variants pass.",
        "corpus": "yash9439/flores200 devtest mirror of FLORES-200",
        "corpus_url": "https://huggingface.co/datasets/yash9439/flores200",
        "corpus_sha256": hashlib.sha256(args.parquet.read_bytes()).hexdigest(),
        "sentences_per_variant": args.sentences,
        "language_variants": len(columns),
        "distinct_languages": len(set(c.split("_")[0] for c in columns)),
        "priority_languages": len(targets),
        "thresholds": [2.0, 3.0],
        "tokenizers": [],
    }

    for model in models:
        print(f"Evaluating {model['name']}", flush=True)
        snapshot = snapshot_download(
            model["repo"], revision=model["revision"],
            allow_patterns=["*.json", "*.model", "*.txt", "*.tiktoken"],
            local_files_only=args.offline,
        )
        tok = AutoTokenizer.from_pretrained(snapshot, use_fast=True, trust_remote_code=False, local_files_only=True)
        if not tok.is_fast:
            parser.error(f"Fast tokenizer required for {model['name']}")
        counts = {}
        for code, sentences in corpus.items():
            encoded = tok(sentences, add_special_tokens=False, padding=False, truncation=False)
            counts[code] = sum(len(ids) for ids in encoded["input_ids"])
        english = counts["eng_Latn"]
        ratios = {code: round(count / english, 4) for code, count in counts.items()}
        language_ratios = {}
        for code, ratio in ratios.items():
            language = code.split("_")[0]
            language_ratios[language] = max(ratio, language_ratios.get(language, 0))
        output["tokenizers"].append({
            "name": model["name"], "repo": model["repo"], "revision": model["revision"],
            "vocab_size": len(tok), "english_tokens": english,
            "within_2x_languages": sum(x <= 2 for x in language_ratios.values()),
            "within_3x_languages": sum(x <= 3 for x in language_ratios.values()),
            "within_2x_variants": sum(x <= 2 for x in ratios.values()),
            "within_3x_variants": sum(x <= 3 for x in ratios.values()),
            "within_2x_priority": sum(max(ratios[code] for code in variants) <= 2 for variants in targets.values()),
            "within_3x_priority": sum(max(ratios[code] for code in variants) <= 3 for variants in targets.values()),
            "mean_ratio": round(sum(ratios.values()) / len(ratios), 3),
            "ratios": ratios,
        })
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n")
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
