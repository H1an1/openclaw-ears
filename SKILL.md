---
name: ears
description: "Music toolkit: Spotify Web API + Netease Cloud Music. Control playback, browse library, manage playlists, download tracks. Use when the user asks about music, playing songs, checking listening history, downloading audio, or managing playlists on either platform."
---

# Ears 🎵

Music toolkit for OpenClaw — Spotify + 网易云音乐.

## Spotify — `scripts/spotify.py`

### Setup (one-time)

1. User creates a Spotify app at https://developer.spotify.com/dashboard
   - Set redirect URI to `http://127.0.0.1:8989/login`
   - Enable Web API
2. Save the client ID:
   ```bash
   python3 scripts/spotify.py config --client-id CLIENT_ID
   ```
3. Authenticate (opens browser):
   ```bash
   python3 scripts/spotify.py auth
   ```

Config stored in `~/.config/openclaw-spotify/`. Token auto-refreshes.

### Commands

#### Info
```bash
spotify.py now                       # Currently playing
spotify.py top-tracks [range] [n]    # Top tracks (short_term|medium_term|long_term)
spotify.py top-artists [range] [n]   # Top artists
spotify.py recent [n]                # Recently played
spotify.py playlists                 # List playlists
spotify.py playlist <id> [n]         # Tracks in a playlist
spotify.py saved [n]                 # Liked tracks
spotify.py following                 # Followed artists
spotify.py search <query>            # Search tracks/artists
spotify.py devices                   # Available playback devices
```

#### Playback Control
```bash
spotify.py play                      # Resume
spotify.py play <query>              # Search and play first match
spotify.py play spotify:track:ID     # Play by URI
spotify.py pause
spotify.py next
spotify.py prev
```

#### Playlist Management
```bash
spotify.py create-playlist <name>
spotify.py add-to-playlist <playlist_id> <track_uri> [...]
```

#### Raw API
```bash
spotify.py raw GET /me/player
spotify.py raw PUT /me/player/volume '{"volume_percent": 50}'
```

### Notes
- If API returns 401, the script auto-refreshes the token.
- `play` requires an active Spotify device.
- Time ranges: `short_term` (~4 weeks), `medium_term` (~6 months), `long_term` (all time).

---

## 网易云音乐 — `scripts/netease.py`

### Setup (one-time)

Dependencies:
```bash
pip3 install pyncm
brew install qrencode  # optional, for terminal QR codes
```

Login via QR code (recommended):
```bash
python3 scripts/netease.py login-qr
```
- Generates a QR code image, user scans with 网易云 app
- For Discord/remote: save QR as PNG with `qrencode -o qr.png -s 10 <URL>` and send the image

Login via SMS:
```bash
python3 scripts/netease.py login <phone> [country_code]
```

Session stored in `~/.config/openclaw-ears/netease-session.json`.

### Commands

#### Auth
```bash
netease.py login <phone> [country]   # Login via SMS (default country: 86)
netease.py login-qr                  # Login via QR code scan
netease.py status                    # Check login status
```

#### Browse
```bash
netease.py search <query>            # Search songs
netease.py playlists                 # Your playlists
netease.py playlist <id>             # Tracks in a playlist
netease.py recent                    # Recently played
netease.py likes                     # Your liked songs
```

#### Audio
```bash
netease.py url <track_id> [bitrate]  # Get audio URL (default 320kbps)
netease.py download <id|query> [dir] # Download a single track
netease.py download-playlist <id> [dir] [--limit N]  # Download playlist
```

#### Playback (macOS desktop app only)
```bash
netease.py play-mac toggle           # Play/pause
netease.py play-mac next             # Next track
netease.py play-mac prev             # Previous track
```

### Notes
- QR login sessions expire; re-login when needed.
- Audio download requires login. Some tracks may be VIP-only or region-locked.
- Playback control only works on macOS with NeteaseMusic.app installed (no remote control).
- Unlike Spotify, 网易云 has no remote playback protocol — phone playback cannot be controlled.

---

## YouTube Music — `scripts/ytmusic.py`

### Setup (one-time)

Dependencies:
```bash
pip3 install ytmusicapi
brew install yt-dlp  # optional, for audio download
```

Login (OAuth, opens browser):
```bash
python3 scripts/ytmusic.py login
```

Auth stored in `~/.config/openclaw-ears/ytmusic-auth.json`.

### Commands

#### Auth
```bash
ytmusic.py login                     # OAuth login (opens browser)
ytmusic.py login-headers             # Login via browser headers
ytmusic.py status                    # Check login status
```

#### Browse
```bash
ytmusic.py search <query>            # Search songs
ytmusic.py search-albums <query>     # Search albums
ytmusic.py artist <id|name>          # Artist info + top songs
ytmusic.py album <browse_id>         # Album tracks
ytmusic.py playlists                 # Your playlists
ytmusic.py playlist <id>             # Tracks in a playlist
ytmusic.py likes                     # Liked songs
ytmusic.py history                   # Play history
```

#### Audio
```bash
ytmusic.py url <video_id>            # Get YouTube/YTMusic URLs
ytmusic.py play <id|query>           # Open in browser and play
ytmusic.py download <id|query> [dir] # Download audio (requires yt-dlp)
```

### Notes
- Search works without login. Playlists/likes/history require auth.
- `play` opens YouTube Music in the default browser.
- Download uses `yt-dlp` — install separately (`brew install yt-dlp`).
- No remote playback control API — `play` only opens browser on local machine.

---

## Apple Music — `scripts/applemusic.py`

### Setup

No setup needed for search. Music.app control requires macOS Automation permission:
- System Settings → Privacy & Security → Automation → enable Music.app for Terminal

### Commands

#### Search (no auth, uses iTunes Search API)
```bash
applemusic.py search <query>         # Search songs
applemusic.py search-albums <query>  # Search albums
applemusic.py artist <name>          # Artist info + top songs
applemusic.py album <album_id>       # Album tracks
applemusic.py lookup <track_id>      # Track details
```

#### Play
```bash
applemusic.py play <id|query>        # Open in Music.app / browser
applemusic.py preview <id|query>     # Play 30s preview locally (afplay)
```

#### Music.app Control (macOS only)
```bash
applemusic.py now                    # Currently playing
applemusic.py pause                  # Pause
applemusic.py resume                 # Resume
applemusic.py next                   # Next track
applemusic.py prev                   # Previous track
applemusic.py local-playlists        # List local playlists
```

### Notes
- Search uses the free iTunes Search API — no Apple Developer account needed.
- Music.app control requires macOS Automation permission.
- `preview` plays a 30-second preview clip via `afplay`.
- No access to personal library (liked songs, playlists) without MusicKit ($99/yr Apple Developer).

---

## QQ 音乐 — `scripts/qqmusic.py`

### Setup

No setup needed for search. Login required for playlists and some downloads.

Login via browser cookie (paste):
```bash
python3 scripts/qqmusic.py login
```

Login via QR code (QQ app scan):
```bash
python3 scripts/qqmusic.py login-qr
```

Cookie stored in `~/.config/openclaw-ears/qqmusic-cookie.txt`.

### Commands

#### Auth
```bash
qqmusic.py login                     # Login via browser cookie
qqmusic.py login-qr                  # Login via QQ QR code
qqmusic.py status                    # Check login status
```

#### Browse
```bash
qqmusic.py search <query>            # Search songs
qqmusic.py search-albums <query>     # Search albums
qqmusic.py playlists                 # Your playlists (needs login)
qqmusic.py playlist <id>             # Tracks in a playlist
```

#### Audio
```bash
qqmusic.py url <songmid>             # Get audio URL
qqmusic.py play <mid|query>          # Open in browser
qqmusic.py download <mid|query> [dir] # Download audio
```

### Notes
- Search works without login.
- Login uses QQ/WeChat cookie from browser — no official OAuth.
- VIP tracks may not be downloadable without VIP subscription.
- No playback control API.
