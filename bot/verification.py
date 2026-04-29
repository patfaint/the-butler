from __future__ import annotations

import asyncio
import logging
import random
import sqlite3
import time

import discord
from discord import app_commands
from discord.ext import commands

from bot import embeds, messages
from bot.config import BotConfig
from bot.database import Database, VerificationRequest
from bot.utils import (
    VerificationSubmission,
    display_username,
    extract_verification_submission,
    has_moderation_permissions,
    mention_role,
    resolve_message_channel,
    safe_dm,
    user_mention,
)
from bot.views import FormLinkView, HelpView, RoleSelectionView, StaffReviewView, VerificationPanelView

log = logging.getLogger(__name__)


class VerificationService:
    def __init__(
        self,
        bot: commands.Bot,
        config: BotConfig,
        database: Database,
    ) -> None:
        self.bot = bot
        self.config = config
        self.database = database
        self.active_sessions: set[tuple[int, int]] = set()

    async def restore_persistent_views(self) -> None:
        self.bot.add_view(VerificationPanelView(self))
        pending_requests = await self.database.get_pending_log_requests()
        for request in pending_requests:
            link_url = request.verification_value if request.verification_type == "Link" else None
            self.bot.add_view(StaffReviewView(self, request.id, link_url=link_url))
        log.info("Restored %s pending verification view(s).", len(pending_requests))

    async def handle_member_join(self, member: discord.Member) -> None:
        if member.bot:
            return

        unverified_role = member.guild.get_role(self.config.unverified_role_id)
        if unverified_role:
            try:
                await member.add_roles(unverified_role, reason="The Butler welcome verification")
            except discord.Forbidden:
                log.warning("Missing permission to assign Unverified role to %s.", member.id)
            except discord.HTTPException:
                log.exception("Failed to assign Unverified role to %s.", member.id)
        else:
            log.warning("Configured Unverified role was not found.")

        channel = await resolve_message_channel(self.bot, member.guild, self.config.welcome_channel_id)
        if channel is None:
            return

        try:
            await channel.send(embed=embeds.welcome_embed(member))
        except discord.HTTPException:
            log.exception("Failed to send welcome embed for %s.", member.id)

    async def start_verification(self, interaction: discord.Interaction) -> None:
        if interaction.guild is None or not isinstance(interaction.user, discord.Member):
            await self._send_interaction_message(
                interaction,
                "Verification can only be started from the server.",
                ephemeral=True,
            )
            return

        key = (interaction.guild.id, interaction.user.id)
        pending_request = await self.database.get_pending_request(
            user_id=interaction.user.id,
            guild_id=interaction.guild.id,
        )
        if pending_request:
            await self._send_interaction_message(
                interaction,
                messages.DUPLICATE_PENDING_RESPONSE,
                ephemeral=True,
            )
            return

        if key in self.active_sessions:
            await self._send_interaction_message(
                interaction,
                "You already have a verification session in progress. Please check your DMs.",
                ephemeral=True,
            )
            return

        try:
            await interaction.user.send(embed=embeds.initial_verification_dm_embed())
        except (discord.Forbidden, discord.HTTPException):
            await self._send_interaction_message(
                interaction,
                messages.DM_FAILURE_RESPONSE,
                ephemeral=True,
            )
            return

        self.active_sessions.add(key)
        await self._send_interaction_message(
            interaction,
            "I've sent you a DM with verification instructions.",
            ephemeral=True,
        )
        asyncio.create_task(self._run_dm_flow(interaction.user, interaction.guild, key))

    async def setup_verification_panel(self, interaction: discord.Interaction) -> None:
        if interaction.guild is None or not isinstance(interaction.user, discord.Member):
            await self._send_interaction_message(
                interaction,
                "This command can only be used in a server.",
                ephemeral=True,
            )
            return

        if not has_moderation_permissions(interaction.user, self.config):
            await self._send_interaction_message(
                interaction,
                messages.UNAUTHORISED_HELP_RESPONSE,
                ephemeral=True,
            )
            return

        channel = await resolve_message_channel(
            self.bot,
            interaction.guild,
            self.config.verification_channel_id,
        )
        if channel is None:
            await self._send_interaction_message(
                interaction,
                "I couldn't find the configured verification channel.",
                ephemeral=True,
            )
            return

        try:
            await channel.send(
                embed=embeds.verification_panel_embed(),
                view=VerificationPanelView(self),
            )
        except discord.HTTPException:
            log.exception("Failed to post verification panel.")
            await self._send_interaction_message(
                interaction,
                "I couldn't post the verification panel. Please check my channel permissions.",
                ephemeral=True,
            )
            return

        await self._send_interaction_message(
            interaction,
            f"Verification panel posted in {channel.mention}.",
            ephemeral=True,
        )

    async def verify_status(
        self,
        interaction: discord.Interaction,
        user: discord.User | discord.Member,
    ) -> None:
        if interaction.guild is None or not isinstance(interaction.user, discord.Member):
            await self._send_interaction_message(
                interaction,
                "This command can only be used in a server.",
                ephemeral=True,
            )
            return

        if not has_moderation_permissions(interaction.user, self.config):
            await self._send_interaction_message(
                interaction,
                messages.UNAUTHORISED_HELP_RESPONSE,
                ephemeral=True,
            )
            return

        request = await self.database.get_latest_request(
            user_id=user.id,
            guild_id=interaction.guild.id,
        )
        await self._send_interaction_message(
            interaction,
            embed=embeds.verification_status_embed(request, user),
            ephemeral=True,
        )

    async def verify_cleanup(self, interaction: discord.Interaction) -> None:
        if interaction.guild is None or not isinstance(interaction.user, discord.Member):
            await self._send_interaction_message(
                interaction,
                "This command can only be used in a server.",
                ephemeral=True,
            )
            return

        if not has_moderation_permissions(interaction.user, self.config):
            await self._send_interaction_message(
                interaction,
                messages.UNAUTHORISED_HELP_RESPONSE,
                ephemeral=True,
            )
            return

        role = interaction.guild.get_role(self.config.unverified_role_id)
        if role is None:
            await self._send_interaction_message(
                interaction,
                "I couldn't find the configured Unverified role.",
                ephemeral=True,
            )
            return

        members = sorted(
            [member for member in role.members if not member.bot],
            key=lambda member: member.display_name.lower(),
        )
        await self._send_interaction_message(
            interaction,
            embed=embeds.verification_cleanup_embed(role=role, members=members),
            ephemeral=True,
        )

    async def review_request(
        self,
        interaction: discord.Interaction,
        request_id: int,
        action: str,
    ) -> None:
        if interaction.guild is None or not isinstance(interaction.user, discord.Member):
            await self._send_interaction_message(
                interaction,
                messages.UNAUTHORISED_STAFF_BUTTON_RESPONSE,
                ephemeral=True,
            )
            return

        if not has_moderation_permissions(interaction.user, self.config):
            await self._send_interaction_message(
                interaction,
                messages.UNAUTHORISED_STAFF_BUTTON_RESPONSE,
                ephemeral=True,
            )
            return

        await interaction.response.defer(ephemeral=True)

        request = await self.database.get_request(request_id)
        if request is None or request.status != "pending":
            await interaction.followup.send(
                "This verification request has already been processed.",
                ephemeral=True,
            )
            return

        if action == "approve":
            await self._approve_request(interaction, request)
        elif action == "deny_underage":
            await self._deny_request(
                interaction,
                request,
                status="denied_underage",
                dm_embed=embeds.denied_underage_dm_embed(),
                log_title="Verification Denied - Under 18",
                log_color=embeds.RED,
                log_status="Denied - Under 18",
                followup="Verification denied as under 18.",
            )
        elif action == "deny_invalid":
            await self._deny_request(
                interaction,
                request,
                status="denied_invalid",
                dm_embed=embeds.denied_invalid_dm_embed(),
                log_title="Verification Denied - Invalid Service",
                log_color=embeds.ORANGE,
                log_status="Denied - Invalid Service",
                followup="Verification denied for invalid service.",
            )
        else:
            await interaction.followup.send("Unknown verification action.", ephemeral=True)

    async def _run_dm_flow(
        self,
        member: discord.Member,
        guild: discord.Guild,
        key: tuple[int, int],
    ) -> None:
        try:
            submission = await self._wait_for_submission(member)
            if submission is None:
                await safe_dm(member, embed=embeds.session_expired_dm_embed())
                await self._record_expired(member, guild)
                return

            selected_role = await self._ask_role(member)
            if selected_role is None:
                await safe_dm(member, embed=embeds.session_expired_dm_embed())
                await self._record_expired(member, guild, submission=submission)
                return

            try:
                request_id = await self.database.create_request(
                    user_id=member.id,
                    guild_id=guild.id,
                    username=display_username(member),
                    verification_type=submission.verification_type,
                    verification_value=submission.verification_value,
                    selected_role=selected_role,
                )
            except sqlite3.IntegrityError:
                await safe_dm(member, content=messages.DUPLICATE_PENDING_RESPONSE)
                return

            request = await self.database.get_request(request_id)
            if request is None:
                log.error("Created verification request %s but could not fetch it.", request_id)
                await safe_dm(member, embed=embeds.session_expired_dm_embed())
                return

            submitted = await self._submit_to_staff(guild, member, request)
            if not submitted:
                await self.database.mark_reviewed(
                    request_id=request.id,
                    status="expired",
                    reviewed_by=None,
                )
                await safe_dm(member, embed=embeds.session_expired_dm_embed())
                return

            await safe_dm(
                member,
                embed=embeds.pending_review_embed(),
                view=FormLinkView(),
            )
        finally:
            self.active_sessions.discard(key)

    async def _wait_for_submission(
        self,
        member: discord.Member,
    ) -> VerificationSubmission | None:
        deadline = time.monotonic() + 300

        def check(message: discord.Message) -> bool:
            return message.author.id == member.id and message.guild is None

        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return None

            try:
                message = await self.bot.wait_for("message", check=check, timeout=remaining)
            except asyncio.TimeoutError:
                return None

            submission = extract_verification_submission(message)
            if submission:
                return submission

            await safe_dm(member, embed=embeds.invalid_submission_dm_embed())

    async def _ask_role(self, member: discord.Member) -> str | None:
        view = RoleSelectionView(member.id)
        try:
            view.message = await member.send(embed=embeds.role_prompt_embed(), view=view)
        except (discord.Forbidden, discord.HTTPException):
            return None

        timed_out = await view.wait()
        if timed_out:
            return None
        return view.selection

    async def _submit_to_staff(
        self,
        guild: discord.Guild,
        member: discord.Member,
        request: VerificationRequest,
    ) -> bool:
        channel = await resolve_message_channel(self.bot, guild, self.config.verify_log_channel_id)
        if channel is None:
            return False

        link_url = request.verification_value if request.verification_type == "Link" else None
        view = StaffReviewView(self, request.id, link_url=link_url)
        try:
            message = await channel.send(
                content=mention_role(self.config.moderation_role_id),
                embed=embeds.verification_log_embed(request, member),
                view=view,
                allowed_mentions=discord.AllowedMentions(roles=True),
            )
        except discord.HTTPException:
            log.exception("Failed to send verification request %s to staff.", request.id)
            return False

        await self.database.set_log_message(
            request_id=request.id,
            log_message_id=message.id,
            log_channel_id=message.channel.id,
        )
        return True

    async def _approve_request(
        self,
        interaction: discord.Interaction,
        request: VerificationRequest,
    ) -> None:
        assert interaction.guild is not None
        assert isinstance(interaction.user, discord.Member)

        member = await self._get_member(interaction.guild, request.user_id)
        if member is None:
            await interaction.followup.send(
                "I couldn't find that user in the server, so roles were not changed.",
                ephemeral=True,
            )
            return

        verified_role = interaction.guild.get_role(self.config.verified_role_id)
        selected_role_id = (
            self.config.domme_role_id
            if request.selected_role == "Domme"
            else self.config.submissive_role_id
        )
        selected_role = interaction.guild.get_role(selected_role_id)
        unverified_role = interaction.guild.get_role(self.config.unverified_role_id)

        missing_roles = []
        if verified_role is None:
            missing_roles.append("Verified")
        if selected_role is None:
            missing_roles.append(request.selected_role or "Selected")
        if missing_roles:
            await interaction.followup.send(
                f"I couldn't find the configured role(s): {', '.join(missing_roles)}.",
                ephemeral=True,
            )
            return

        try:
            if unverified_role and unverified_role in member.roles:
                await member.remove_roles(
                    unverified_role,
                    reason=f"Approved by {interaction.user}",
                )

            roles_to_add = [
                role
                for role in (verified_role, selected_role)
                if role is not None and role not in member.roles
            ]
            if roles_to_add:
                await member.add_roles(
                    *roles_to_add,
                    reason=f"Approved by {interaction.user}",
                )
        except discord.Forbidden:
            await interaction.followup.send(
                "I don't have permission to update that user's roles.",
                ephemeral=True,
            )
            return
        except discord.HTTPException:
            log.exception("Failed to update roles for %s.", member.id)
            await interaction.followup.send(
                "Discord rejected the role update. Please try again.",
                ephemeral=True,
            )
            return

        updated = await self.database.mark_reviewed(
            request_id=request.id,
            status="approved",
            reviewed_by=interaction.user.id,
        )
        if not updated:
            await interaction.followup.send(
                "This verification request has already been processed.",
                ephemeral=True,
            )
            return

        await safe_dm(member, embed=embeds.approved_dm_embed(self.config))
        await self._send_general_announcement(request)
        await self._edit_staff_message(
            interaction,
            request,
            title="User Verified!",
            color=embeds.GREEN,
            status="Approved",
        )
        await interaction.followup.send("Verification approved.", ephemeral=True)

    async def _deny_request(
        self,
        interaction: discord.Interaction,
        request: VerificationRequest,
        *,
        status: str,
        dm_embed: discord.Embed,
        log_title: str,
        log_color: discord.Color,
        log_status: str,
        followup: str,
    ) -> None:
        assert isinstance(interaction.user, discord.Member)

        updated = await self.database.mark_reviewed(
            request_id=request.id,
            status=status,
            reviewed_by=interaction.user.id,
        )
        if not updated:
            await interaction.followup.send(
                "This verification request has already been processed.",
                ephemeral=True,
            )
            return

        user = self.bot.get_user(request.user_id)
        if user is None:
            try:
                user = await self.bot.fetch_user(request.user_id)
            except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                user = None

        if user:
            await safe_dm(user, embed=dm_embed)

        await self._edit_staff_message(
            interaction,
            request,
            title=log_title,
            color=log_color,
            status=log_status,
        )
        await interaction.followup.send(followup, ephemeral=True)

    async def _edit_staff_message(
        self,
        interaction: discord.Interaction,
        request: VerificationRequest,
        *,
        title: str,
        color: discord.Color,
        status: str,
    ) -> None:
        assert isinstance(interaction.user, discord.Member)
        link_url = request.verification_value if request.verification_type == "Link" else None
        view = StaffReviewView(None, request.id, link_url=link_url, disabled=True)
        embed = embeds.verification_outcome_embed(
            request=request,
            moderator=interaction.user,
            title=title,
            color=color,
            status=status,
        )
        try:
            if interaction.message:
                await interaction.message.edit(content=None, embed=embed, view=view)
        except discord.HTTPException:
            log.exception("Failed to edit staff verification message %s.", request.id)

    async def _send_general_announcement(self, request: VerificationRequest) -> None:
        guild = self.bot.get_guild(request.guild_id)
        if guild is None:
            return

        channel = await resolve_message_channel(self.bot, guild, self.config.general_channel_id)
        if channel is None:
            return

        template = random.choice(
            messages.GENERAL_DOMME_MESSAGES
            if request.selected_role == "Domme"
            else messages.GENERAL_SUBMISSIVE_MESSAGES
        )
        try:
            await channel.send(template.format(user_mention=user_mention(request.user_id)))
        except discord.HTTPException:
            log.exception("Failed to send general announcement for %s.", request.user_id)

    async def _record_expired(
        self,
        member: discord.Member,
        guild: discord.Guild,
        *,
        submission: VerificationSubmission | None = None,
    ) -> None:
        try:
            await self.database.create_request(
                user_id=member.id,
                guild_id=guild.id,
                username=display_username(member),
                verification_type=submission.verification_type if submission else None,
                verification_value=submission.verification_value if submission else None,
                selected_role=None,
                status="expired",
            )
        except sqlite3.IntegrityError:
            pass

    async def _get_member(
        self,
        guild: discord.Guild,
        user_id: int,
    ) -> discord.Member | None:
        member = guild.get_member(user_id)
        if member:
            return member
        try:
            return await guild.fetch_member(user_id)
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            return None

    async def _send_interaction_message(
        self,
        interaction: discord.Interaction,
        content: str | None = None,
        *,
        embed: discord.Embed | None = None,
        ephemeral: bool = False,
    ) -> None:
        if interaction.response.is_done():
            await interaction.followup.send(content=content, embed=embed, ephemeral=ephemeral)
        else:
            await interaction.response.send_message(content=content, embed=embed, ephemeral=ephemeral)


class VerificationCog(commands.Cog):
    def __init__(
        self,
        bot: commands.Bot,
        config: BotConfig,
        database: Database,
    ) -> None:
        self.bot = bot
        self.service = VerificationService(bot, config, database)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        await self.service.handle_member_join(member)

    @app_commands.command(
        name="setup-verification",
        description="Posts the verification panel in the configured verification channel.",
    )
    async def setup_verification(self, interaction: discord.Interaction) -> None:
        await self.service.setup_verification_panel(interaction)

    @app_commands.command(
        name="verify-status",
        description="Checks a user's verification status.",
    )
    @app_commands.describe(user="The user to check.")
    async def verify_status(
        self,
        interaction: discord.Interaction,
        user: discord.User,
    ) -> None:
        await self.service.verify_status(interaction, user)

    @app_commands.command(
        name="verify-cleanup",
        description="Shows users who still have the Unverified role.",
    )
    async def verify_cleanup(self, interaction: discord.Interaction) -> None:
        await self.service.verify_cleanup(interaction)

    @app_commands.command(
        name="help",
        description="Shows the restricted bot help menu.",
    )
    async def help(self, interaction: discord.Interaction) -> None:
        if interaction.user.id not in messages.HELP_ALLOWED_USER_IDS:
            await interaction.response.send_message(
                messages.UNAUTHORISED_HELP_RESPONSE,
                ephemeral=True,
            )
            return

        view = HelpView(interaction.user.id)
        await interaction.response.send_message(
            embed=embeds.help_page_embed(view.current_page, view.total_pages),
            view=view,
            ephemeral=True,
        )
