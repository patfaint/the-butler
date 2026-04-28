# 🎩 The Butler

A professional Discord bot for **The Drain Server** — a polished, sassy butler who keeps order, tracks tributes, manages Domme profiles, and adds a touch of class to an 18+ findom/femdom community.

Built with `discord.py` (slash commands), `SQLAlchemy` async, and designed to be hosted on **AWS**.

---

## ✨ Features (MVP — Fully Live)

| Feature | Status |
|---|---|
| `/help` — 5-page paginated pink help menu | ✅ Live |
| Permissions system (`is_domme`, `is_sub`, `is_admin`, `is_domme_or_admin`, `is_verified`, `cooldown`) | ✅ Live |
| Welcome embed on member join | ✅ Live |
| Admin `/set*` commands (roles, channels, VIP role) | ✅ Live |
| Full database schema (GuildConfig, DommeProfile, SubProfile, Tribute, JailRecord, VIPRole, TributeStreak) | ✅ Live |
| `/setup` — Domme onboarding modal (display name, Throne link, coffee amount, dynamic pricing) | ✅ Live |
| `/myprofile` — View your Domme profile | ✅ Live |
| `/throne <link>` — Register/update Throne wishlist link | ✅ Live |
| `/wishlist @domme` — View a Domme's Throne link | ✅ Live |
| `/coffee` — Dynamic coffee alert DMs all verified subs + posts to announcement channel | ✅ Live |
| `/tribute @domme $amount` — Sub submits a tribute (pending confirmation) | ✅ Live |
| `/confirm @sub $amount` — Domme confirms a tribute + streak tracking | ✅ Live |
| `/leaderboard` — Top 10 sub leaderboard by total confirmed tributes | ✅ Live |
| `/stats` — Personal tribute stats (given, received, count, longest streak) | ✅ Live |
| `/jail @user <duration> [reason]` — Jail system: assigns role, strips & saves other roles | ✅ Live |
| `/release @user` — Early release with role restoration | ✅ Live |
| Auto-release — APScheduler loop releases jailed members when sentence expires | ✅ Live |
| `/givevip @member <duration>` — Time-limited VIP role assignment | ✅ Live |
| VIP expiry checker — APScheduler removes expired VIP roles automatically | ✅ Live |
| `/trivia` — Button-based trivia game with 30-second timer (10 questions) | ✅ Live |
| `/meme` — Random meme GIF via Tenor API | ✅ Live |
| Keyword GIF reactions — Passive Tenor GIF responses to server keywords | ✅ Live |
| `/sendverification` — Posts verification rules embed with button to verification channel | ✅ Live |
| Verification button — Members click to verify; sub role assigned automatically | ✅ Live |

---

## 🛠 Tech Stack

- **Python 3.11+**
- **discord.py ≥ 2.3** — slash commands via `app_commands`, modals, persistent views
- **SQLAlchemy ≥ 2.0** (async) + **aiosqlite**
- **discord.ext.tasks** — for timed events (jail auto-release, VIP expiry)
- **httpx** — async HTTP client for Tenor API
- **Tenor API** — for GIF reactions and memes
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
TENOR_API_KEY=your_tenor_api_key_here   # required for GIF reactions & memes
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

### 7. Initial Server Setup (Admin)

Run these commands in order after the bot is online:

1. `/setdommerole @YourDommeRole`
2. `/setsubrole @YourSubRole`
3. `/setjailrole @YourJailRole`
4. `/setadminrole @YourAdminRole`
5. `/setviprole @YourVIPRole`
6. `/setwelcomechannel #welcome`
7. `/setleaderboardchannel #tributes`
8. `/setannouncementchannel #announcements`
9. `/setverificationchannel #verify`
10. `/sendverification` — posts the verification embed with button

Dommes then run `/setup` to configure their profiles.

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

### Environment Variables on AWS

Store secrets in **AWS Secrets Manager** or **SSM Parameter Store** and inject them as environment variables in your EC2 user data, ECS task definition, or Lambda configuration. Never hardcode tokens in source code.

---

## 📋 Bot Commands (Full MVP)

### 👑 Domme Commands
| Command | Description |
|---|---|
| `/setup` | Configure your Butler profile via modal (name, Throne link, coffee amount & scaling) |
| `/myprofile` | View your current Butler profile |
| `/throne <link>` | Register or update your Throne wishlist link |
| `/coffee` | Alert all verified subs with a dynamic coffee request |
| `/confirm @sub $amount` | Confirm a sub's tribute |
| `/jail @user <duration> [reason]` | Send someone to jail (e.g. `1h`, `30m`, `2d`, `1h30m`) |
| `/release @user` | Release someone from jail early |
| `/givevip @member <duration>` | Grant a member a time-limited VIP role |

### 🐾 Sub Commands
| Command | Description |
|---|---|
| `/tribute @domme $amount` | Submit a tribute to a Domme (awaits confirmation) |
| `/wishlist @domme` | View a Domme's Throne wishlist link |
| `/leaderboard` | View the server tribute leaderboard (top 10 by confirmed total) |
| `/stats` | View your personal tribute stats and longest streak |

### 🎭 Fun & Verification
| Command | Description |
|---|---|
| `/trivia` | Start a button-based trivia game |
| `/meme` | Get a random meme GIF via Tenor |
| Keyword reactions | The Butler automatically posts GIFs for phrases like "good boy", "yes mistress", "tribute", etc. |

### 🔧 Admin Commands
| Command | Description |
|---|---|
| `/setwelcomechannel #channel` | Set the welcome channel |
| `/setleaderboardchannel #channel` | Set the leaderboard/tribute confirmation channel |
| `/setannouncementchannel #channel` | Set the announcement channel for coffee alerts |
| `/setverificationchannel #channel` | Set the verification channel |
| `/setdommerole @role` | Set the Domme role |
| `/setsubrole @role` | Set the Sub role |
| `/setjailrole @role` | Set the jail role |
| `/setadminrole @role` | Set the admin role |
| `/setviprole @role` | Set the VIP role |
| `/sendverification` | Post the verification embed with agree button |

### ℹ️ General
| Command | Description |
|---|---|
| `/help` | Browse all commands with a paginated pink embed (5 pages) |

---

## 🗄 Database Schema

All tables are created automatically on startup.

| Table | Purpose |
|---|---|
| `guild_config` | Per-server settings (role IDs, channel IDs) |
| `domme_profiles` | Domme display name, Throne link, coffee scaling prefs, last coffee timestamp |
| `sub_profiles` | Sub verification status, puppy flag |
| `tributes` | Every tribute logged through the bot |
| `jail_records` | Active and historical jail sentences with saved role lists |
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
│   ├── help.py             # /help paginated menu (5 pages)
│   ├── permissions.py      # Permission checks & rate limiting
│   ├── setup.py            # Domme onboarding modal + /myprofile
│   ├── throne.py           # Throne link registry + /wishlist
│   ├── coffee.py           # Dynamic coffee alert system
│   ├── tribute.py          # Tribute logging + confirm + leaderboard + stats
│   ├── verification.py     # Button-based member verification
│   ├── welcome.py          # Welcome embed on member join
│   ├── reactions.py        # Passive keyword GIF reactions via Tenor
│   ├── trivia.py           # Button trivia game + /meme GIFs
│   ├── jail.py             # Jail system with auto-release
│   ├── vip.py              # Expiring VIP roles with auto-expiry
│   └── moderation.py       # Admin /set* commands
├── database/
│   ├── models.py           # SQLAlchemy ORM models
│   ├── db.py               # Async engine + session factory
│   └── helpers.py          # Shared DB utilities
└── utils/
    ├── embeds.py           # Reusable pink embed builders
    └── algorithms.py       # Coffee price dynamic algorithm
```


---

## 🛠 Tech Stack

- **Python 3.11+**
- **discord.py ≥ 2.3** — slash commands via `app_commands`, modals, persistent views
- **SQLAlchemy ≥ 2.0** (async) + **aiosqlite**
- **discord.ext.tasks** — for timed events (jail auto-release, VIP expiry)
- **httpx** — async HTTP client for Tenor API
- **Tenor API** — for GIF reactions
- **AWS** — environment variables for all secrets, no hardcoded values
