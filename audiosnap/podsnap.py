#!/usr/bin/env python3
"""podsnap — Download and transcribe audio from podcasts and videos.

Supports: YouTube, Bilibili, 小宇宙, Apple Podcasts, generic RSS, and any yt-dlp supported site.
"""

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path


def detect_source(url: str) -> str:
    """Detect the source type from URL."""
    if "xiaoyuzhoufm.com" in url:
        return "xiaoyuzhou"
    if "youtube.com" in url or "youtu.be" in url:
        return "ytdlp"
    if "bilibili.com" in url or "b23.tv" in url:
        return "ytdlp"
    if "podcasts.apple.com" in url:
        return "apple"
    if url.endswith(".xml") or url.endswith("/rss") or "/feed" in url:
        return "rss"
    if url.endswith((".mp3", ".m4a", ".wav", ".ogg", ".opus", ".flac")):
        return "direct"
    # Default: try yt-dlp
    return "ytdlp"


def download_direct(url: str, output: str) -> str:
    """Download a direct audio URL."""
    print(f"⬇️  Downloading: {url}", file=sys.stderr)
    urllib.request.urlretrieve(url, output)
    return output


def download_ytdlp(url: str, output: str) -> str:
    """Download audio via yt-dlp."""
    print(f"⬇️  Downloading via yt-dlp: {url}", file=sys.stderr)
    cmd = [
        "yt-dlp",
        "-x",  # extract audio
        "--audio-format", "mp3",
        "--audio-quality", "0",
        "-o", output,
        "--no-playlist",
        "--cookies-from-browser", "chrome",
        "--remote-components", "ejs:github",
        url,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ yt-dlp error: {result.stderr}", file=sys.stderr)
        sys.exit(1)
    # yt-dlp may add extension
    for ext in [output, output + ".mp3", output.rsplit(".", 1)[0] + ".mp3"]:
        if os.path.exists(ext):
            return ext
    # Find the file yt-dlp actually created
    base = output.rsplit(".", 1)[0]
    import glob
    matches = glob.glob(f"{base}.*")
    if matches:
        return matches[0]
    print("❌ Could not find downloaded file", file=sys.stderr)
    sys.exit(1)


def download_xiaoyuzhou(url: str, output: str) -> str:
    """Download from 小宇宙 by extracting audio URL from the page or API."""
    print(f"⬇️  Fetching 小宇宙 episode: {url}", file=sys.stderr)

    # Extract episode ID from URL
    # https://www.xiaoyuzhoufm.com/episode/XXXXX
    match = re.search(r"/episode/([a-f0-9]+)", url)
    if not match:
        # Try podcast RSS
        match = re.search(r"/podcast/([a-f0-9]+)", url)
        if match:
            return download_xiaoyuzhou_rss(match.group(1), output)
        print("❌ Can't parse 小宇宙 URL", file=sys.stderr)
        sys.exit(1)

    episode_id = match.group(1)

    # Try the API endpoint
    api_url = f"https://www.xiaoyuzhoufm.com/episode/{episode_id}"
    req = urllib.request.Request(api_url, headers={
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    })
    try:
        resp = urllib.request.urlopen(req)
        html = resp.read().decode("utf-8")
    except Exception as e:
        print(f"❌ Failed to fetch page: {e}", file=sys.stderr)
        sys.exit(1)

    # Extract audio URL from meta tag or script data
    # Look for og:audio or enclosure URL in the page
    audio_match = re.search(r'"enclosure":\s*\{[^}]*"url":\s*"([^"]+)"', html)
    if not audio_match:
        audio_match = re.search(r'property="og:audio"[^>]*content="([^"]+)"', html)
    if not audio_match:
        audio_match = re.search(r'"mediaUrl":\s*"([^"]+)"', html)
    if not audio_match:
        audio_match = re.search(r'(https://[^"]+\.m4a[^"]*)', html)
    if not audio_match:
        audio_match = re.search(r'(https://[^"]+\.mp3[^"]*)', html)

    if audio_match:
        audio_url = audio_match.group(1)
        return download_direct(audio_url, output)

    # Fallback: try yt-dlp
    print("⚠️  Can't find audio URL, trying yt-dlp...", file=sys.stderr)
    return download_ytdlp(url, output)


def download_xiaoyuzhou_rss(podcast_id: str, output: str) -> str:
    """Download latest episode from 小宇宙 podcast RSS."""
    rss_url = f"https://api.xiaoyuzhoufm.com/v1/podcast/rss/{podcast_id}"
    print(f"⬇️  Fetching RSS: {rss_url}", file=sys.stderr)
    req = urllib.request.Request(rss_url, headers={
        "User-Agent": "Mozilla/5.0"
    })
    try:
        resp = urllib.request.urlopen(req)
        tree = ET.parse(resp)
        root = tree.getroot()

        for item in root.iter("item"):
            enclosure = item.find("enclosure")
            if enclosure is not None:
                audio_url = enclosure.get("url")
                title = item.findtext("title", "episode")
                print(f"📻 Latest: {title}", file=sys.stderr)
                return download_direct(audio_url, output)

        print("❌ No episodes found in RSS", file=sys.stderr)
        sys.exit(1)
    except urllib.error.HTTPError:
        print("⚠️  RSS requires auth, skipping", file=sys.stderr)
        return download_ytdlp(f"https://www.xiaoyuzhoufm.com/podcast/{podcast_id}", output)


def transcribe(audio_path: str, method: str = "auto") -> str:
    """Transcribe audio file."""
    if method == "auto":
        # Try groq-whisper first (fast, cloud), then mlx_whisper (local)
        for cmd in ["groq-whisper", "mlx_whisper"]:
            if subprocess.run(["which", cmd], capture_output=True).returncode == 0:
                method = cmd
                break
        else:
            print("❌ No transcription tool found. Install groq-whisper or mlx_whisper", file=sys.stderr)
            sys.exit(1)

    print(f"📝 Transcribing with {method}...", file=sys.stderr)

    if method == "groq-whisper":
        result = subprocess.run([method, audio_path], capture_output=True, text=True)
    elif method == "mlx_whisper":
        result = subprocess.run([
            method, audio_path,
            "--model", "mlx-community/whisper-large-v3-turbo"
        ], capture_output=True, text=True)
    else:
        result = subprocess.run([method, audio_path], capture_output=True, text=True)

    if result.returncode != 0:
        print(f"❌ Transcription error: {result.stderr}", file=sys.stderr)
        sys.exit(1)

    return result.stdout.strip()


def main():
    parser = argparse.ArgumentParser(
        description="Download and transcribe audio from podcasts and videos",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  podsnap https://youtube.com/watch?v=xxx              # Download + transcribe YouTube
  podsnap https://www.xiaoyuzhoufm.com/episode/xxx     # Download + transcribe 小宇宙
  podsnap https://youtube.com/watch?v=xxx -o talk.mp3   # Download only
  podsnap https://youtube.com/watch?v=xxx --no-transcribe  # Download only
  podsnap local-file.mp3                                 # Transcribe local file
  podsnap https://example.com/podcast.rss --latest 3     # Download latest 3 episodes
        """,
    )
    parser.add_argument("url", help="URL or local file path")
    parser.add_argument("-o", "--output", help="Output audio file path")
    parser.add_argument("--no-transcribe", action="store_true", help="Download only, don't transcribe")
    parser.add_argument("--transcribe-only", action="store_true", help="Transcribe existing local file")
    parser.add_argument("--method", default="auto", help="Transcription method (auto/groq-whisper/mlx_whisper)")
    parser.add_argument("--transcript-output", "-t", help="Save transcript to file")

    args = parser.parse_args()

    # Local file — just transcribe
    if os.path.exists(args.url):
        if args.no_transcribe:
            print("Nothing to do — local file, no transcribe", file=sys.stderr)
            return
        text = transcribe(args.url, args.method)
        if args.transcript_output:
            Path(args.transcript_output).write_text(text)
            print(f"💾 Transcript saved: {args.transcript_output}", file=sys.stderr)
        else:
            print(text)
        return

    # Determine output path
    if args.output:
        audio_path = args.output
    else:
        audio_path = os.path.join(tempfile.gettempdir(), "podsnap-audio.mp3")

    # Download
    source = detect_source(args.url)
    if source == "xiaoyuzhou":
        audio_path = download_xiaoyuzhou(args.url, audio_path)
    elif source == "direct":
        audio_path = download_direct(args.url, audio_path)
    elif source == "rss":
        # TODO: RSS feed support
        print("RSS feed support coming soon. Pass an episode URL instead.", file=sys.stderr)
        sys.exit(1)
    else:
        audio_path = download_ytdlp(args.url, audio_path)

    file_size = os.path.getsize(audio_path) / (1024 * 1024)
    print(f"✅ Downloaded: {audio_path} ({file_size:.1f}MB)", file=sys.stderr)

    # Transcribe
    if not args.no_transcribe:
        text = transcribe(audio_path, args.method)
        if args.transcript_output:
            Path(args.transcript_output).write_text(text)
            print(f"💾 Transcript saved: {args.transcript_output}", file=sys.stderr)
        else:
            print(text)


if __name__ == "__main__":
    main()
