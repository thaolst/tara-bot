# TARA BOT 🤖✈️🛒

[![Version](https://img.shields.io/badge/version-v2.1.0-brightgreen?style=flat-square)](https://github.com/thaolst/tara-bot/releases)
[![GitHub stars](https://img.shields.io/github/stars/thaolst/tara-bot?style=flat-square&color=yellow)](https://github.com/thaolst/tara-bot/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/thaolst/tara-bot?style=flat-square&color=blue)](https://github.com/thaolst/tara-bot/network/members)

**AI agent cá nhân trên Telegram — săn vé máy bay, so sánh giá, cào deal.**

[![Deploy on Fly.io](https://img.shields.io/badge/deploy-fly.io-6a0dad?style=flat-square)](https://fly.io)
[![License: MIT](https://img.shields.io/badge/license-MIT-4ade80?style=flat-square)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-60a5fa?style=flat-square)](https://python.org)

> Build bởi **Lê Song Tiên Thảo** · [GitHub](https://github.com/thaolst) · [LinkedIn](https://www.linkedin.com/in/thaolst/) · [Facebook](https://www.facebook.com/LeSongTienThao)
>
> Đây là side project. Repo chính của mình về AI x growth marketing: [growth-mcp](https://github.com/thaolst/growth-mcp) (MCP server, `pip install growth-mcp`) và [ai-growth-prompts](https://github.com/thaolst/ai-growth-prompts).

## ✨ Tính năng

| Tính năng | Mô tả | Trạng thái |
|---|---|---|
| 💬 **Chat tự nhiên** | Hỏi "tìm vé SG Đà Nẵng cuối tuần" — Claude hiểu ngữ cảnh, tự gọi đúng tool | ✅ |
| ✈️ **Tìm vé máy bay** | Giá real-time từ Google Flights, top 5 chuyến, link Google Flights | ✅ |
| 🛒 **So sánh giá sản phẩm** | Google Shopping — giá, rating, shop, link mua trực tiếp | ✅ |
| 🗓️ **Xem ngày giờ xuất hành** | Tính Can Chi, giờ Hoàng Đạo, xung hợp tuổi theo lịch can chi truyền thống. Chỉ chạy khi bạn chủ động hỏi, mặc định vẫn tìm vé thẳng. Tham khảo, không phải dự báo có cơ sở khoa học | ✅ |
| 👨‍👩‍👧 **Xem ngày cho nhóm** | 2-5 người cùng đi: loại ngày xung với bất kỳ ai, tìm ngày an toàn cho cả nhóm | ✅ |
| 🔔 **Daily price monitor** | 9AM mỗi sáng tự động check giá 4 tuyến SGN↔HAN/DAD/PQC, gửi Telegram | ✅ |
| 🧠 **Memory trong session** | LLM nhớ toàn bộ lịch sử chat, hỏi tiếp không cần nhắc lại | ✅ |
| ⚡ **Prompt caching** | Cache system prompt từ turn 2 → tiết kiệm ~90% token cost (Anthropic) | ✅ |
| 🧩 **Adaptive thinking** | Claude tự bật extended thinking khi câu hỏi phức tạp (Anthropic) | ✅ |
| 🔄 **LLM mode switch** | Hỗ trợ Anthropic Claude hoặc OpenAI-compatible (Gemini, local LLM) | ✅ |
| 🔁 **Multi-turn tool loop** | Một lượt hỏi có thể gọi nhiều tool liên tiếp, tối đa 5 vòng | ✅ |
| 🔗 **Google Flights link** | Mỗi kết quả vé kèm link tìm thêm trên Google Flights | ✅ |
| 🛡️ **Private mode** | `ALLOWED_USER_ID` — chỉ bạn mới dùng được bot | ✅ |
| 🔄 **Commands** | `/start` `/reset` `/uptime` | ✅ |
| 🏥 **Health check** | HTTP endpoint cho Fly.io keepalive | ✅ |
| 🆕 **Shopee cào giá** | | 🔜 |
| 🔔 **Auto-deal alert** | Notify khi giá rẻ hơn ngưỡng đặt | 🔜 |
| 👥 **Multi-user** | | 🔜 |

## 🎬 Demo

```
👤: tìm vé SG Hà Nội thứ 7 tuần này

🤖: ✈️ Sài Gòn → Hà Nội
    📅 2026-05-16 → 2026-05-21 (5 chuyến)

    🏆 1,450,000đ 06:00→08:05 (2h5)
       `Vietjet Air VJ123` · *Thẳng*

    🥈 1,890,000đ 09:30→11:35 (2h5)
       `Bamboo Airways QH201` · *Thẳng*

    🥉 2,100,000đ 08:30→10:30 (2h0)
       `Vietnam Airlines VN123` · *Thẳng*

    [🔍 Xem thêm trên Google Flights](https://google.com/travel/flights?...)
```

```
👤: iPhone 16 giá bao nhiêu

🤖: 🛒 iPhone 16 (6 kết quả)

    🥇 *22,990,000đ* 🔥 — CellphoneS
       ⭐⭐⭐⭐ 4.8 (2,341 đánh giá)
       🔗 https://cellphones.com.vn/...

    🥈 *23,500,000đ* — Thế Giới Di Động
       ⭐⭐⭐⭐ 4.7 (1,890 đánh giá)
```

```
👤: mình sinh 1995, xem ngày tốt đi Đà Nẵng tháng 7

🤖: Tuổi Hợi 🐗 (1995), mình xem ngày xuất hành tháng 7 cho bạn.

    Ngày đẹp nhất là 2026-07-06 (Thứ 2), ngày Đinh Mão 🐰 - rất tốt, tam hợp.
    Giờ tốt trong ngày: 07:00-09:00, 11:00-13:00, 17:00-19:00.

    Mấy ngày khác cũng đẹp nếu cần lùi lịch:
    🟢 2026-07-05 (Chủ Nhật) - rất tốt
    🟢 2026-07-09 (Thứ 5) - tốt

    Bạn muốn mình tìm vé cho ngày nào không?

    Lưu ý: đây chỉ là tham khảo theo lịch can chi truyền thống,
    không phải dự báo có cơ sở khoa học.
```

## 🧱 Tech stack

```
┌──────────────┐     ┌──────────────────────────┐     ┌──────────────────┐
│   Telegram   │ ←→  │      LLM Backend          │ ←→  │     SerpAPI      │
│     Bot      │     │(Anthropic / OpenAI-compat)│     │  · Google Flights│
│              │     │  · Multi-turn tool loop   │     │  · Google Shopping│
│  /start      │     │  · Prompt caching         │     └──────────────────┘
│  /reset      │     │  · Adaptive thinking      │
│  /uptime     │     │  · Session memory         │
└──────────────┘     └──────────────────────────┘
│  /uptime     │     └──────────────────────────┘
└──────────────┘
                      ┌──────────────────────────┐
                      │      GitHub Actions       │
                      │  · 9AM daily monitor      │
                      │  · 4 tuyến bay cố định    │
                      └──────────────────────────┘
```

| Thành phần | Chi tiết |
|---|---|
| **AI** | Claude Sonnet 4.6 (Anthropic) hoặc OpenAI-compatible (Gemini, ...) |
| **Bot** | python-telegram-bot v20+ |
| **Search** | SerpAPI — Google Flights + Google Shopping |
| **Host** | Fly.io free tier, region Singapore |
| **Scheduler** | GitHub Actions cron, 9AM Vietnam (UTC+7) |
| **Language** | Python 3.11+ |

## 🚀 Deploy trong 5 phút

### 1. Chuẩn bị API keys

| Key | Lấy ở đâu | Free quota |
|---|---|---|
| `TELEGRAM_TOKEN` | [@BotFather](https://t.me/botfather) → `/newbot` | Không giới hạn |
| `ALLOWED_USER_ID` | [@userinfobot](https://t.me/userinfobot) → `/start` | — |
| `TELEGRAM_CHAT_ID` | Giống `ALLOWED_USER_ID` | — |
| `LLM_MODE` | `anthropic` or `openai` | `anthropic` |
| `ANTHROPIC_API_KEY` | [console.anthropic.com](https://console.anthropic.com/settings/keys) | $5 free credit |
| `OPENAI_API_KEY` | [Google AI Studio](https://aistudio.google.com/app/apikey) | Free tier |
| `SERPAPI_KEY` | [serpapi.com](https://serpapi.com) | 250 req/tháng |

### 2. Deploy lên Fly.io

```bash
git clone https://github.com/thaolst/tara-bot
cd tara-bot

fly auth login
fly launch --from Dockerfile --name tara-bot-yourname

fly secrets set \
  TELEGRAM_TOKEN=xxx \
  ANTHROPIC_API_KEY=xxx \
  SERPAPI_KEY=xxx \
  ALLOWED_USER_ID=xxx \
  TELEGRAM_CHAT_ID=xxx

fly deploy
```

### 3. Bật daily monitor

- GitHub repo → **Settings → Secrets → Actions** → thêm 3 secrets: `SERPAPI_KEY`, `TELEGRAM_TOKEN`, `TELEGRAM_CHAT_ID`
- **Actions tab** → **Flight Monitor** → Enable workflow

*Chi tiết đầy đủ: [DEPLOY.md](./DEPLOY.md)*

## ⚙️ Cấu hình

| Env var | Bắt buộc | Mô tả |
|---|---|---|
| `ANTHROPIC_API_KEY` | ✅ | Anthropic API key |
| `TELEGRAM_TOKEN` | ✅ | Telegram Bot token từ @BotFather |
| `ALLOWED_USER_ID` | ✅ | Telegram user ID — chỉ ID này mới dùng được bot |
| `SERPAPI_KEY` | ✅ | SerpAPI key cho Flights + Shopping |
| `TELEGRAM_CHAT_ID` | ✅ | Chat ID nhận daily monitor (thường = ALLOWED_USER_ID) |
| `AFFILIATE_TEMPLATE` | ❌ | Template URL affiliate (coming soon) |

## 📁 Cấu trúc

```
tara-bot/
├── src/
│   ├── bot.py          # Telegram bot — polling, session, /start /reset /uptime
│   ├── agents.py       # Claude agent — tool loop, prompt caching, adaptive thinking
│   ├── config.py       # Env config loader
│   └── tools/
│       ├── serpapi.py      # Flight search + Shopping search
│       └── lucky_dates.py  # Xem ngày giờ tốt theo lịch can chi (tham khảo)
├── scripts/
│   └── monitor.py      # Daily price check — chạy bởi GitHub Actions
├── .github/workflows/
│   └── monitor.yml     # Cron 9AM Vietnam daily
├── Dockerfile
├── fly.toml            # Fly.io config — region Singapore, 1GB RAM
├── DEPLOY.md
└── CHANGELOG.md
```

## 💰 Chi phí

| Service | Cost | Ghi chú |
|---|---|---|
| Fly.io | $0 | Free tier đủ dùng |
| SerpAPI | $0 | 250 req/tháng free |
| Anthropic | ~$0.50/tháng | Prompt caching giảm ~90% cost |
| GitHub Actions | $0 | Public repo free |
| **Tổng** | **~$0.50/tháng** | |

## 🗺️ Roadmap

- [x] Flight search — top 5 chuyến, compact format, Google Flights link
- [x] Shopping search — giá, rating, shop, link mua
- [x] Xem ngày giờ xuất hành theo lịch can chi — Can Chi, giờ Hoàng Đạo, xung hợp tuổi, opt-in (tham khảo, có disclaimer)
- [x] Xem ngày cho nhóm 2-5 người — loại ngày xung với bất kỳ ai
- [x] Daily price monitor 9AM (GitHub Actions)
- [x] 24/7 bot trên Fly.io (Singapore)
- [x] Prompt caching — tiết kiệm token cost
- [x] Adaptive thinking — extended thinking tự động
- [x] Multi-turn tool loop (max 5 iter)
- [x] Private mode (ALLOWED_USER_ID)
- [x] /reset /uptime commands
- [ ] Affiliate link injection đầy đủ
- [ ] Shopee price scraper
- [ ] Auto-deal alert (notify khi giá rẻ hơn ngưỡng)
- [ ] Multi-user support

## ⚠️ Về tính năng xem ngày giờ tốt

Tính năng này tính Can Chi, giờ Hoàng Đạo và xung hợp tuổi theo lịch can chi truyền thống. Nó được thiết kế để:

- Chỉ chạy khi người dùng chủ động hỏi về ngày tốt. Mặc định bot vẫn tìm vé thẳng, không tự xem ngày.
- Nhận thông tin linh hoạt: chỉ năm sinh cũng chạy được, đủ ngày tháng thì tính thêm Nhật Trụ cho sát hơn, thêm giờ sinh thì ghi nhận đủ Tứ Trụ.
- Luôn kèm một câu nhắc rõ ràng ở cuối mỗi kết quả.

Đây là nội dung tham khảo theo quy ước truyền thống, không phải dự báo có cơ sở khoa học và không thể kiểm chứng như giá vé hay thời tiết. Phần xem ngày cho nhóm là cách dung hòa do mình tự thiết kế (tử vi truyền thống vốn xem cho một người), nên càng đông người thì ngày an toàn càng hiếm. Mình build phần này chủ yếu để thực hành thiết kế tool nhận input linh hoạt và tool routing có điều kiện, đồng thời giữ sự thành thật về giới hạn của chính sản phẩm.

## 📝 License

MIT — free to use, fork, modify.

> *Tara Bot — build public để chia sẻ và học hỏi, không phải product thương mại.*


## Các repo khác của mình

Nếu bạn làm growth marketing hoặc quan tâm đến AI agent cho công việc thực tế:

| Repo | Mô tả |
|------|-------|
| [ai-growth-agents-for-marketers](https://github.com/thaolst/ai-growth-agents-for-marketers) | Prompts và Python agents cho campaign brief, MEU planning, A/B test — build từ campaign fintech thực tế |
| [growth-mcp](https://github.com/thaolst/growth-mcp) | MCP server cho growth marketing, có CSV data layer phân tích A/B test và retention từ data thật — `pip install growth-mcp` |
| [ai-growth-prompts](https://github.com/thaolst/ai-growth-prompts) | Prompt collection cho voucher design, segmentation, game mechanics |

---

## Other repos

If you work in growth marketing or are interested in AI agents for real work:

| Repo | Description |
|------|-------------|
| [ai-growth-agents-for-marketers](https://github.com/thaolst/ai-growth-agents-for-marketers) | Prompts and Python agents for campaign brief, MEU planning, A/B test — built from real fintech campaigns |
| [growth-mcp](https://github.com/thaolst/growth-mcp) | MCP server for growth marketing with a CSV data layer for A/B test and retention analysis on real data — `pip install growth-mcp` |
| [ai-growth-prompts](https://github.com/thaolst/ai-growth-prompts) | Prompt collection for voucher design, segmentation, game mechanics |

