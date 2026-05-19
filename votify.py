#!/usr/bin/env python3
"""
Votify - Download Spotify songs, playlists, and albums as MP3
No API credentials needed. Works from any public Spotify link.

Usage:
    python votify.py <spotify_url>
    python votify.py <spotify_url> --output my_music
    python votify.py <spotify_url> --format flac
"""

import sys
import argparse
import json
import re
from pathlib import Path

# --- Dependency check ---------------------------------------------------------
missing = []
try:
    import requests
except ImportError:
    missing.append("requests")

try:
    import yt_dlp
except ImportError:
    missing.append("yt-dlp")

try:
    import static_ffmpeg
except ImportError:
    missing.append("static-ffmpeg")

if missing:
    print(f"Missing packages: {', '.join(missing)}")
    print("Run setup first:")
    print("  Windows:   setup.bat")
    print("  Mac/Linux: bash setup.sh")
    sys.exit(1)

# Add bundled FFmpeg to PATH so yt-dlp can find it for audio conversion
static_ffmpeg.add_paths()

# ------------------------------------------------------------------------------

# Googlebot UA causes Spotify to serve a server-rendered page with og: meta tags.
_HEADERS_BOT = {
    "User-Agent": "Googlebot/2.1 (+http://www.google.com/bot.html)",
}

# Standard browser UA for the embed pages (playlist / album).
_HEADERS_BROWSER = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


def parse_url(url):
    """Return (type, id) from a Spotify link, e.g. ('track', 'abc123')."""
    match = re.search(r"spotify\.com/(track|playlist|album)/([A-Za-z0-9]+)", url)
    if not match:
        raise ValueError(
            f"Unrecognised Spotify URL: {url}\n"
            "Expected a link to a track, playlist, or album."
        )
    return match.group(1), match.group(2)


# --- Track metadata -----------------------------------------------------------

def _og_tag(html, prop):
    m = re.search(rf'<meta[^>]+property="{re.escape(prop)}"[^>]+content="([^"]*)"', html)
    if not m:
        m = re.search(rf'<meta[^>]+content="([^"]*)"[^>]+property="{re.escape(prop)}"', html)
    return m.group(1) if m else ""


def fetch_track(track_id):
    """
    Fetch title + artist for a single track.
    Spotify serves a fully rendered page (with og: tags) to Googlebot.
    og:description format: "Artist · Album · Song · year"
    """
    resp = requests.get(
        f"https://open.spotify.com/track/{track_id}",
        headers=_HEADERS_BOT,
        timeout=15,
    )
    resp.raise_for_status()
    html = resp.text

    title = _og_tag(html, "og:title")
    desc = _og_tag(html, "og:description")
    # Strip occasional "Listen to X on Spotify. " prefix
    if "on Spotify." in desc:
        desc = desc.split("on Spotify.", 1)[-1].strip()
    # First segment before " · " is the artist name(s)
    artists = desc.split(" \u00b7 ")[0].strip() if desc else "Unknown"

    if not title:
        raise RuntimeError(f"Could not read track metadata for ID {track_id!r}.")
    return {"title": title, "artists": artists}


# --- Playlist / album metadata ------------------------------------------------

def _embed_track_list(embed_type, spotify_id):
    """
    Fetch the Spotify embed page and extract tracks from __NEXT_DATA__.
    The JSON path is: props.pageProps.state.data.entity.trackList
    Each item has: title (track name), subtitle (artist names as a string).
    """
    resp = requests.get(
        f"https://open.spotify.com/embed/{embed_type}/{spotify_id}",
        headers=_HEADERS_BROWSER,
        timeout=15,
    )
    resp.raise_for_status()

    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', resp.text, re.DOTALL)
    if not m:
        raise RuntimeError("__NEXT_DATA__ not found in embed page.")

    data = json.loads(m.group(1))
    try:
        track_list = data["props"]["pageProps"]["state"]["data"]["entity"]["trackList"]
    except (KeyError, TypeError) as exc:
        raise RuntimeError(f"Unexpected embed page structure: {exc}") from exc

    if not track_list:
        raise RuntimeError("trackList is empty.")

    return [
        {"title": t["title"], "artists": t.get("subtitle") or "Unknown"}
        for t in track_list
        if isinstance(t, dict) and t.get("title")
    ]


def fetch_playlist_tracks(playlist_id):
    return _embed_track_list("playlist", playlist_id)


def fetch_album_tracks(album_id):
    return _embed_track_list("album", album_id)


# --- Download -----------------------------------------------------------------

def safe_filename(s):
    """Strip characters that are illegal in filenames on Windows/Mac/Linux."""
    return re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", s).strip()


def download_track(title, artists, output_dir, audio_format):
    name = safe_filename(f"{title} - {artists}")
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": str(output_dir / f"{name}.%(ext)s"),
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": audio_format,
                "preferredquality": "192",
            }
        ],
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([f"ytsearch1:{title} {artists}"])


# --- Main ---------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Download Spotify songs, playlists, and albums as MP3",
        prog="votify",
    )
    parser.add_argument("url", help="Spotify link — track, playlist, or album")
    parser.add_argument(
        "-o", "--output",
        default="downloads",
        metavar="DIR",
        help="Folder to save files into (default: ./downloads)",
    )
    parser.add_argument(
        "--format",
        default="mp3",
        choices=["mp3", "flac", "ogg", "opus", "m4a"],
        help="Audio format (default: mp3)",
    )

    args = parser.parse_args()
    output_dir = Path(args.output).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 56)
    print("  Votify")
    print("=" * 56)

    try:
        url_type, url_id = parse_url(args.url)
    except ValueError as e:
        print(e)
        sys.exit(1)

    try:
        if url_type == "track":
            print("Fetching track info...", end=" ", flush=True)
            track = fetch_track(url_id)
            tracks = [track]
            print(f"{track['title']} \u2014 {track['artists']}")
        elif url_type == "playlist":
            print("Fetching playlist...", end=" ", flush=True)
            tracks = fetch_playlist_tracks(url_id)
            print(f"{len(tracks)} tracks")
        elif url_type == "album":
            print("Fetching album...", end=" ", flush=True)
            tracks = fetch_album_tracks(url_id)
            print(f"{len(tracks)} tracks")
    except Exception as e:
        print(f"\nFailed: {e}")
        sys.exit(1)

    print(f"Output: {output_dir}")
    print(f"Format: {args.format}")
    print()

    failed = []
    for i, track in enumerate(tracks, 1):
        label = f"{track['title']} \u2014 {track['artists']}"
        print(f"[{i}/{len(tracks)}] {label}", end=" ... ", flush=True)
        try:
            download_track(track["title"], track["artists"], output_dir, args.format)
            print("done")
        except KeyboardInterrupt:
            print("\nCancelled.")
            sys.exit(0)
        except Exception as e:
            print(f"FAILED ({e})")
            failed.append(track)

    total = len(tracks)
    ok = total - len(failed)
    print()
    print(f"Finished: {ok}/{total} downloaded \u2192 {output_dir}")

    if failed:
        print(f"\nCould not download ({len(failed)}):")
        for t in failed:
            print(f"  \u2022 {t['title']} \u2014 {t['artists']}")


if __name__ == "__main__":
    main()
