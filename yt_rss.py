# yt_rss.py - 2025 雲端記憶 + 分類推播（用 seen.txt + 自動 commit）
import feedparser
import requests
import os
import sys
from datetime import datetime

# 記憶檔案
seen_file = "seen.txt"

# 讀取記憶（從 seen.txt）
seen = set()
if os.path.exists(seen_file):
    with open(seen_file, "r", encoding="utf-8") as f:
        seen = set(line.strip() for line in f if line.strip())
new_seen = seen.copy()

# 頻道對應 Webhook
CHANNEL_WEBHOOKS = {
    "UCxH2mFGJOqJ15UyCiZ7rN9w": "WEBHOOK_HUANGLING",   # 煌靈
    "UCXOBLGJdYA1mfhOrDwQESTg": "WEBHOOK_STANLEY",     # Stanley
    # 想加更多？直接加一行： "UCxxx": "WEBHOOK_名字"
}

def send_discord(video, webhook_url):
    published_dt = datetime.strptime(video["published"], "%Y-%m-%dT%H:%M:%S%z")
    taiwan_time = published_dt.astimezone()
    time_str = taiwan_time.strftime("%Y/%m/%d")

    # 粗體時間 + 點就看影片（藍色連結）
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
        raw_id = entry.id.split(":", 1)[-1]
        video_id = f"yt:video:{raw_id}"  # 正確格式！

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

    # 寫回記憶 + 自動 commit
    if new_seen != seen:
        with open(seen_file, "w", encoding="utf-8") as f:
            for vid in sorted(new_seen, reverse=True)[:200]:
                f.write(vid + "\n")
        print(f"更新記憶：新增 {len(new_seen - seen)} 筆")

        # 自動 commit + push
        commit_msg = f"更新 YouTube 記憶：新增 {len(new_seen - seen)} 筆影片 ID"
        os.system(f'git add {seen_file}')
        os.system(f'git commit -m "{commit_msg}"')
        os.system('git push')
    else:
        print("沒有新影片～")

if __name__ == "__main__":
    main()

