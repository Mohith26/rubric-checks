# rubric-checks

Two cheap, deterministic checks for rubric-graded benchmarks, run over four public ones.

I read Snorkel's post [Checking the Rubrics: RIFT Results on Five Public Benchmarks](https://snorkel.ai/blog/checking-the-rubrics-rift-results-on-five-public-benchmarks/). One of its examples of "ungrounded verification" is a criterion whose worked example says `5.0% - 3.0% - 3.0% = 1.8%`. That made me wonder how often worked arithmetic inside rubric criteria is simply wrong, and whether a dumb parser could find it without an LLM. RIFT does far more than this (expert-panel signals, coverage, weighting); this repo only covers two narrow, mechanical failure types.

## What it checks

1. **Arithmetic in a criterion.** Flat expressions with a stated result, like `a - b - c = d` or `x * 25% = $y`. Scale suffixes (`k`, `m`, `M`, `bn`, `million`) are applied and a percent can be read as a number or a fraction. Anything ambiguous (parentheses, the tail of a longer expression, scientific notation, unspaced `2x3`) is skipped rather than guessed. A result passes if it is within half a unit of its last shown digit or 1% (2% for `≈`).
2. **Duplicate criteria in one rubric.** Exact duplicates after lowercasing and stripping punctuation. The script also lists near-duplicates (token Jaccard >= 0.9), but see the note below.

## Results

| Benchmark | Rubrics | Criteria | Worked calculations parsed | Wrong | Exact duplicate pairs |
|---|---|---|---|---|---|
| HealthBench (OSS eval) | 5,000 | 57,237 | 1 | 0 | 13 |
| ProfBench | 40 | 1,162 | 2 | 0 | 3 |
| PRBench finance | 600 | 9,865 | 50 | 3 | 1 |
| PRBench legal | 500 | 8,827 | 0 | 0 | 0 |

- **PRBench finance: 3 of the 50 worked calculations I could parse are wrong.** One is the `5.0% - 3.0% - 3.0% = 1.8%` example from the RIFT post (it is -1.0%). The other two are an order-of-magnitude slip (a product that comes to 0.25% written as 2.5%) and a multiplication that comes to 11.125 written as 11.25. I checked all three by hand.
- **HealthBench: 13 rubrics contain the exact same criterion twice.** In 2 of them the copies have opposite signs (for example +10 and -10 points), so the behavior is rewarded and penalized at once and the criterion cancels out.
- Worked arithmetic is rare outside finance, so the arithmetic check has almost nothing to say about the other benchmarks.

`results/` has every flag as a task ID, criterion index and the numbers involved. I left out criterion text on purpose so this repo doesn't republish benchmark content (PRBench carries a canary string).

**Limitations.** The parser is conservative, so it misses calculations written in words, with parentheses, or in LaTeX, and 50 parsed calculations is a small sample. Near-duplicates by token overlap are mostly templated parallel criteria ("identifies the first of four solutions" vs "the second"), not real redundancy, which is a good argument for the semantic signals RIFT uses instead.

## Run it

```sh
./fetch_data.sh
python -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python -m pytest -q
.venv/bin/python scan.py data results
```

The scan takes about 3 seconds.
