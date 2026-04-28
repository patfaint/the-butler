"""Moderation cog — admin /set* commands."""

from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from cogs.permissions import handle_check_failure, is_admin
from database.db import AsyncSessionLocal
from database.helpers import get_or_create_guild_config
from utils.embeds import success_embed

class ModerationCog(commands.Cog, name="Moderation"):
    """Admin configuration commands."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    async def cog_app_command_error(
        self,
        interaction: discord.Interaction,
        error: app_commands.AppCommandError,
    ) -> None:
        await handle_check_failure(interaction, error)

    # ── Channel setters ───────────────────────────────────────────────────────

    @app_commands.command(
        name="setwelcomechannel",
        description="Set the welcome channel. (Admin only)",
    )
    @is_admin()
    async def set_welcome_channel(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
    ) -> None:
        if interaction.guild is None:
            await interaction.response.send_message(
                "This command can only be used in a server.", ephemeral=True
            )
            return
        async with AsyncSessionLocal() as session:
            config = await get_or_create_guild_config(session, interaction.guild.id)
            config.welcome_channel_id = channel.id
            await session.commit()
        await interaction.response.send_message(
            embed=success_embed(f"Welcome channel set to {channel.mention}. 🎩"),
            ephemeral=True,
        )

    @app_commands.command(
        name="setleaderboardchannel",
        description="Set the leaderboard channel. (Admin only)",
    )
    @is_admin()
    async def set_leaderboard_channel(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
    ) -> None:
        if interaction.guild is None:
            await interaction.response.send_message(
                "This command can only be used in a server.", ephemeral=True
            )
            return
        async with AsyncSessionLocal() as session:
            config = await get_or_create_guild_config(session, interaction.guild.id)
            config.leaderboard_channel_id = channel.id
            await session.commit()
        await interaction.response.send_message(
            embed=success_embed(f"Leaderboard channel set to {channel.mention}. 🎩"),
            ephemeral=True,
        )

    @app_commands.command(
        name="setannouncementchannel",
        description="Set the announcement channel used for coffee alerts. (Admin only)",
    )
    @is_admin()
    async def set_announcement_channel(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
    ) -> None:
        if interaction.guild is None:
            await interaction.response.send_message(
                "This command can only be used in a server.", ephemeral=True
            )
            return
        async with AsyncSessionLocal() as session:
            config = await get_or_create_guild_config(session, interaction.guild.id)
            config.announcement_channel_id = channel.id
            await session.commit()
        await interaction.response.send_message(
            embed=success_embed(f"Announcement channel set to {channel.mention}. 🎩"),
            ephemeral=True,
        )

    # ── Role setters ──────────────────────────────────────────────────────────

    @app_commands.command(
        name="setdommerole",
        description="Set the Domme role. (Admin only)",
    )
    @is_admin()
    async def set_domme_role(
        self,
        interaction: discord.Interaction,
        role: discord.Role,
    ) -> None:
        if interaction.guild is None:
            await interaction.response.send_message(
                "This command can only be used in a server.", ephemeral=True
            )
            return
        async with AsyncSessionLocal() as session:
            config = await get_or_create_guild_config(session, interaction.guild.id)
            config.domme_role_id = role.id
            await session.commit()
        await interaction.response.send_message(
            embed=success_embed(f"Domme role set to {role.mention}. 🎩"),
            ephemeral=True,
        )

    @app_commands.command(
        name="setsubrole",
        description="Set the Sub role. (Admin only)",
    )
    @is_admin()
    async def set_sub_role(
        self,
        interaction: discord.Interaction,
        role: discord.Role,
    ) -> None:
        if interaction.guild is None:
            await interaction.response.send_message(
                "This command can only be used in a server.", ephemeral=True
            )
            return
        async with AsyncSessionLocal() as session:
            config = await get_or_create_guild_config(session, interaction.guild.id)
            config.sub_role_id = role.id
            await session.commit()
        await interaction.response.send_message(
            embed=success_embed(f"Sub role set to {role.mention}. 🎩"),
            ephemeral=True,
        )

    @app_commands.command(
        name="setjailrole",
        description="Set the jail role. (Admin only)",
    )
    @is_admin()
    async def set_jail_role(
        self,
        interaction: discord.Interaction,
        role: discord.Role,
    ) -> None:
        if interaction.guild is None:
            await interaction.response.send_message(
                "This command can only be used in a server.", ephemeral=True
            )
            return
        async with AsyncSessionLocal() as session:
            config = await get_or_create_guild_config(session, interaction.guild.id)
            config.jail_role_id = role.id
            await session.commit()
        await interaction.response.send_message(
            embed=success_embed(f"Jail role set to {role.mention}. 🎩"),
            ephemeral=True,
        )

    @app_commands.command(
        name="setadminrole",
        description="Set the admin role. (Admin only)",
    )
    @is_admin()
    async def set_admin_role(
        self,
        interaction: discord.Interaction,
        role: discord.Role,
    ) -> None:
        if interaction.guild is None:
            await interaction.response.send_message(
                "This command can only be used in a server.", ephemeral=True
            )
            return
        async with AsyncSessionLocal() as session:
            config = await get_or_create_guild_config(session, interaction.guild.id)
            config.admin_role_id = role.id
            await session.commit()
        await interaction.response.send_message(
            embed=success_embed(f"Admin role set to {role.mention}. 🎩"),
            ephemeral=True,
        )

    @app_commands.command(
        name="setviprole",
        description="Set the VIP role used for time-limited grants. (Admin only)",
    )
    @is_admin()
    async def set_vip_role(
        self,
        interaction: discord.Interaction,
        role: discord.Role,
    ) -> None:
        if interaction.guild is None:
            await interaction.response.send_message(
                "This command can only be used in a server.", ephemeral=True
            )
            return
        async with AsyncSessionLocal() as session:
            config = await get_or_create_guild_config(session, interaction.guild.id)
            config.vip_role_id = role.id
            await session.commit()
        await interaction.response.send_message(
            embed=success_embed(f"VIP role set to {role.mention}. 🎩"),
            ephemeral=True,
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ModerationCog(bot))

