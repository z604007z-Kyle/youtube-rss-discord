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

# ========= 測試模式 =========
if len(sys.argv) > 1 and sys.argv[1] == "test":
    r = requests.post(WEBHOOK, json={"content": "純淨美學版測試成功！\n有縮圖 + 中文時間 + 絕對不擋～"})
    print("測試成功！" if r.status_code == 204 else f"失敗：{r.status_code}")
    sys.exit()

# ========= 記憶檔 =========
seen_file = "seen.txt"
seen = set()
if os.path.exists(seen_file):
    with open(seen_file, "r", encoding="utf-8") as f:
        seen = set(line.strip() for line in f if line.strip())
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
            for raw in f:
                line = raw.split("#")[0].strip()
                if not line:
                    continue
                if line.startswith("UC"):
                    channels.append(("id", line))
                    print(f"載入 UC: {line}")
    except FileNotFoundError:
        print("錯誤：channels.txt 不見了！")
        return

    for ctype, cid in channels:
        url = f"https://www.youtube.com/feeds/videos.xml?channel_id={cid}"
        
        # 防台灣 IP 擋
        feed = feedparser.parse(url, request_headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36'
        })
        
        if not feed.entries:
            print(f"抓不到: {cid}")
            continue

        entry = feed.entries[0]
        video_id = entry.id.split(":", 1)[-1]  # 關鍵：抓 video_id
        
        if video_id in new_seen:
            continue

        # 這裡一定要加 video_id 進去！
        video = {
            "title": entry.title,
            "url": entry.link,
            "published": entry.published,
            "video_id": video_id  # 一定要有這行！
        }
        
        send_discord(video)
        new_seen.add(video_id)

    # 寫回 seen.txt
    with open(seen_file, "w", encoding="utf-8") as f:
        for vid in sorted(new_seen, reverse=True)[:200]:
            f.write(vid + "\n")

    if new_seen == seen:
        print("沒有新影片～")

if __name__ == "__main__":
    main()