"""Appends one row per episode per platform per day to stats.csv."""
import csv, datetime as dt, os, requests
from common import load_queue, graph, env, yt_access_token, ROOT

OUT = os.path.join(ROOT, "stats.csv")

def ig_stats():
    rows = {}
    media = graph("GET", f"{env('IG_USER_ID')}/media", fields="id,caption,media_product_type,timestamp", limit=50)["data"]
    for m in media:
        try:
            ins = graph("GET", f"{m['id']}/insights", metric="views,reach,likes,comments,shares,saved")["data"]
            rows[m["id"]] = {"caption": (m.get("caption") or "")[:60], **{i["name"]: i["values"][0]["value"] for i in ins}}
        except Exception as e:
            print("ig", m["id"], e)
    return rows

def fb_stats():
    rows = {}
    vids = graph("GET", f"{env('META_PAGE_ID')}/video_reels", fields="id,description,created_time", limit=50)["data"]
    for v in vids:
        try:
            ins = graph("GET", f"{v['id']}/video_insights")["data"]
            d = {i["name"]: i["values"][0]["value"] for i in ins if i.get("values")}
            rows[v["id"]] = {"caption": (v.get("description") or "")[:60], "views": d.get("blue_reels_play_count") or d.get("fb_reels_total_plays"),
                             "reach": d.get("post_impressions_unique"), "likes": None, "comments": None, "shares": None, "saved": None}
        except Exception as e:
            print("fb", v["id"], e)
    return rows

def yt_stats():
    tok = yt_access_token(); h = {"Authorization": f"Bearer {tok}"}
    ch = requests.get("https://www.googleapis.com/youtube/v3/channels", params={"part": "contentDetails", "mine": "true"}, headers=h).json()
    uploads = ch["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
    items = requests.get("https://www.googleapis.com/youtube/v3/playlistItems", params={"part": "contentDetails,snippet", "playlistId": uploads, "maxResults": 50}, headers=h).json()["items"]
    ids = ",".join(i["contentDetails"]["videoId"] for i in items)
    vs = requests.get("https://www.googleapis.com/youtube/v3/videos", params={"part": "statistics,snippet", "id": ids}, headers=h).json()["items"]
    return {v["id"]: {"caption": v["snippet"]["title"][:60], "views": v["statistics"].get("viewCount"), "reach": None,
                      "likes": v["statistics"].get("likeCount"), "comments": v["statistics"].get("commentCount"), "shares": None, "saved": None} for v in vs}

def main():
    today = dt.date.today().isoformat()
    new = not os.path.exists(OUT)
    with open(OUT, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["date", "platform", "post_id", "caption", "views", "reach", "likes", "comments", "shares", "saved"])
        for plat, fn in (("instagram", ig_stats), ("facebook", fb_stats), ("youtube", yt_stats)):
            try:
                for pid, r in fn().items():
                    w.writerow([today, plat, pid, r["caption"], r.get("views"), r.get("reach"), r.get("likes"), r.get("comments"), r.get("shares"), r.get("saved")])
            except Exception as e:
                print(plat, "stats failed:", e)

if __name__ == "__main__":
    main()
