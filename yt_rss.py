# yt_rss.py - 台灣終極純淨美學版（有縮圖 + 只顯示中文時間 + 永不擋）
import feedparser
import requests
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
WEBHOOK = os.getenv("DISCORD_WEBHOOK")

if not WEBHOOK:
    print("錯誤：.env 沒填 DISCORD_WEBHOOK")
    sys.exit(1)

# 讀取雲端記憶（GitHub State）
seen = set()
state_str = os.getenv("STATE_SEEN", "")
if state_str:
    seen = set(state_str.split(","))

new_seen = seen.copy()

def send_discord(video):
    # 台灣時間
    published_dt = datetime.strptime(video["published"], "%Y-%m-%dT%H:%M:%S%z")
    taiwan_time = published_dt.astimezone()
    time_str = taiwan_time.strftime("%Y/%m/%d %H:%M")

    # 關鍵：**粗體** + 超連結 → 點粗體時間就直接看影片！
    content = f"[**{time_str}**]({video['url']})"

    r = requests.post(WEBHOOK, json={"content": content})
    if r.status_code == 204:
        print(f"推播成功：{video['title'][:40]}...")
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
            print(f"警告：{cid} 沒有設定 Webhook，跳過")
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
        video_id = entry.id.split(":", 1)[-1]
        
        if video_id in new_seen:
            continue

        video = {
            "title": entry.title,
            "url": entry.link,
            "published": entry.published,
            "author": entry.author
        }
        
        send_discord(video, webhook_url)
        new_seen.add(video_id)

    # 關鍵：寫回雲端記憶！
    if new_seen != seen:
        print(f"更新雲端記憶：新增 {len(new_seen - seen)} 筆")
        print(f"::set-state name=STATE_SEEN::{','.join(sorted(new_seen, reverse=True)[:200])}")

    if new_seen == seen:
        print("沒有新影片～")

if __name__ == "__main__":

    main()
