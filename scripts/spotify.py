#!/usr/bin/env python3
"""Spotify CLI for OpenClaw — OAuth PKCE auth + Web API client."""
import http.server, json, sys, os, hashlib, base64, secrets, threading, subprocess
import urllib.parse
import urllib.request
import urllib.error

DEFAULT_CLIENT_ID = ""
PORT = 8989
REDIRECT_URI = f"http://127.0.0.1:{PORT}/login"
SCOPES = (
    "user-read-playback-state user-read-currently-playing user-modify-playback-state "
    "playlist-read-private playlist-read-collaborative playlist-modify-public playlist-modify-private "
    "user-follow-read user-follow-modify user-top-read user-read-recently-played "
    "user-library-read user-library-modify user-read-private user-read-email"
)
CONFIG_DIR = os.path.expanduser("~/.config/openclaw-spotify")
TOKEN_FILE = os.path.join(CONFIG_DIR, "token.json")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

os.makedirs(CONFIG_DIR, exist_ok=True)

def get_client_id():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE) as f:
            cfg = json.load(f)
            if cfg.get("client_id"):
                return cfg["client_id"]
    if DEFAULT_CLIENT_ID:
        return DEFAULT_CLIENT_ID
    print("ERROR: No client_id configured. Run: spotify.py config --client-id YOUR_CLIENT_ID")
    sys.exit(1)

def save_config(client_id):
    cfg = {}
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE) as f:
            cfg = json.load(f)
    cfg["client_id"] = client_id
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2)
    os.chmod(CONFIG_FILE, 0o600)
    print(f"Client ID saved to {CONFIG_FILE}")

def get_token():
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE) as f:
            data = json.load(f)
            if "access_token" in data:
                return data["access_token"]
    return None

def get_refresh_token():
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE) as f:
            data = json.load(f)
            return data.get("refresh_token")
    return None

def refresh_access_token():
    rt = get_refresh_token()
    if not rt:
        return None
    client_id = get_client_id()
    data = urllib.parse.urlencode({
        "grant_type": "refresh_token",
        "refresh_token": rt,
        "client_id": client_id,
    }).encode()
    req = urllib.request.Request(
        "https://accounts.spotify.com/api/token",
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    try:
        resp = urllib.request.urlopen(req)
        token_data = json.loads(resp.read())
        # Preserve refresh_token if not returned
        if "refresh_token" not in token_data:
            token_data["refresh_token"] = rt
        with open(TOKEN_FILE, "w") as f:
            json.dump(token_data, f, indent=2)
        os.chmod(TOKEN_FILE, 0o600)
        return token_data.get("access_token")
    except urllib.error.HTTPError:
        return None

def auth():
    client_id = get_client_id()
    verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(verifier.encode()).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
    state = secrets.token_urlsafe(16)

    params = urllib.parse.urlencode({
        "response_type": "code",
        "client_id": client_id,
        "state": state,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPES,
    })
    auth_url = f"https://accounts.spotify.com/authorize?{params}"

    code_holder = {}

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path.startswith("/login"):
                qs = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
                code_holder["code"] = qs.get("code", [None])[0]
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(b"<h1>Success! Close this tab.</h1>")
                threading.Thread(target=self.server.shutdown).start()
        def log_message(self, *a):
            pass

    server = http.server.HTTPServer(("127.0.0.1", PORT), Handler)
    print(f"AUTH_URL:{auth_url}")
    sys.stdout.flush()

    try:
        subprocess.Popen(["open", auth_url], stderr=subprocess.DEVNULL)
    except FileNotFoundError:
        try:
            subprocess.Popen(["xdg-open", auth_url], stderr=subprocess.DEVNULL)
        except FileNotFoundError:
            pass

    server.serve_forever()

    code = code_holder.get("code")
    if not code:
        print("ERROR: No authorization code received")
        sys.exit(1)

    data = urllib.parse.urlencode({
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "client_id": client_id,
        "code_verifier": verifier,
    }).encode()
    req = urllib.request.Request(
        "https://accounts.spotify.com/api/token",
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    resp = urllib.request.urlopen(req)
    token_data = json.loads(resp.read())

    with open(TOKEN_FILE, "w") as f:
        json.dump(token_data, f, indent=2)
    os.chmod(TOKEN_FILE, 0o600)
    print(f"TOKEN_SAVED:{TOKEN_FILE}")
    return token_data["access_token"]

def api(endpoint, method="GET", body=None):
    token = get_token()
    if not token:
        print("No token. Run: spotify.py auth")
        sys.exit(1)

    url = f"https://api.spotify.com/v1{endpoint}"
    data = json.dumps(body).encode() if body else None
    headers = {"Authorization": f"Bearer {token}"}
    if body:
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        resp = urllib.request.urlopen(req)
        if resp.status == 204:
            return {}
        return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        if e.code == 401:
            # Try refresh
            new_token = refresh_access_token()
            if new_token:
                headers["Authorization"] = f"Bearer {new_token}"
                req = urllib.request.Request(url, data=data, headers=headers, method=method)
                try:
                    resp = urllib.request.urlopen(req)
                    if resp.status == 204:
                        return {}
                    return json.loads(resp.read())
                except urllib.error.HTTPError as e2:
                    print(f"API Error {e2.code}: {e2.read().decode()}")
                    sys.exit(1)
            else:
                print("Token expired. Run: spotify.py auth")
                sys.exit(1)
        print(f"API Error {e.code}: {e.read().decode()}")
        sys.exit(1)

def print_tracks(items, numbered=True):
    for i, t in enumerate(items, 1):
        artists = ", ".join(a["name"] for a in t["artists"])
        prefix = f"{i}. " if numbered else ""
        print(f"{prefix}{t['name']} — {artists}")

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "help"

    if cmd == "config":
        if "--client-id" in sys.argv:
            idx = sys.argv.index("--client-id")
            if idx + 1 < len(sys.argv):
                save_config(sys.argv[idx + 1])
            else:
                print("Usage: spotify.py config --client-id YOUR_CLIENT_ID")
        else:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE) as f:
                    print(json.dumps(json.load(f), indent=2))
            else:
                print("No config found.")

    elif cmd == "auth":
        auth()

    elif cmd == "top-tracks":
        time_range = sys.argv[2] if len(sys.argv) > 2 else "medium_term"
        limit = int(sys.argv[3]) if len(sys.argv) > 3 else 50
        data = api(f"/me/top/tracks?limit={limit}&time_range={time_range}")
        print_tracks(data["items"])

    elif cmd == "top-artists":
        time_range = sys.argv[2] if len(sys.argv) > 2 else "medium_term"
        limit = int(sys.argv[3]) if len(sys.argv) > 3 else 50
        data = api(f"/me/top/artists?limit={limit}&time_range={time_range}")
        for i, a in enumerate(data["items"], 1):
            genres = ", ".join(a.get("genres", [])[:3])
            g = f" ({genres})" if genres else ""
            print(f"{i}. {a['name']}{g}")

    elif cmd == "recent":
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 50
        data = api(f"/me/player/recently-played?limit={limit}")
        for i, item in enumerate(data["items"], 1):
            t = item["track"]
            artists = ", ".join(a["name"] for a in t["artists"])
            print(f"{i}. {t['name']} — {artists}")

    elif cmd == "now":
        data = api("/me/player/currently-playing")
        if not data or not data.get("item"):
            print("Nothing playing.")
        else:
            t = data["item"]
            artists = ", ".join(a["name"] for a in t["artists"])
            progress = data.get("progress_ms", 0) // 1000
            duration = t.get("duration_ms", 0) // 1000
            state = "▶" if data.get("is_playing") else "⏸"
            print(f"{state} {t['name']} — {artists}")
            print(f"  {progress // 60}:{progress % 60:02d} / {duration // 60}:{duration % 60:02d}")
            print(f"  Album: {t['album']['name']}")

    elif cmd == "playlists":
        data = api("/me/playlists?limit=50")
        for i, p in enumerate(data["items"], 1):
            total = p.get("tracks", {}).get("total", "?")
            print(f"{i}. {p['name']} ({total} tracks) — id:{p['id']}")

    elif cmd == "playlist":
        pid = sys.argv[2]
        limit = int(sys.argv[3]) if len(sys.argv) > 3 else 100
        data = api(f"/playlists/{pid}/tracks?limit={limit}")
        for i, item in enumerate(data["items"], 1):
            t = item.get("track")
            if t:
                artists = ", ".join(a["name"] for a in t["artists"])
                print(f"{i}. {t['name']} — {artists}")

    elif cmd == "saved":
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 50
        data = api(f"/me/tracks?limit={limit}")
        for i, item in enumerate(data["items"], 1):
            t = item["track"]
            artists = ", ".join(a["name"] for a in t["artists"])
            print(f"{i}. {t['name']} — {artists}")

    elif cmd == "following":
        data = api("/me/following?type=artist&limit=50")
        for i, a in enumerate(data["artists"]["items"], 1):
            genres = ", ".join(a.get("genres", [])[:3])
            g = f" ({genres})" if genres else ""
            print(f"{i}. {a['name']}{g}")

    elif cmd == "search":
        query = " ".join(sys.argv[2:])
        if not query:
            print("Usage: spotify.py search <query>")
            sys.exit(1)
        data = api(f"/search?q={urllib.parse.quote(query)}&type=track,artist&limit=10")
        if data.get("tracks", {}).get("items"):
            print("Tracks:")
            print_tracks(data["tracks"]["items"])
        if data.get("artists", {}).get("items"):
            print("\nArtists:")
            for i, a in enumerate(data["artists"]["items"], 1):
                print(f"{i}. {a['name']} (followers: {a.get('followers', {}).get('total', '?')})")

    elif cmd == "play":
        if len(sys.argv) > 2:
            uri = sys.argv[2]
            if uri.startswith("spotify:"):
                if "track" in uri:
                    api("/me/player/play", "PUT", {"uris": [uri]})
                else:
                    api("/me/player/play", "PUT", {"context_uri": uri})
            else:
                # Search and play first result
                data = api(f"/search?q={urllib.parse.quote(' '.join(sys.argv[2:]))}&type=track&limit=1")
                if data.get("tracks", {}).get("items"):
                    track = data["tracks"]["items"][0]
                    artists = ", ".join(a["name"] for a in track["artists"])
                    print(f"Playing: {track['name']} — {artists}")
                    api("/me/player/play", "PUT", {"uris": [track["uri"]]})
                else:
                    print("No results found.")
                    sys.exit(1)
        else:
            api("/me/player/play", "PUT")
            print("Resumed playback.")

    elif cmd == "pause":
        api("/me/player/pause", "PUT")
        print("Paused.")

    elif cmd == "next":
        api("/me/player/next", "POST")
        print("Skipped to next.")

    elif cmd == "prev":
        api("/me/player/previous", "POST")
        print("Previous track.")

    elif cmd == "devices":
        data = api("/me/player/devices")
        for d in data.get("devices", []):
            active = " ✓" if d["is_active"] else ""
            print(f"- {d['name']} ({d['type']}){active} — id:{d['id']}")

    elif cmd == "create-playlist":
        name = sys.argv[2] if len(sys.argv) > 2 else "New Playlist"
        me = api("/me")
        data = api(f"/users/{me['id']}/playlists", "POST", {
            "name": name,
            "public": False,
        })
        print(f"Created: {data['name']} — id:{data['id']}")

    elif cmd == "add-to-playlist":
        if len(sys.argv) < 4:
            print("Usage: spotify.py add-to-playlist <playlist_id> <track_uri> [track_uri...]")
            sys.exit(1)
        pid = sys.argv[2]
        uris = sys.argv[3:]
        api(f"/playlists/{pid}/tracks", "POST", {"uris": uris})
        print(f"Added {len(uris)} track(s) to playlist.")

    elif cmd == "raw":
        # Raw API call: spotify.py raw GET /me/player
        method = sys.argv[2].upper() if len(sys.argv) > 2 else "GET"
        endpoint = sys.argv[3] if len(sys.argv) > 3 else "/me"
        body = json.loads(sys.argv[4]) if len(sys.argv) > 4 else None
        result = api(endpoint, method, body)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    else:
        print("""Spotify CLI for OpenClaw

Usage: spotify.py <command> [args]

Setup:
  config --client-id ID   Save Spotify app client ID
  auth                    Authenticate with Spotify (opens browser)

Info:
  now                     Currently playing track
  top-tracks [range] [n]  Top tracks (short_term|medium_term|long_term)
  top-artists [range] [n] Top artists
  recent [n]              Recently played
  playlists               List your playlists
  playlist <id> [n]       Show tracks in a playlist
  saved [n]               Liked/saved tracks
  following               Followed artists
  search <query>          Search tracks and artists
  devices                 List available devices

Playback:
  play [query|uri]        Play track/playlist or resume
  pause                   Pause playback
  next                    Skip to next track
  prev                    Previous track

Playlists:
  create-playlist <name>          Create a new playlist
  add-to-playlist <id> <uris...>  Add tracks to playlist

Advanced:
  raw <METHOD> <endpoint> [body]  Raw Spotify API call""")
