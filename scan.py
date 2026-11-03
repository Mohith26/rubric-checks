"""Run the arithmetic and duplicate checks over public rubric benchmarks.

Usage: python scan.py DATA_DIR OUT_DIR
DATA_DIR must contain the files listed in README.md. Output files hold task
IDs, criterion indices and numbers only, not benchmark text.
"""

import json
import sys
from pathlib import Path

import pandas as pd

from rubric_arith import duplicate_pairs, scan_text


def healthbench(path):
    for line in open(path):
        r = json.loads(line)
        yield r["prompt_id"], [c["criterion"] for c in r["rubrics"]]


def profbench(path):
    for line in open(path):
        r = json.loads(line)
        yield r["task_id"], [c["criterion_description"] for c in r["rubrics"]]


def prbench(path):
    for _, r in pd.read_parquet(path).iterrows():
        yield r["task"], [c["title"] for c in r["rubric"]]


SOURCES = {
    "healthbench": ("healthbench_oss_eval.jsonl", healthbench),
    "profbench": ("profbench_test.jsonl", profbench),
    "prbench_finance": ("prbench_finance.parquet", prbench),
    "prbench_legal": ("prbench_legal.parquet", prbench),
}


def main(data_dir, out_dir):
    out = Path(out_dir)
    out.mkdir(exist_ok=True)
    summary = {}
    for name, (fname, reader) in SOURCES.items():
        tasks = criteria = checked = 0
        arith, dupes = [], []
        for task_id, crits in reader(Path(data_dir) / fname):
            tasks += 1
            criteria += len(crits)
            for i, c in enumerate(crits):
                n, found = scan_text(c)
                checked += n
                for f in found:
                    arith.append({"task": task_id, "criterion": i, "stated": f.stated,
                                  "computed": round(f.computed, 6), "approx": f.approx})
            for i, j, s in duplicate_pairs(crits):
                dupes.append({"task": task_id, "a": i, "b": j, "similarity": s,
                              "exact": s == 1.0})
        summary[name] = {
            "tasks": tasks, "criteria": criteria,
            "expressions_checked": checked,
            "arithmetic_flags": len(arith),
            "duplicate_pairs": len(dupes),
            "exact_duplicate_pairs": sum(d["exact"] for d in dupes),
            "tasks_with_duplicates": len({d["task"] for d in dupes}),
        }
        (out / f"{name}_arith.json").write_text(json.dumps(arith, indent=1))
        (out / f"{name}_dupes.json").write_text(json.dumps(dupes, indent=1))
    (out / "summary.json").write_text(json.dumps(summary, indent=1))
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
