# TG Tasker Bot 🚀

[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Bot Status](https://img.shields.io/badge/status-live-brightgreen)](#)
[![Made with ❤️ by gptonline.ai](https://img.shields.io/badge/Made%20by-gptonline.ai-red)](https://gptonline.ai)

A powerful and customizable **Telegram bot** for managing task-based earning systems — ideal for crypto projects, airdrops, traffic exchanges, or SMM growth.
...

https://ibb.co/pv9YMnZM
https://ibb.co/9H30WvG8
https://ibb.co/TqhQYRPw
# TG Tasker Bot 🚀

A powerful and customizable **Telegram bot** for managing task-based earning systems — ideal for crypto projects, airdrops, traffic exchanges, or SMM growth.  
Users earn **SD tokens** for completing tasks (e.g., subscribing to channels, commenting, liking), and admins can manage everything from a user-friendly panel.

## 🔥 Features

### ✅ User Functionality
- **Task feed** with real-time updates (sorted by newest)
- Task types include:
  - **Telegram**: join channels, subscribe to bots
  - **YouTube**: subscribe, like, comment
  - **Instagram**: follow, like, comment
- Automatic **token accrual** after task completion
- **Anti-fraud logic**:
  - Tokens revoked if user unsubscribes within 24h
  - Telegram admin check to validate channel joins
- **Balance and withdrawal** system (min. threshold logic)
- **Daily broadcast messages** (3× per day or manually via admin panel)
- **Referral system** (optional)
- Supports SD token display and history

### 🛠 Admin Functionality
- Add new tasks via bot interface
  - Select platform: Telegram / YouTube / Instagram
  - Set price per task and amount
  - For Telegram: auto-checks if bot is added as admin
  - Min. task cost: 100 SD enforced
- Auto-labeling by category (e.g. `YouTube: Subscribe + Comment +0.5 SD`)
- View and manage tasks
- View pending withdrawals
- Mass payout tracking (manual/automated)
- Broadcast system with editable text/image/buttons

### ⚙️ System Logic
- Customizable minimum withdrawal amount (default 100 SD)
- Automatic reward logic via internal balance tracking
- Error handling, logs, and secure task processing
- Optimized to run on small VPS

---

## 💡 Example Daily Broadcast

```
✅ Каждый день активные игроки выводят свои USDT.

Задания появляются, исчезают, обновляются. Зайди сейчас — возможно, там уже что-то новое.

Не упускай шанс заработать.
```

With image and **“🚀 Start game”** button.

---

## 🧪 Stack & Technologies

- Python + Aiogram
- SQLite / PostgreSQL
- Hosted on Railway / Render / VPS
- Uses Telegram Bot API

---

## 📦 Setup

1. Clone repo  
2. Edit config.py file (sample below)
3. Run bot with `python bot.py` or use a process manager like `pm2` / `systemd`

```env
BOT_TOKEN=your_telegram_bot_token
ADMIN_IDS=123456789
MIN_WITHDRAW=100
USDT_WALLET=your_wallet_address
```
---

## 📜 License

MIT — free to use, modify and contribute.

---
