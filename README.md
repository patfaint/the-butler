# 🎩 The Butler

A professional Discord bot for **The Drain Server** — a polished, sassy butler who keeps order, tracks tributes, manages Domme profiles, and adds a touch of class to an 18+ findom/femdom community.

Built with `discord.py` (slash commands), `SQLAlchemy` async, and designed to be hosted on **AWS**.

---

## ✨ Features (Phase 1)

| Feature | Status |
|---|---|
| `/help` — paginated pink help menu | ✅ Live |
| Permissions system (`is_domme`, `is_sub`, `is_admin`, `is_domme_or_admin`, `is_verified`, `cooldown`) | ✅ Live |
| Welcome embed on member join | ✅ Live |
| Admin `/set*` commands (roles & channels) | ✅ Live |
| Full database schema (GuildConfig, DommeProfile, SubProfile, Tribute, JailRecord, VIPRole, TributeStreak) | ✅ Live |
| Stub commands for Phase 2 (coffee, throne, tribute, jail, trivia, reactions, VIP, verification) | ✅ Ready |

---

## 🛠 Tech Stack

- **Python 3.11+**
- **discord.py ≥ 2.3** — slash commands via `app_commands`
- **SQLAlchemy ≥ 2.0** (async) + **aiosqlite**
- **APScheduler** — for timed events (AWS EventBridge compatible)
- **Tenor API** — for GIF reactions
- **AWS** — environment variables for all secrets, no hardcoded values

---

## 🚀 Getting Started

### 1. Create the Discord Application

1. Go to [discord.com/developers/applications](https://discord.com/developers/applications) and click **New Application**.
2. Name it **The Butler** and save.
3. Go to **Bot** → click **Add Bot**.
4. Under **Privileged Gateway Intents**, enable:
   - **Server Members Intent**
   - **Message Content Intent**
5. Copy the **Bot Token** — you'll need it shortly.

### 2. Invite the Bot to Your Server

In the **OAuth2 → URL Generator** section:
- Scopes: `bot`, `applications.commands`
- Bot Permissions: `Administrator` (or at minimum: Manage Roles, Send Messages, Embed Links, Read Message History)

Open the generated URL in your browser and select your server.

### 3. Get Your Guild (Server) ID

In Discord:
- Enable **Developer Mode** (User Settings → Advanced → Developer Mode)
- Right-click your server icon → **Copy Server ID**

### 4. Configure Environment Variables

```bash
cp .env.example .env
```

Fill in `.env`:

```env
DISCORD_TOKEN=your_bot_token_here
GUILD_ID=your_server_id_here
TENOR_API_KEY=your_tenor_api_key_here   # optional for Phase 1
DATABASE_URL=sqlite+aiosqlite:///./butler.db
```

### 5. Install Dependencies

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 6. Run the Bot

```bash
python bot.py
```

On first run, the bot will:
- Create the SQLite database (`butler.db`) with all tables
- Load all cogs
- Sync slash commands to your guild (available within seconds)
- Set its status to *"At your service. 🎩"*

---

## ☁️ Deploying on AWS

### Option A — EC2 (recommended for always-on)

1. Launch an **EC2 t3.micro** instance (Amazon Linux 2 or Ubuntu 22.04).
2. Install Python 3.11: `sudo dnf install python3.11` (or `apt install python3.11`)
3. Clone this repo and follow steps 4–6 above.
4. Set environment variables via **AWS Systems Manager Parameter Store** or a `.env` file (never commit secrets).
5. Run as a systemd service:

```ini
# /etc/systemd/system/butler.service
[Unit]
Description=The Butler Discord Bot
After=network.target

[Service]
User=ec2-user
WorkingDirectory=/home/ec2-user/the-butler
ExecStart=/home/ec2-user/the-butler/venv/bin/python bot.py
EnvironmentFile=/home/ec2-user/the-butler/.env
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable butler
sudo systemctl start butler
```

### Option B — AWS Lambda + EventBridge (for scheduled tasks only)

Scheduled commands (coffee reminders, VIP expiry checks) can be extracted into Lambda functions triggered by EventBridge rules. The main bot process still needs to run on EC2 or ECS.

### Environment Variables on AWS

Store secrets in **AWS Secrets Manager** or **SSM Parameter Store** and inject them as environment variables in your EC2 user data, ECS task definition, or Lambda configuration. Never hardcode tokens in source code.

---

## 📋 Bot Commands (Phase 1)

### 👑 Domme Commands
| Command | Description |
|---|---|
| `/setup` | Configure your Butler profile *(stub — Phase 2)* |
| `/coffee` | Alert all subs you're seeking coffee *(stub — Phase 2)* |
| `/throne` | Register or display your Throne wishlist link *(stub — Phase 2)* |
| `/confirm @sub $amount` | Confirm a sub's tribute *(stub — Phase 2)* |
| `/jail @user <duration>` | Send someone to jail *(stub — Phase 2)* |
| `/release @user` | Release someone from jail early *(stub — Phase 2)* |

### 🐾 Sub Commands
| Command | Description |
|---|---|
| `/tribute @domme $amount` | Log a tribute to a domme *(stub — Phase 2)* |
| `/wishlist @domme` | View a domme's Throne wishlist link *(stub — Phase 2)* |
| `/leaderboard` | View the server tribute leaderboard *(stub — Phase 2)* |
| `/stats` | View your personal tribute stats *(stub — Phase 2)* |

### 🎭 Fun Commands
| Command | Description |
|---|---|
| `/trivia` | Start a trivia game *(stub — Phase 2)* |
| `/meme` | Get a random meme GIF *(stub — Phase 2)* |

### 🔧 Admin Commands
| Command | Description |
|---|---|
| `/setwelcomechannel #channel` | Set the welcome channel |
| `/setleaderboardchannel #channel` | Set the leaderboard channel |
| `/setdommerole @role` | Set the Domme role |
| `/setsubrole @role` | Set the Sub role |
| `/setjailrole @role` | Set the jail role |
| `/setverificationchannel #channel` | Set the verification channel *(stub — Phase 2)* |

### ℹ️ General
| Command | Description |
|---|---|
| `/help` | Browse all commands with a paginated pink embed |

---

## 🗄 Database Schema

All tables are created automatically on startup.

| Table | Purpose |
|---|---|
| `guild_config` | Per-server settings (role IDs, channel IDs) |
| `domme_profiles` | Domme display name, Throne link, coffee scaling prefs |
| `sub_profiles` | Sub verification status, puppy flag |
| `tributes` | Every tribute logged through the bot |
| `jail_records` | Active and historical jail sentences |
| `vip_roles` | Time-limited VIP role assignments |
| `tribute_streaks` | Consecutive-day tribute streaks per sub/domme pair |

---

## 🎩 Butler Tone

All bot messages are formal, polished, and slightly sassy:

> *"As you wish, Mistress. 🎩"*
> *"Your tribute has been recorded with the utmost discretion."*
> *"I'm afraid that command is reserved for the Dommes, darling. 🎩"*
> *"The Butler is always watching. 🎩"*

---

## 📁 Project Structure

```
the-butler/
├── bot.py                  # Entry point
├── config.py               # Env var loader
├── requirements.txt
├── .env.example
├── README.md
├── cogs/
│   ├── help.py             # /help paginated menu
│   ├── permissions.py      # Permission checks & rate limiting
│   ├── setup.py            # Domme onboarding wizard (Phase 2)
│   ├── throne.py           # Throne link registry (Phase 2)
│   ├── coffee.py           # Coffee alert system (Phase 2)
│   ├── tribute.py          # Tribute logging + leaderboard (Phase 2)
│   ├── verification.py     # New member verification (Phase 2)
│   ├── welcome.py          # Welcome embed on member join
│   ├── reactions.py        # Passive keyword/emoji GIF reactions (Phase 2)
│   ├── trivia.py           # Trivia game + meme GIFs (Phase 2)
│   ├── jail.py             # Jail system (Phase 2)
│   ├── vip.py              # Expiring VIP roles (Phase 2)
│   └── moderation.py       # Admin /set* commands
├── database/
│   ├── models.py           # SQLAlchemy ORM models
│   └── db.py               # Async engine + session factory
└── utils/
    ├── embeds.py           # Reusable pink embed builders
    └── algorithms.py       # Coffee price algorithm
```
