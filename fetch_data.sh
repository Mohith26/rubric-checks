#!/bin/sh
# Downloads the public rubric benchmarks this repo scans into ./data.
set -e
mkdir -p data
curl -sL -o data/healthbench_oss_eval.jsonl https://openaipublic.blob.core.windows.net/simple-evals/healthbench/2025-05-07-06-14-12_oss_eval.jsonl
curl -sL -o data/profbench_test.jsonl https://huggingface.co/datasets/nvidia/ProfBench/resolve/main/test.jsonl
curl -sL -o data/prbench_finance.parquet https://huggingface.co/datasets/ScaleAI/PRBench/resolve/main/data/finance-00000-of-00001.parquet
curl -sL -o data/prbench_legal.parquet https://huggingface.co/datasets/ScaleAI/PRBench/resolve/main/data/legal-00000-of-00001.parquet
