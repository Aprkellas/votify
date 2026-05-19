#!/usr/bin/env bash
set -e

echo "============================================================"
echo "  Votify Setup"
echo "============================================================"
echo

# Check Python
if ! command -v python3 &>/dev/null; then
    echo "ERROR: python3 not found. Install Python 3.8+ first."
    exit 1
fi

echo "[1/3] Creating virtual environment..."
python3 -m venv venv

echo "[2/3] Installing dependencies..."
source venv/bin/activate
pip install --upgrade pip --quiet
pip install -r requirements.txt

echo "[3/3] Verifying FFmpeg (auto-downloaded on first run)..."
python3 -c "import static_ffmpeg; static_ffmpeg.add_paths(); print('FFmpeg ready.')"

echo
echo "============================================================"
echo "  Setup complete!"
echo "============================================================"
echo
echo "To use Votify:"
echo "  1. Activate the environment:  source venv/bin/activate"
echo "  2. Run:  python votify.py <spotify_url>"
echo
echo "No credentials needed -- just paste any Spotify link."
echo
