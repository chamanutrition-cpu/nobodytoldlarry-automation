import json, os, time, requests
GRAPH = "https://graph.facebook.com/v24.0"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QUEUE = os.path.join(ROOT, "queue.json")

def load_queue():
    return json.load(open(QUEUE, encoding="utf-8"))

def save_queue(q):
    json.dump(q, open(QUEUE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

def env(name):
    v = os.environ.get(name)
    if not v:
        raise SystemExit(f"Missing secret {name}")
    return v

def yt_access_token():
    r = requests.post("https://oauth2.googleapis.com/token", data={
        "client_id": env("YT_CLIENT_ID"), "client_secret": env("YT_CLIENT_SECRET"),
        "refresh_token": env("YT_REFRESH_TOKEN"), "grant_type": "refresh_token"}, timeout=30)
    r.raise_for_status()
    return r.json()["access_token"]

def graph(method, path, **params):
    params.setdefault("access_token", env("META_PAGE_TOKEN"))
    r = requests.request(method, f"{GRAPH}/{path}", data=params if method == "POST" else None,
                         params=params if method == "GET" else None, timeout=60)
    if r.status_code >= 400:
        raise RuntimeError(f"Graph {path}: {r.status_code} {r.text}")
    return r.json()
