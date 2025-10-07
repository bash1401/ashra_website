GPA Calculator: India Grading Systems Crawler

This crawler discovers Indian universities and attempts to extract grading systems in the existing `gpacalculator/grading-systems.json` schema.

Usage:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r scripts/requirements.txt
python scripts/crawl_india_grading.py
```

Notes:
- Targets Wikipedia list to discover university pages, then follows likely links (Academic Regulations, Examination, Grading, etc.).
- Heuristics parse tables with Grade/Points/Percentage columns and infer `scale`.
- Output is merged back into `gpacalculator/grading-systems.json` without adding source URLs.
- Run multiple times to incrementally enrich the dataset.

