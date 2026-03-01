#!/usr/bin/env python3
"""YouTube Music CLI for OpenClaw — via ytmusicapi."""
import json, sys, os

CONFIG_DIR = os.path.expanduser("~/.config/openclaw-ears")
AUTH_FILE = os.path.join(CONFIG_DIR, "ytmusic-auth.json")
os.makedirs(CONFIG_DIR, exist_ok=True)

def get_yt(need_auth=False):
    from ytmusicapi import YTMusic
    if need_auth:
        if not os.path.exists(AUTH_FILE):
            print("Not logged in. Run: ytmusic.py login")
            sys.exit(1)
        return YTMusic(AUTH_FILE)
    return YTMusic()

def print_tracks(items, numbered=True):
    for i, t in enumerate(items, 1):
        title = t.get("title", "?")
        artists = "/".join(a["name"] for a in t.get("artists", []) if a.get("name"))
        vid = t.get("videoId", "?")
        dur = t.get("duration", "")
        prefix = f"{i}. " if numbered else ""
        extra = f" [{dur}]" if dur else ""
        print(f"{prefix}{title} — {artists}{extra} (id:{vid})")

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "help"

    if cmd == "login":
        from ytmusicapi import YTMusic
        print("YouTube Music OAuth login...")
        print("A browser window will open. Sign in with your Google account.\n")
        YTMusic.setup_oauth(filepath=AUTH_FILE, open_browser=True)
        print(f"\nAuth saved to {AUTH_FILE}")

    elif cmd == "login-headers":
        from ytmusicapi import YTMusic
        print("Paste your request headers from browser (YouTube Music).")
        print("Go to music.youtube.com, open DevTools > Network, find a request,")
        print("copy the request headers, paste here, then press Ctrl+D:\n")
        headers = sys.stdin.read()
        YTMusic.setup(filepath=AUTH_FILE, headers_raw=headers)
        print(f"\nAuth saved to {AUTH_FILE}")

    elif cmd == "status":
        yt = get_yt(need_auth=True)
        try:
            account = yt.get_account_info()
            print(f"Logged in as: {account.get('accountName', 'unknown')}")
            print(f"Channel: {account.get('channelHandle', '?')}")
        except Exception as e:
            print(f"Auth check failed: {e}")

    elif cmd == "search":
        query = " ".join(sys.argv[2:])
        if not query:
            print("Usage: ytmusic.py search <query>")
            sys.exit(1)
        yt = get_yt()
        results = yt.search(query, filter="songs", limit=20)
        print_tracks(results)

    elif cmd == "search-albums":
        query = " ".join(sys.argv[2:])
        if not query:
            print("Usage: ytmusic.py search-albums <query>")
            sys.exit(1)
        yt = get_yt()
        results = yt.search(query, filter="albums", limit=10)
        for i, a in enumerate(results, 1):
            artists = "/".join(x["name"] for x in a.get("artists", []) if x.get("name"))
            print(f"{i}. {a.get('title','?')} — {artists} (id:{a.get('browseId','?')})")

    elif cmd == "playlists":
        yt = get_yt(need_auth=True)
        results = yt.get_library_playlists(limit=50)
        for i, p in enumerate(results, 1):
            count = p.get("count", "?")
            print(f"{i}. {p['title']} ({count} tracks) — id:{p['playlistId']}")

    elif cmd == "playlist":
        if len(sys.argv) < 3:
            print("Usage: ytmusic.py playlist <id>")
            sys.exit(1)
        pid = sys.argv[2]
        yt = get_yt()
        result = yt.get_playlist(pid, limit=200)
        tracks = result.get("tracks", [])
        print(f"「{result.get('title', '?')}」— {len(tracks)} tracks\n")
        print_tracks(tracks)

    elif cmd == "likes":
        yt = get_yt(need_auth=True)
        result = yt.get_liked_songs(limit=50)
        tracks = result.get("tracks", [])
        print_tracks(tracks)

    elif cmd == "history":
        yt = get_yt(need_auth=True)
        results = yt.get_history()
        print_tracks(results[:50])

    elif cmd == "album":
        if len(sys.argv) < 3:
            print("Usage: ytmusic.py album <browse_id>")
            sys.exit(1)
        yt = get_yt()
        result = yt.get_album(sys.argv[2])
        artists = "/".join(a["name"] for a in result.get("artists", []) if a.get("name"))
        print(f"「{result.get('title','?')}」— {artists} ({result.get('year','')})\n")
        for i, t in enumerate(result.get("tracks", []), 1):
            dur = t.get("duration", "")
            print(f"{i}. {t.get('title','?')} [{dur}] (id:{t.get('videoId','?')})")

    elif cmd == "artist":
        if len(sys.argv) < 3:
            print("Usage: ytmusic.py artist <channel_id|query>")
            sys.exit(1)
        yt = get_yt()
        arg = sys.argv[2]
        # If it looks like a channel ID, use directly
        if arg.startswith("UC") or arg.startswith("MP"):
            artist = yt.get_artist(arg)
        else:
            # Search for artist
            results = yt.search(arg, filter="artists", limit=1)
            if not results:
                print(f"Artist not found: {arg}")
                sys.exit(1)
            artist = yt.get_artist(results[0]["browseId"])

        print(f"{artist.get('name', '?')}")
        print(f"Subscribers: {artist.get('subscribers', '?')}\n")

        songs = artist.get("songs", {})
        if songs and songs.get("results"):
            print("Top Songs:")
            for i, t in enumerate(songs["results"][:10], 1):
                artists = "/".join(a["name"] for a in t.get("artists", []) if a.get("name"))
                print(f"  {i}. {t.get('title','?')} — {artists}")

    elif cmd == "url":
        if len(sys.argv) < 3:
            print("Usage: ytmusic.py url <video_id>")
            sys.exit(1)
        vid = sys.argv[2]
        print(f"https://music.youtube.com/watch?v={vid}")
        print(f"https://www.youtube.com/watch?v={vid}")

    elif cmd == "download":
        if len(sys.argv) < 3:
            print("Usage: ytmusic.py download <video_id|query> [output_dir]")
            sys.exit(1)
        import subprocess

        arg = sys.argv[2]
        out_dir = sys.argv[3] if len(sys.argv) > 3 else "."

        # If not a video ID, search first
        if len(arg) != 11 or " " in arg:
            query = " ".join(sys.argv[2:])
            yt = get_yt()
            results = yt.search(query, filter="songs", limit=1)
            if not results:
                print(f"No results: {query}")
                sys.exit(1)
            vid = results[0]["videoId"]
            title = results[0].get("title", "?")
            artists = "/".join(a["name"] for a in results[0].get("artists", []) if a.get("name"))
            print(f"Found: {title} — {artists} (id:{vid})")
        else:
            vid = arg

        url = f"https://music.youtube.com/watch?v={vid}"
        os.makedirs(out_dir, exist_ok=True)

        # Use yt-dlp for download
        result = subprocess.run([
            "yt-dlp", "-x", "--audio-format", "mp3", "--audio-quality", "0",
            "-o", os.path.join(out_dir, "%(title)s - %(artist)s.%(ext)s"),
            url
        ], capture_output=True, text=True)

        if result.returncode == 0:
            print(result.stdout.strip().split("\n")[-1] if result.stdout.strip() else "Download complete!")
        else:
            if "yt-dlp" in result.stderr.lower() or result.returncode == 127:
                print("yt-dlp not found. Install: brew install yt-dlp")
            else:
                print(f"Download failed: {result.stderr[:300]}")

    else:
        print("""YouTube Music CLI for OpenClaw

Usage: ytmusic.py <command> [args]

Auth:
  login                     OAuth login (opens browser)
  login-headers             Login via browser headers (paste)
  status                    Check login status

Browse:
  search <query>            Search songs
  search-albums <query>     Search albums
  artist <id|name>          Artist info + top songs
  album <browse_id>         Album tracks
  playlists                 Your playlists
  playlist <id>             Tracks in a playlist
  likes                     Liked songs
  history                   Play history

Audio:
  url <video_id>            Get YouTube/YTMusic URLs
  download <id|query> [dir] Download audio (requires yt-dlp)
""")
