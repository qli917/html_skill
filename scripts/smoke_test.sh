#!/usr/bin/env bash
set -euo pipefail

python3 -m py_compile scripts/extract_html_main.py scripts/make_html_compare.py
python3 scripts/extract_html_main.py examples/messy_article.html --format markdown > /tmp/html_skill_body.md

grep -q "Main insight" /tmp/html_skill_body.md
grep -q "Good extraction" /tmp/html_skill_body.md

echo "Smoke test passed."
