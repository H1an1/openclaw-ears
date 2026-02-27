---
name: spotify
description: Control Spotify playback, browse music library, and manage playlists via the Spotify Web API. Use when the user asks to play music, check what's playing, see top tracks/artists, search songs, create playlists, or access their Spotify listening history.
---

# Spotify

Control Spotify via the Web API using `scripts/spotify.py`.

## Setup (one-time)

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

## Commands

### Info
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

### Playback Control
```bash
spotify.py play                      # Resume
spotify.py play <query>              # Search and play first match
spotify.py play spotify:track:ID     # Play by URI
spotify.py pause
spotify.py next
spotify.py prev
```

### Playlist Management
```bash
spotify.py create-playlist <name>
spotify.py add-to-playlist <playlist_id> <track_uri> [...]
```

### Raw API
```bash
spotify.py raw GET /me/player
spotify.py raw PUT /me/player/volume '{"volume_percent": 50}'
```

## Notes

- Run `auth` in background mode to keep the callback server alive while user authorizes.
- If API returns 401, the script auto-refreshes the token.
- The `play` command requires an active Spotify device (phone, desktop app, or web player).
- `top-tracks`/`top-artists` time ranges: `short_term` (~4 weeks), `medium_term` (~6 months), `long_term` (all time).
