#!/usr/bin/env bash
# Download the public International Stroke Trial (IST) IPD used by the
# ONISHI integration demo. Open access (Sandercock et al. 2011, Trials 12:101).
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/data"
mkdir -p "$DIR"
curl -sL -o "$DIR/IST_corrected.csv" \
  "https://datashare.ed.ac.uk/bitstream/handle/10283/124/IST_corrected.csv"
echo "Saved $DIR/IST_corrected.csv"
