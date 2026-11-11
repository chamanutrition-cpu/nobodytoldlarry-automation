"""Sends the last 14 days of stats to Claude (cheap model) and opens a GitHub issue with the summary.
GitHub emails the issue to the repo owner."""
import csv, datetime as dt, os, requests
from common import ROOT, env

rows = list(csv.reader(open(os.path.join(ROOT, "stats.csv"), encoding="utf-8")))
head, body = rows[0], rows[1:]
cut = (dt.date.today() - dt.timedelta(days=14)).isoformat()
recent = [head] + [r for r in body if r[0] >= cut]
table = "\n".join(",".join(r) for r in recent)
prompt = ("You are the growth analyst for 'Nobody Told Larry', a faceless cartoon channel (funny true stories about money, psychology, dating, history). "
          "Here are daily cumulative stats per post (CSV). In plain, simple English and under 200 words: 1) rank the episodes, "
          "2) say what the winner did differently (topic, hook, length), 3) recommend the topic and first line for the next episode, "
          "4) flag anything broken (e.g. a post with zero views).\n\n" + table)
r = requests.post("https://api.anthropic.com/v1/messages", headers={
    "x-api-key": env("ANTHROPIC_API_KEY"), "anthropic-version": "2023-06-01", "content-type": "application/json"},
    json={"model": os.environ.get("SUMMARY_MODEL", "claude-haiku-5-5"), "max_tokens": 600,
          "messages": [{"role": "user", "content": prompt}]}, timeout=120)
r.raise_for_status()
text = r.json()["content"][0]["text"]
repo = env("GITHUB_REPOSITORY")
requests.post(f"https://api.github.com/repos/{repo}/issues", headers={"Authorization": f"Bearer {env('GITHUB_TOKEN')}"},
              json={"title": f"Weekly performance — {dt.date.today()}", "body": text}).raise_for_status()
print(text)
