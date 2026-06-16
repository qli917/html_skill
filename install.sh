#!/usr/bin/env bash
set -euo pipefail

MODE="${1:-minimal}"

python3 -m pip install --upgrade beautifulsoup4

case "$MODE" in
  minimal|--minimal|"")
    echo "Installed minimal dependencies: beautifulsoup4"
    ;;
  browser|--browser|--with-browser)
    python3 -m pip install --upgrade playwright
    python3 -m playwright install chromium
    echo "Installed browser rendering dependencies: beautifulsoup4 + playwright + chromium"
    ;;
  *)
    echo "Unknown install mode: $MODE" >&2
    echo "Usage:" >&2
    echo "  bash install.sh" >&2
    echo "  bash install.sh --with-browser" >&2
    exit 2
    ;;
esac

cat <<'MSG'

Try it:
  python3 scripts/extract_html_main.py examples/messy_article.html --format markdown
MSG
