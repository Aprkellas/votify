# Votify

Download any Spotify song, playlist, or album as an MP3. No account or API keys needed — just paste a link.

---

## First-time setup

**Requires Python 3.8+** — [python.org/downloads](https://www.python.org/downloads/)
Windows: check **"Add Python to PATH"** during install.

Then run the setup script once:

```
# Windows
setup.bat

# Mac / Linux
bash setup.sh
```

This creates a virtual environment and installs all dependencies. FFmpeg is downloaded automatically the first time you run votify (takes ~30 seconds).

---

## Every time you use it

**1. Activate the virtual environment:**

```
# Windows
venv\Scripts\activate

# Mac / Linux
source venv/bin/activate
```

You'll see `(venv)` appear in your terminal. You only need to do this once per terminal session.

**2. Run votify with any Spotify link:**

```
python votify.py https://open.spotify.com/track/...
python votify.py https://open.spotify.com/playlist/...
python votify.py https://open.spotify.com/album/...
```

Files are saved to a `downloads/` folder next to the script.

---

## Options

| Flag | Default | Description |
|------|---------|-------------|
| `-o`, `--output` | `./downloads` | Folder to save files into |
| `--format` | `mp3` | Audio format: `mp3`, `flac`, `ogg`, `opus`, `m4a` |

```
# Save to a different folder
python votify.py <url> --output "C:\Users\You\Music"

# Download as FLAC instead of MP3
python votify.py <url> --format flac
```

---

## Troubleshooting

**"Missing packages" error**
→ You need to activate the virtual environment first: `venv\Scripts\activate`

**A specific song fails**
→ yt-dlp couldn't find a match on YouTube. Rare, but can happen with very new or regional releases.

