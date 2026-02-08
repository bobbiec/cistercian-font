#!/bin/bash
# Build the Cistercian font from scratch.
# Prerequisites: Node.js ≥14, Python 3, FontForge (python3-fontforge), fonttools + brotli

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

check() {
  if ! command -v "$1" &>/dev/null; then
    echo -e "${RED}✗ $1 not found${NC} – $2"
    exit 1
  fi
  echo -e "${GREEN}✓${NC} $1"
}

echo "Checking dependencies…"
check node       "install from https://nodejs.org/"
check python3    "install Python 3"
python3 -c "import fontforge" 2>/dev/null \
  && echo -e "${GREEN}✓${NC} fontforge (Python module)" \
  || { echo -e "${RED}✗ fontforge Python module not found${NC} – apt install python3-fontforge / brew install fontforge"; exit 1; }
python3 -c "from fontTools.ttLib import TTFont" 2>/dev/null \
  && echo -e "${GREEN}✓${NC} fonttools" \
  || { echo -e "${RED}✗ fonttools not found${NC} – pip install fonttools brotli"; exit 1; }

echo ""
echo "Step 1/2: Generating SVG glyphs…"
node src/generate-glyphs.js

echo ""
echo "Step 2/2: Building font files…"
python3 src/build-font.py

echo ""
echo -e "${GREEN}Done!${NC}  Font files are in ./fonts/"
echo "Try the live demo at https://bobbiec.github.io/cistercian-font.html"
