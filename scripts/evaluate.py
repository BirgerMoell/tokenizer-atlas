"""Evaluate pinned Hugging Face tokenizers on a shared JSONL corpus."""

import argparse
import hashlib
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path

from transformers import AutoTokenizer


def p95(values):
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, math.ceil(0.95 * len(ordered)) - 1)]


def summarize(rows):
    n = len(rows)
    total_bytes = sum(r["bytes"] for r in rows)
    total_tokens = sum(r["tokens"] for r in rows)
    return {
        "samples": n,
        "utf8_bytes": total_bytes,
        "tokens": total_tokens,
        "tokens_per_100_utf8_bytes": round(100 * total_tokens / total_bytes, 3) if total_bytes else None,
        "bytes_per_token": round(total_bytes / total_tokens, 3) if total_tokens else None,
        "exact_roundtrip_rate": round(sum(r["roundtrip"] for r in rows) / n, 5),
        "p95_tokens_per_sample": p95([r["tokens"] for r in rows]),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--tokenizer", action="append", required=True)
    parser.add_argument("--revision", action="append", default=[], metavar="MODEL=COMMIT_SHA")
    args = parser.parse_args()
    revisions = dict(item.split("=", 1) for item in args.revision)
    raw = args.corpus.read_bytes()
    corpus = [json.loads(line) for line in raw.splitlines() if line.strip()]
    for row in corpus:
        for field in ("language", "script", "domain", "text"):
            if field not in row:
                parser.error(f"Corpus row missing {field}")
    output = {"corpus_sha256": hashlib.sha256(raw).hexdigest(), "samples": len(corpus), "method": "text only; add_special_tokens=False; exact UTF-8 roundtrip", "tokenizers": {}}
    for model in args.tokenizer:
        revision = revisions.get(model, "main")
        tokenizer = AutoTokenizer.from_pretrained(model, revision=revision, use_fast=True, trust_remote_code=False)
        groups = defaultdict(list)
        for row in corpus:
            ids = tokenizer.encode(row["text"], add_special_tokens=False)
            result = {"bytes": len(row["text"].encode("utf-8")), "tokens": len(ids), "roundtrip": tokenizer.decode(ids, skip_special_tokens=False, clean_up_tokenization_spaces=False) == row["text"]}
            groups[(row["language"], row["script"], row["domain"])].append(result)
        output["tokenizers"][model] = {
            "revision": revision,
            "vocab_size": len(tokenizer),
            "groups": [{"language": key[0], "script": key[1], "domain": key[2], **summarize(rows)} for key, rows in sorted(groups.items())],
        }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()
