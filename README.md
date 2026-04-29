# 🎩 The Butler

A professional Discord bot for **The Drain Server** — a polished, sassy butler who keeps order, tracks tributes, manages Domme profiles, and adds a touch of class to an 18+ findom/femdom community.

Built with `discord.py` (slash commands), `SQLAlchemy` async, **Python 3.12**, and designed to be hosted on **AWS EC2**.

---

## 🛠 Tech Stack

- **Python 3.12**
- **discord.py ≥ 2.3** — slash commands via `app_commands`
- **SQLAlchemy ≥ 2.0** (async) + **aiosqlite**
- **APScheduler** — for timed events
- **Tenor API** — for GIF reactions
- **AWS EC2** — always-on, systemd-managed service

---

## 📁 Project Structure

```
the-butler/
├── bot.py                  # Entry point — Butler class + main()
├── config.py               # Env var loader
├── requirements.txt
├── .env.example
├── install.sh              # One-time EC2 setup
├── update.sh               # Pull + restart (run by CI deploy)
├── README.md
├── cogs/                   # Slash-command cogs (add here)
│   └── __init__.py
├── database/
│   ├── db.py               # Async engine + session factory
│   ├── helpers.py          # Shared DB helpers (get_or_create_guild_config)
│   └── models.py           # SQLAlchemy ORM models
└── utils/
    ├── embeds.py           # Reusable pink embed builders
    └── algorithms.py       # Coffee price algorithm
```

---

## 🚀 Local Development

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
TENOR_API_KEY=your_tenor_api_key_here   # optional
DATABASE_URL=sqlite+aiosqlite:///./butler.db
```

### 5. Install Dependencies

```bash
python3.12 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 6. Run the Bot

```bash
python bot.py
```

On first run, the bot will:
- Create the SQLite database (`butler.db`) with all tables
- Sync slash commands to your guild (available within seconds)
- Set its status to *"At your service. 🎩"*

---

## ☁️ Deploying on AWS EC2

### First-time installation

1. Launch an **EC2 t3.micro** instance (Amazon Linux 2023 or Ubuntu 22.04).
2. Open port **22** in the Security Group for your IP (or the GitHub Actions IP range if using the deploy workflow).
3. SSH into the instance and run the one-line installer as root:

```bash
curl -fsSL https://raw.githubusercontent.com/patfaint/the-butler/main/install.sh | sudo bash
```

The script will:
- Install Python 3.12 and Git
- Create a dedicated `butler` system user
- Clone the repo to `/home/butler/the-butler`
- Create a Python virtual environment and install dependencies
- Prompt for your `.env` values (`DISCORD_TOKEN`, `GUILD_ID`, etc.)
- Register and start a **systemd service** (`the-butler`) that restarts automatically on failure

### Manual updates

To pull the latest code and restart the service at any time:

```bash
sudo bash /home/butler/the-butler/update.sh
```

### Automated deploys via GitHub Actions

Every push to `main` automatically deploys to your EC2 instance using the workflow at `.github/workflows/deploy.yml`.

**Required GitHub Secrets** (Settings → Secrets and variables → Actions → New repository secret):

| Secret | Value |
|---|---|
| `EC2_HOST` | Your EC2 public IP or DNS hostname |
| `EC2_USER` | SSH username (e.g. `ubuntu` or `ec2-user`) |
| `EC2_SSH_KEY` | Contents of your EC2 private key (`~/.ssh/your-key.pem`) |

The workflow SSHes into the instance and runs `update.sh`, which:
1. `git fetch` + `git reset --hard origin/main` (clean pull)
2. Upgrades Python dependencies
3. Restarts the `the-butler` systemd service
4. Verifies the service came back up

> **Tip:** The SSH user (`EC2_USER`) must have passwordless `sudo` access. On Amazon Linux / Ubuntu the default `ec2-user` / `ubuntu` accounts have this by default.

### Useful commands

```bash
sudo systemctl status the-butler     # service health
sudo journalctl -u the-butler -f     # live logs
sudo systemctl restart the-butler    # manual restart
sudo bash /home/butler/the-butler/update.sh  # pull + restart
```

---

## 🗄 Database Schema

All tables are created automatically on startup via `database/models.py`.

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
