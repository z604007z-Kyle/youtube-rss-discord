# yt_rss.py - 2025 雲端記憶 + 分類推播（無 .env）
import feedparser
import requests
import os
import sys
from datetime import datetime

# 讀取雲端記憶
seen = set()
state_str = os.getenv("STATE_SEEN", "")
if state_str:
    seen = set(state_str.split(","))
new_seen = seen.copy()

# 頻道對應 Webhook
CHANNEL_WEBHOOKS = {
    "UCxH2mFGJOqJ15UyCiZ7rN9w": "WEBHOOK_HUANGLING",
    "UCXOBLGJdYA1mfhOrDwQESTg": "WEBHOOK_STANLEY",
}

def send_discord(video, webhook_url):
    published_dt = datetime.strptime(video["published"], "%Y-%m-%dT%H:%M:%S%z")
    taiwan_time = published_dt.astimezone()
    time_str = taiwan_time.strftime("%Y/%m/%d %H:%M")

    content = f"[**{time_str}**]({video['url']})"

    r = requests.post(webhook_url, json={
        "content": content,
        "allowed_mentions": {"parse": []}
    })
    if r.status_code == 204:
        print(f"推播成功 → {video['author']}: {video['title'][:30]}...")
    else:
        print(f"推播失敗：{r.status_code}")

def main():
    channels = []
    try:
        with open("channels.txt", "r", encoding="utf-8") as f:
            for line in f:
                line = line.split("#")[0].strip()
                if line.startswith("UC"):
                    channels.append(line)
                    print(f"載入 UC: {line}")
    except FileNotFoundError:
        print("錯誤：channels.txt 不見了！")
        return

    for cid in channels:
        webhook_key = CHANNEL_WEBHOOKS.get(cid)
        if not webhook_key:
            print(f"警告：{cid} 沒有設定 Webhook")
            continue
        webhook_url = os.getenv(webhook_key)
        if not webhook_url:
            print(f"錯誤：環境變數 {webhook_key} 未設定")
            continue

        url = f"https://www.youtube.com/feeds/videos.xml?channel_id={cid}"
        feed = feedparser.parse(url, request_headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        if not feed.entries:
            print(f"抓不到: {cid}")
            continue

        entry = feed.entries[0]
            raw_id = entry.id.split(":", 1)[-1]
            video_id = f"yt:video:{raw_id}"  # 加上 yt:video: 前綴！

        if video_id in new_seen:
            continue

        video = {
            "title": entry.title,
            "url": entry.link,
            "published": entry.published,
            "author": entry.author
        }
        
        send_discord(video, webhook_url)
        new_seen.add(video_id)  # 存完整 ID

    # 寫回雲端記憶
    if new_seen != seen:
        print(f"更新雲端記憶：新增 {len(new_seen - seen)} 筆")
        print(f"::set-state name=STATE_SEEN::{','.join(sorted(new_seen, reverse=True)[:200])}")

    if new_seen == seen:
        print("沒有新影片～")

if __name__ == "__main__":
    main()

