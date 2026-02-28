# 🎧 OpenClaw Ears

Audio superpowers for [OpenClaw](https://github.com/openclaw/openclaw) agents — Spotify control, system audio capture, and podcast/video transcription.

Three tools, one goal: **let your AI agent hear the world.**

## What's Inside

| Tool | What it does |
|------|-------------|
| 🎵 **spotify.py** | Control Spotify — play, pause, search, browse library |
| 🎤 **audiosnap** | Record system audio on macOS (no virtual drivers needed) |
| 🎙️ **podsnap** | Download + transcribe audio from YouTube, 小宇宙, Bilibili, etc. |

---

## 🎵 Spotify

Control Spotify playback via the Web API.

### Setup

1. Create a Spotify app at [developer.spotify.com/dashboard](https://developer.spotify.com/dashboard)
   - Redirect URI: `http://127.0.0.1:8989/login`
   - Enable **Web API**
2. Configure:
   ```bash
   python3 scripts/spotify.py config --client-id YOUR_CLIENT_ID
   python3 scripts/spotify.py auth
   ```

### Commands

```bash
spotify.py now                       # What's playing
spotify.py play "Björk"              # Search and play
spotify.py pause                     # Pause
spotify.py next                      # Next track
spotify.py search "All Is Full Of Love"  # Search
spotify.py top-tracks                # Your top tracks
spotify.py top-artists               # Your top artists
spotify.py recent                    # Recently played
spotify.py playlists                 # Your playlists
spotify.py devices                   # Available devices
spotify.py raw GET /me/player        # Direct API access
```

---

## 🎤 audiosnap

Capture system audio on macOS using Apple's native [ScreenCaptureKit](https://developer.apple.com/documentation/screencapturekit/). No BlackHole, no Soundflower, no kernel extensions.

### Why?

Virtual audio drivers like BlackHole break on every major macOS update. On macOS Tahoe, BlackHole is completely non-functional — the driver appears but passes zero audio. ScreenCaptureKit is Apple's official API and works reliably.

### Build & Install

```bash
cd audiosnap
swift build -c release
ln -s $(pwd)/.build/release/audiosnap /usr/local/bin/audiosnap
```

### Usage

```bash
audiosnap                                # Record 5s → audiosnap-output.wav
audiosnap 10 output.wav                  # Record 10s to file
audiosnap 30 meeting.wav --exclude-self  # Exclude own process audio
audiosnap 5 out.wav --sample-rate 44100 --channels 1
```

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `duration` | Recording duration in seconds | `5` |
| `output` | Output file path | `audiosnap-output.wav` |
| `--exclude-self` | Exclude this process's audio | off |
| `--sample-rate N` | Sample rate in Hz | `48000` |
| `--channels N` | Number of channels | `2` |

### TCC Permission Workaround

macOS requires Screen Recording permission. If running from a process that doesn't have it (like an AI agent daemon), use the wrapper:

```bash
# Automatically falls back to Terminal.app which has the permission
./audiosnap/audiosnap-wrapper.sh 10 output.wav
```

### Requirements

- macOS 13 (Ventura) or later
- Screen Recording permission (prompted on first run)

---

## 🎙️ podsnap

Download and transcribe audio from podcasts, YouTube, and more — one command.

### Install

```bash
ln -s $(pwd)/audiosnap/podsnap.py /usr/local/bin/podsnap
```

### Usage

```bash
podsnap https://youtube.com/watch?v=xxx           # YouTube → transcript
podsnap https://xiaoyuzhoufm.com/episode/xxx      # 小宇宙 → transcript
podsnap https://bilibili.com/video/xxx            # Bilibili → transcript
podsnap https://example.com/podcast.mp3            # Direct URL → transcript
podsnap local-recording.mp3                        # Local file → transcript
```

### Options

```bash
podsnap URL -o audio.mp3              # Save audio to specific path
podsnap URL --no-transcribe           # Download only, skip transcription
podsnap URL -t transcript.txt         # Save transcript to file
podsnap URL --method mlx_whisper      # Use specific transcription engine
```

### Supported Sources

- **YouTube** — via yt-dlp (requires deno for JS challenge solving)
- **小宇宙** — extracts audio URL from episode page
- **Bilibili** — via yt-dlp
- **Apple Podcasts** — via yt-dlp
- **Any yt-dlp supported site** — [1000+ sites](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md)
- **Direct audio URLs** — mp3, m4a, wav, ogg, opus, flac
- **Local files** — just transcribe, no download

### Transcription

podsnap auto-detects the best available transcription tool:
1. **groq-whisper** (cloud, fast) — preferred
2. **mlx_whisper** (local, Apple Silicon) — fallback

### Requirements

- Python 3.8+
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) — for downloading
- [deno](https://deno.land/) — for YouTube JS challenges
- A Whisper transcription tool (groq-whisper or mlx_whisper)

---

## Use Cases

- 🤖 **AI agents** that can listen to music, meetings, podcasts
- 🎙️ **Podcast transcription** — give it a URL, get text
- 📝 **Meeting notes** — record system audio during calls
- 🎵 **Music identification** — record + transcribe lyrics
- 📚 **Video learning** — transcribe lectures and talks

## Origin Story

Born when BlackHole broke on macOS Tahoe and an AI agent wanted to listen to Björk. The agent wrote audiosnap in 160 lines of Swift, then got asked "can it do podcasts too?" — and podsnap was born 🦞

## License

MIT
