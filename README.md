# 🎵 Spotify Skill for OpenClaw

Control Spotify playback, browse your music library, and manage playlists — all from OpenClaw.

## Setup

1. Create a Spotify app at [developer.spotify.com/dashboard](https://developer.spotify.com/dashboard)
   - Set redirect URI to `http://127.0.0.1:8989/login`
   - Enable **Web API**
2. Configure your client ID:
   ```bash
   python3 scripts/spotify.py config --client-id YOUR_CLIENT_ID
   ```
3. Authenticate (opens browser):
   ```bash
   python3 scripts/spotify.py auth
   ```

## What You Can Do

| Command | Description |
|---------|-------------|
| `now` | What's currently playing |
| `top-tracks` | Your top tracks (short/medium/long term) |
| `top-artists` | Your top artists |
| `recent` | Recently played |
| `playlists` | List your playlists |
| `search <query>` | Search tracks & artists |
| `play <query>` | Search and play |
| `pause` / `next` / `prev` | Playback control |
| `create-playlist <name>` | Create a new playlist |
| `devices` | List available devices |
| `raw <METHOD> <endpoint>` | Direct Spotify API access |

## Requirements

- Python 3.8+
- A Spotify account (free or premium)
- OpenClaw (optional — works standalone too)

## License

MIT
