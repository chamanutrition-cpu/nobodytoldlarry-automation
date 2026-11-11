"""Publishes any queued episode whose publish_at has arrived.
Facebook Reel + Instagram Reel go out at publish time; YouTube is uploaded up to 48h early
with a native publishAt schedule. Status per platform is written back to queue.json."""
import datetime as dt, time, requests
from common import load_queue, save_queue, graph, env, yt_access_token

def now():
    return dt.datetime.now(dt.timezone.utc)

def post_facebook(ep):
    page = env("META_PAGE_ID")
    start = graph("POST", f"{page}/video_reels", upload_phase="start")
    vid = start["video_id"]
    r = requests.post(f"https://rupload.facebook.com/video-upload/v24.0/{vid}",
                      headers={"Authorization": f"OAuth {env('META_PAGE_TOKEN')}", "file_url": ep["video_url"]}, timeout=120)
    r.raise_for_status()
    for _ in range(60):
        st = graph("GET", vid, fields="status")["status"]
        if st.get("uploading_phase", {}).get("status") == "complete" or st.get("video_status") in ("ready", "upload_complete"):
            break
        time.sleep(10)
    graph("POST", f"{page}/video_reels", upload_phase="finish", video_id=vid,
          video_state="PUBLISHED", description=ep["caption"])
    return vid

def post_instagram(ep):
    ig = env("IG_USER_ID")
    c = graph("POST", f"{ig}/media", media_type="REELS", video_url=ep["video_url"],
              caption=ep["caption"], share_to_feed="true")["id"]
    for _ in range(60):
        s = graph("GET", c, fields="status_code")["status_code"]
        if s == "FINISHED":
            break
        if s == "ERROR":
            raise RuntimeError("Instagram processing error")
        time.sleep(10)
    return graph("POST", f"{ig}/media_publish", creation_id=c)["id"]

def post_youtube(ep, publish_at):
    tok = yt_access_token()
    body = {"snippet": {"title": ep["title"][:100], "description": ep["caption"], "categoryId": "27"},
            "status": {"selfDeclaredMadeForKids": False}}
    if publish_at > now():
        body["status"].update(privacyStatus="private", publishAt=publish_at.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
    else:
        body["status"]["privacyStatus"] = "public"
    init = requests.post("https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status",
                         headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json; charset=UTF-8",
                                  "X-Upload-Content-Type": "video/mp4"}, json=body, timeout=60)
    init.raise_for_status()
    data = requests.get(ep["video_url"], timeout=300).content
    up = requests.put(init.headers["Location"], data=data, headers={"Content-Type": "video/mp4"}, timeout=600)
    up.raise_for_status()
    return up.json()["id"]

def main():
    q = load_queue(); changed = False
    for ep in q["episodes"]:
        at = dt.datetime.fromisoformat(ep["publish_at"])
        for plat, state in list(ep["platforms"].items()):
            if state not in ("queued", "failed"):
                continue
            due = now() >= at if plat != "youtube" else now() >= at - dt.timedelta(hours=48)
            if not due:
                continue
            try:
                rid = {"facebook": post_facebook, "instagram": post_instagram,
                       "youtube": lambda e: post_youtube(e, at)}[plat](ep)
                ep["platforms"][plat] = "done"
                ep.setdefault("ids", {})[plat] = rid
                print(f"{ep['id']} {plat}: posted {rid}")
            except Exception as e:
                ep["platforms"][plat] = "failed"
                ep.setdefault("errors", {})[plat] = str(e)[:500]
                print(f"{ep['id']} {plat}: FAILED {e}")
            changed = True
    if changed:
        save_queue(q)

if __name__ == "__main__":
    main()
