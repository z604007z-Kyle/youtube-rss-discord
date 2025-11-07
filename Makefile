include .env
export

yt:
	@python yt_rss.py

test:
	@curl -H "Content-Type: application/json" -d '{"content": "YouTube 通知系統已啟動！🎉"}' $(DISCORD_WEBHOOK)