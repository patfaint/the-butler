# The Butler

The Butler is a production-ready Discord bot for The Drain Server. It handles welcomes, 18+ age verification, staff approval, role assignment, SQLite persistence, and a polished restricted help menu.

## Features

- Welcome embed when a member joins
- Unverified role assignment on join
- Persistent age verification panel
- DM-based verification flow with approved links or image submissions
- Domme/Submissive role selection during verification
- Staff approval and denial buttons
- SQLite persistence at `data/the_butler.sqlite3`
- Public plain-text welcome after approval
- Restricted `/help` command with paginated embeds
- Production `install.sh` bootstrap script
- Hardened `the-butler.service` systemd unit
- GitHub Actions deployment workflow

## Project Structure

```text
.
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
├── install.sh
├── main.py
├── the-butler.service
├── bot/
│   ├── __init__.py
│   ├── config.py
│   ├── database.py
│   ├── embeds.py
│   ├── messages.py
│   ├── views.py
│   ├── verification.py
│   └── utils.py
├── data/
│   └── .gitkeep
└── .github/
    └── workflows/
        └── deploy.yml
```

## Discord Developer Portal Setup

1. Create an application in the Discord Developer Portal.
2. Add a bot to the application.
3. Copy the bot token and store it only in your local `.env` or on the server.
4. Enable these privileged gateway intents:
   - `MESSAGE CONTENT`
   - `MEMBERS`
5. Invite the bot with these permissions:
   - Send Messages
   - Embed Links
   - Attach Files
   - Read Message History
   - Use Slash Commands
   - Manage Roles
   - View Channels

The bot role must be above the Unverified, Verified, Domme, and Submissive roles in Discord role order.

## Server Setup

Create these channels and roles before starting the bot:

Channels:

- Welcome channel
- Verification channel
- Verification log channel
- General channel
- Roles channel
- Introductions channel

Roles:

- Unverified
- Verified
- Domme
- Submissive
- Moderation

Copy each channel and role ID into `.env`.

## Local Setup

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env`, then run:

```bash
python main.py
```

`GUILD_ID` is optional but recommended while testing because it syncs slash commands to one server immediately.

## Environment Variables

```env
DISCORD_TOKEN=
GUILD_ID=
WELCOME_CHANNEL_ID=
VERIFICATION_CHANNEL_ID=
VERIFY_LOG_CHANNEL_ID=
GENERAL_CHANNEL_ID=
ROLES_CHANNEL_ID=
INTRODUCTIONS_CHANNEL_ID=
UNVERIFIED_ROLE_ID=
VERIFIED_ROLE_ID=
DOMME_ROLE_ID=
SUBMISSIVE_ROLE_ID=
MODERATION_ROLE_ID=
DATABASE_PATH=data/the_butler.sqlite3
```

Never commit `.env`. The token belongs only on your machine or server.

## Slash Commands

- `/setup-verification` posts the verification panel in the configured verification channel.
- `/verify-status` checks a user's verification status.
- `/verify-cleanup` shows users who still have the Unverified role.
- `/help` shows the restricted bot help menu.

`/help` only works for these Discord user IDs:

- `1493691258873319454`
- `1299308718009356289`

## Production Install

Run the installer on a fresh Linux server:

```bash
sudo bash install.sh
```

Run it from the deploy user's shell with `sudo`, not from a direct root login. The installer makes that non-root user the owner of the checked-out app so GitHub Actions can update it later.

The installer:

- Installs `git`, `python3`, `python3-venv`, `pip`, and Python 3.11
- Creates the `butlerbot` runtime user
- Creates `/opt/the-butler/app`, `/opt/the-butler/data`, and `/opt/the-butler/logs`
- Clones this repository
- Creates a virtual environment
- Installs dependencies
- Prompts for the Discord token, channel IDs, and role IDs with numeric ID validation
- Writes `/opt/the-butler/app/.env`
- Sets `chmod 600` on `.env`
- Stores the production SQLite database at `/opt/the-butler/data/the_butler.sqlite3`
- Installs and starts `the-butler.service`

Useful commands after install:

```bash
sudo systemctl status the-butler
sudo journalctl -u the-butler -f
sudo systemctl restart the-butler
```

## Systemd Security

The bot runs as `butlerbot`, not root. The service uses privilege restrictions and allows writes only to:

- `/opt/the-butler/app`
- `/opt/the-butler/data`
- `/opt/the-butler/logs`

Keep the runtime user separate from the deploy user. The deploy user should SSH into the server, update `/opt/the-butler/app`, install dependencies, and restart the service through `sudo`.

## GitHub Actions Deploy

The workflow in `.github/workflows/deploy.yml` deploys on pushes to `main`.

Add these GitHub repository secrets:

- `DEPLOY_HOST`: server hostname or IP
- `DEPLOY_USER`: SSH deploy user, not `butlerbot`
- `DEPLOY_SSH_KEY`: private SSH key for the deploy user
- `DEPLOY_PORT`: SSH port, usually `22`
- `DEPLOY_KNOWN_HOSTS`: pinned SSH known_hosts entry for the server

The workflow stops the service, pulls the latest code, updates dependencies, refreshes the systemd unit, reloads systemd, and starts the service again. It does not store or send the Discord token. The token stays in `/opt/the-butler/app/.env` on the server.

Create `DEPLOY_KNOWN_HOSTS` from a trusted machine and verify the fingerprint before saving it:

```bash
ssh-keyscan -p 22 your-server.example.com
```

The deploy user needs permission to run:

```bash
sudo systemctl restart the-butler
```

## Troubleshooting

Slash commands are missing:

- Confirm the bot is online.
- Set `GUILD_ID` for immediate guild command syncing.
- Reinvite the bot with `applications.commands`.

The bot cannot assign roles:

- Move the bot role above every role it manages.
- Confirm `Manage Roles` is enabled.
- Check the configured role IDs.

Users cannot start verification:

- Ask them to enable DMs from server members.
- Confirm `MESSAGE CONTENT` and `MEMBERS` intents are enabled.

Staff buttons do not work after restart:

- Confirm pending requests exist in `data/the_butler.sqlite3`.
- Check the service logs for startup or database errors.

Check logs:

```bash
sudo journalctl -u the-butler -f
```
