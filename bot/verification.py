from __future__ import annotations

import asyncio
import logging
import random
import sqlite3
import time
from dataclasses import dataclass

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
    has_admin_command_permissions,
    has_moderation_role,
    mention_role,
    resolve_message_channel,
    safe_dm,
    user_mention,
)
from bot.views import (
    DommeDeleteConfirmView,
    DommeSetupCoffeeView,
    DommeSetupDetailsView,
    DommeSetupIntroView,
    DommeSetupNameView,
    DommeSetupPaymentsView,
    DommeSetupReviewView,
    DommeSetupThroneView,
    FormLinkView,
    HelpView,
    RoleSelectionView,
    StaffReviewView,
    VerificationPanelView,
)

log = logging.getLogger(__name__)


@dataclass
class DommeProfileSession:
    user_id: int
    message: discord.Message | None = None
    name: str | None = None
    honorific: str | None = None
    pronouns: str | None = None
    age: str | None = None
    tribute_price: str | None = None
    throne: str | None = None
    paypal: str | None = None
    youpay: str | None = None
    cashapp: str | None = None
    venmo: str | None = None
    beemit: str | None = None
    loyalfans: str | None = None
    onlyfans: str | None = None
    throne_tracking_enabled: bool = False
    coffee_enabled: bool = False


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
        self.session_tasks: set[asyncio.Task[None]] = set()

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

        verified_role = interaction.guild.get_role(self.config.verified_role_id)
        if verified_role and verified_role in interaction.user.roles:
            await self._send_interaction_message(
                interaction,
                messages.ALREADY_VERIFIED_RESPONSE,
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
            prompt_message = await interaction.user.send(
                embed=embeds.initial_verification_dm_embed(),
            )
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
        self._start_dm_flow(interaction.user, interaction.guild, key, prompt_message)

    def _start_dm_flow(
        self,
        member: discord.Member,
        guild: discord.Guild,
        key: tuple[int, int],
        prompt_message: discord.Message,
    ) -> None:
        task = asyncio.create_task(self._run_dm_flow_safely(member, guild, key, prompt_message))
        self.session_tasks.add(task)
        task.add_done_callback(self.session_tasks.discard)

    async def _run_dm_flow_safely(
        self,
        member: discord.Member,
        guild: discord.Guild,
        key: tuple[int, int],
        prompt_message: discord.Message,
    ) -> None:
        try:
            await self._run_dm_flow(member, guild, key, prompt_message)
        except Exception:
            log.exception("Unexpected verification session failure for %s.", member.id)
            self.active_sessions.discard(key)
            await self._edit_dm_message(
                prompt_message,
                embed=embeds.session_expired_dm_embed(),
                view=None,
            )

    async def setup_verification_panel(self, ctx: commands.Context[commands.Bot]) -> None:
        if ctx.guild is None or not isinstance(ctx.author, discord.Member):
            await self._send_context_message(ctx, "This command can only be used in a server.")
            return

        if not has_admin_command_permissions(ctx.author, self.config):
            await self._send_context_message(ctx, messages.UNAUTHORISED_HELP_RESPONSE)
            return

        channel = await resolve_message_channel(
            self.bot,
            ctx.guild,
            self.config.verification_channel_id,
        )
        if channel is None:
            await self._send_context_message(
                ctx,
                "I couldn't find the configured verification channel.",
            )
            return

        try:
            await channel.send(
                embed=embeds.verification_panel_embed(),
                view=VerificationPanelView(self),
            )
        except discord.HTTPException:
            log.exception("Failed to post verification panel.")
            await self._send_context_message(
                ctx,
                "I couldn't post the verification panel. Please check my channel permissions.",
            )
            return

        await self._send_context_message(
            ctx,
            f"Verification panel posted in {channel.mention}.",
        )

    async def verify_status(
        self,
        ctx: commands.Context[commands.Bot],
        user: discord.User | discord.Member,
    ) -> None:
        if ctx.guild is None or not isinstance(ctx.author, discord.Member):
            await self._send_context_message(ctx, "This command can only be used in a server.")
            return

        if not has_admin_command_permissions(ctx.author, self.config):
            await self._send_context_message(ctx, messages.UNAUTHORISED_HELP_RESPONSE)
            return

        request = await self.database.get_latest_request(
            user_id=user.id,
            guild_id=ctx.guild.id,
        )
        await self._send_context_message(
            ctx,
            embed=embeds.verification_status_embed(request, user),
        )

    async def verify_cleanup(self, ctx: commands.Context[commands.Bot]) -> None:
        if ctx.guild is None or not isinstance(ctx.author, discord.Member):
            await self._send_context_message(ctx, "This command can only be used in a server.")
            return

        if not has_admin_command_permissions(ctx.author, self.config):
            await self._send_context_message(ctx, messages.UNAUTHORISED_HELP_RESPONSE)
            return

        role = ctx.guild.get_role(self.config.unverified_role_id)
        if role is None:
            await self._send_context_message(ctx, "I couldn't find the configured Unverified role.")
            return

        members = sorted(
            [member for member in role.members if not member.bot],
            key=lambda member: member.display_name.lower(),
        )
        await self._send_context_message(
            ctx,
            embed=embeds.verification_cleanup_embed(role=role, members=members),
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

        if not has_moderation_role(interaction.user, self.config):
            await self._send_interaction_message(
                interaction,
                messages.UNAUTHORISED_STAFF_BUTTON_RESPONSE,
                ephemeral=True,
            )
            return

        await interaction.response.defer(ephemeral=True)

        claimed = await self.database.claim_pending_request(
            request_id=request_id,
            reviewed_by=interaction.user.id,
        )
        if not claimed:
            await interaction.followup.send(
                "This verification request has already been processed.",
                ephemeral=True,
            )
            return

        request = await self.database.get_request(request_id)
        if request is None or request.status != "pending":
            await self.database.release_request_claim(
                request_id=request_id,
                reviewed_by=interaction.user.id,
            )
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
            await self.database.release_request_claim(
                request_id=request_id,
                reviewed_by=interaction.user.id,
            )
            await interaction.followup.send("Unknown verification action.", ephemeral=True)

    async def _run_dm_flow(
        self,
        member: discord.Member,
        guild: discord.Guild,
        key: tuple[int, int],
        prompt_message: discord.Message,
    ) -> None:
        try:
            submission = await self._wait_for_submission(member, prompt_message)
            if submission is None:
                await self._edit_dm_message(
                    prompt_message,
                    embed=embeds.session_expired_dm_embed(),
                    view=None,
                )
                await self._record_expired(member, guild)
                return

            selected_role = await self._ask_role(member, prompt_message)
            if selected_role is None:
                await self._edit_dm_message(
                    prompt_message,
                    embed=embeds.session_expired_dm_embed(),
                    view=None,
                )
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
                await self._edit_dm_message(
                    prompt_message,
                    embed=embeds.session_expired_dm_embed(),
                    view=None,
                )
                return

            submitted = await self._submit_to_staff(guild, member, request)
            if not submitted:
                await self.database.mark_reviewed(
                    request_id=request.id,
                    status="expired",
                    reviewed_by=None,
                )
                await self._edit_dm_message(
                    prompt_message,
                    embed=embeds.session_expired_dm_embed(),
                    view=None,
                )
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
        prompt_message: discord.Message,
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

            await self._edit_dm_message(
                prompt_message,
                embed=embeds.initial_verification_dm_embed(messages.INVALID_SUBMISSION_DM_DESCRIPTION),
                view=None,
            )

    async def _ask_role(
        self,
        member: discord.Member,
        prompt_message: discord.Message,
    ) -> str | None:
        view = RoleSelectionView(member.id)
        view.message = prompt_message
        await self._edit_dm_message(
            prompt_message,
            embed=embeds.role_prompt_embed(),
            view=view,
        )

        timed_out = await view.wait()
        if timed_out:
            return None

        await self._edit_dm_message(
            prompt_message,
            embed=embeds.role_prompt_embed(view.selection),
            view=view,
        )
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
            await self.database.release_request_claim(
                request_id=request.id,
                reviewed_by=interaction.user.id,
            )
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
            await self.database.release_request_claim(
                request_id=request.id,
                reviewed_by=interaction.user.id,
            )
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
            await self.database.release_request_claim(
                request_id=request.id,
                reviewed_by=interaction.user.id,
            )
            await interaction.followup.send(
                "I don't have permission to update that user's roles.",
                ephemeral=True,
            )
            return
        except discord.HTTPException:
            log.exception("Failed to update roles for %s.", member.id)
            await self.database.release_request_claim(
                request_id=request.id,
                reviewed_by=interaction.user.id,
            )
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
            await self.database.release_request_claim(
                request_id=request.id,
                reviewed_by=interaction.user.id,
            )
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
            await self.database.release_request_claim(
                request_id=request.id,
                reviewed_by=interaction.user.id,
            )
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

    async def _edit_dm_message(
        self,
        message: discord.Message,
        *,
        embed: discord.Embed,
        view: discord.ui.View | None,
    ) -> None:
        try:
            await message.edit(embed=embed, view=view)
        except (discord.Forbidden, discord.NotFound, discord.HTTPException):
            log.exception("Failed to edit DM message %s.", message.id)

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

    async def _send_context_message(
        self,
        ctx: commands.Context[commands.Bot],
        content: str | None = None,
        *,
        embed: discord.Embed | None = None,
    ) -> None:
        await ctx.reply(content=content, embed=embed, mention_author=False)

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


class DommeProfileService:
    def __init__(
        self,
        bot: commands.Bot,
        config: BotConfig,
        database: Database,
    ) -> None:
        self.bot = bot
        self.config = config
        self.database = database
        self.sessions: dict[int, DommeProfileSession] = {}

    def finish_session(self, user_id: int) -> None:
        self.sessions.pop(user_id, None)

    def build_later_embed(self) -> discord.Embed:
        return embeds.domme_setup_later_embed()

    def build_cancelled_embed(self) -> discord.Embed:
        return embeds.domme_setup_cancelled_embed()

    async def start_setup(self, member: discord.Member) -> bool:
        session = DommeProfileSession(user_id=member.id)
        view = DommeSetupIntroView(self, session)
        try:
            session.message = await member.send(
                embed=embeds.domme_setup_intro_embed(),
                view=view,
            )
        except (discord.Forbidden, discord.HTTPException):
            return False

        self.sessions[member.id] = session
        return True

    async def show_name_step(
        self,
        session: DommeProfileSession,
        interaction: discord.Interaction,
    ) -> None:
        await self._update_session_message(
            session,
            interaction=interaction,
            embed=embeds.domme_setup_name_embed(
                name=session.name,
                honorific=session.honorific,
            ),
            view=DommeSetupNameView(self, session),
        )

    async def show_details_step(
        self,
        session: DommeProfileSession,
        interaction: discord.Interaction,
    ) -> None:
        await self._update_session_message(
            session,
            interaction=interaction,
            embed=embeds.domme_setup_details_embed(
                pronouns=session.pronouns,
                age=session.age,
                tribute_price=session.tribute_price,
            ),
            view=DommeSetupDetailsView(self, session),
        )

    async def show_payments_step(
        self,
        session: DommeProfileSession,
        interaction: discord.Interaction,
    ) -> None:
        await self._update_session_message(
            session,
            interaction=interaction,
            embed=embeds.domme_setup_payments_embed(
                throne=session.throne,
                paypal=session.paypal,
                youpay=session.youpay,
                cashapp=session.cashapp,
                venmo=session.venmo,
                beemit=session.beemit,
                loyalfans=session.loyalfans,
                onlyfans=session.onlyfans,
            ),
            view=DommeSetupPaymentsView(self, session),
        )

    async def refresh_payments_step(
        self,
        session: DommeProfileSession,
        interaction: discord.Interaction,
    ) -> None:
        await self.show_payments_step(session, interaction)

    async def advance_after_payments(
        self,
        session: DommeProfileSession,
        interaction: discord.Interaction,
    ) -> None:
        if session.throne:
            await self.show_throne_step(session, interaction)
            return
        session.throne_tracking_enabled = False
        await self.show_coffee_step(session, interaction)

    async def show_throne_step(
        self,
        session: DommeProfileSession,
        interaction: discord.Interaction,
    ) -> None:
        await self._update_session_message(
            session,
            interaction=interaction,
            embed=embeds.domme_setup_throne_embed(throne=session.throne),
            view=DommeSetupThroneView(self, session),
        )

    async def show_coffee_step(
        self,
        session: DommeProfileSession,
        interaction: discord.Interaction,
    ) -> None:
        await self._update_session_message(
            session,
            interaction=interaction,
            embed=embeds.domme_setup_coffee_embed(coffee_enabled=None),
            view=DommeSetupCoffeeView(self, session),
        )

    async def show_review_step(
        self,
        session: DommeProfileSession,
        interaction: discord.Interaction,
    ) -> None:
        await self._update_session_message(
            session,
            interaction=interaction,
            embed=embeds.domme_setup_review_embed(
                name=session.name,
                honorific=session.honorific,
                pronouns=session.pronouns,
                age=session.age,
                tribute_price=session.tribute_price,
                throne=session.throne,
                paypal=session.paypal,
                youpay=session.youpay,
                cashapp=session.cashapp,
                venmo=session.venmo,
                beemit=session.beemit,
                loyalfans=session.loyalfans,
                onlyfans=session.onlyfans,
                throne_tracking_enabled=session.throne_tracking_enabled,
                coffee_enabled=session.coffee_enabled,
            ),
            view=DommeSetupReviewView(self, session),
        )

    async def save_profile(
        self,
        session: DommeProfileSession,
        interaction: discord.Interaction,
    ) -> None:
        await self.database.save_domme_profile(
            user_id=session.user_id,
            name=session.name,
            honorific=session.honorific,
            pronouns=session.pronouns,
            age=session.age,
            tribute_price=session.tribute_price,
            throne=session.throne,
            paypal=session.paypal,
            youpay=session.youpay,
            cashapp=session.cashapp,
            venmo=session.venmo,
            beemit=session.beemit,
            loyalfans=session.loyalfans,
            onlyfans=session.onlyfans,
            throne_tracking_enabled=session.throne_tracking_enabled,
            coffee_enabled=session.coffee_enabled,
        )
        self.finish_session(session.user_id)
        await self._update_session_message(
            session,
            interaction=interaction,
            embed=embeds.domme_setup_complete_embed(),
            view=None,
        )

    async def delete_profile(self, interaction: discord.Interaction, user_id: int) -> None:
        deleted = await self.database.delete_domme_profile(user_id=user_id)
        if deleted:
            await interaction.response.edit_message(
                content="Your Domme profile has been deleted.",
                view=None,
            )
            return

        await interaction.response.edit_message(
            content="I couldn't find a saved Domme profile to delete.",
            view=None,
        )

    async def _update_session_message(
        self,
        session: DommeProfileSession,
        *,
        interaction: discord.Interaction,
        embed: discord.Embed,
        view: discord.ui.View | None,
    ) -> None:
        if session.message is None:
            return

        try:
            if interaction.response.is_done():
                await session.message.edit(embed=embed, view=view)
            else:
                await interaction.response.edit_message(embed=embed, view=view)
                if interaction.message:
                    session.message = interaction.message
        except discord.HTTPException:
            log.exception("Failed to update Domme profile setup for %s.", session.user_id)
            self.finish_session(session.user_id)


class VerificationCog(commands.Cog):
    def __init__(
        self,
        bot: commands.Bot,
        config: BotConfig,
        database: Database,
    ) -> None:
        self.bot = bot
        self.config = config
        self.database = database
        self.service = VerificationService(bot, config, database)
        self.domme_service = DommeProfileService(bot, config, database)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        await self.service.handle_member_join(member)

    @commands.command(name="setup_verification")
    async def setup_verification(self, ctx: commands.Context[commands.Bot]) -> None:
        await self.service.setup_verification_panel(ctx)

    @commands.command(name="verify_status")
    async def verify_status(
        self,
        ctx: commands.Context[commands.Bot],
        user: discord.User,
    ) -> None:
        await self.service.verify_status(ctx, user)

    @commands.command(name="verify_cleanup")
    async def verify_cleanup(self, ctx: commands.Context[commands.Bot]) -> None:
        await self.service.verify_cleanup(ctx)

    @commands.command(name="domme")
    async def domme(
        self,
        ctx: commands.Context[commands.Bot],
        action: str | None = None,
    ) -> None:
        if ctx.guild is None or not isinstance(ctx.author, discord.Member):
            await ctx.reply("This command can only be used in a server channel.", mention_author=False)
            return

        domme_role = ctx.guild.get_role(self.config.domme_role_id)
        if domme_role is None:
            await ctx.reply("I couldn't find the configured Domme role.", mention_author=False)
            return

        if domme_role not in ctx.author.roles:
            await ctx.reply("Only members with the Domme role can use this command.", mention_author=False)
            return

        profile = await self.database.get_domme_profile(user_id=ctx.author.id)
        requested_action = (action or "").strip().lower()

        if requested_action == "delete":
            if profile is None:
                await ctx.reply("You do not have a saved Domme profile to delete.", mention_author=False)
                return

            view = DommeDeleteConfirmView(self.domme_service, ctx.author.id)
            reply = await ctx.reply(
                "Are you sure you want to delete your Domme profile?",
                view=view,
                mention_author=False,
            )
            view.message = reply
            return

        if profile is not None:
            await ctx.reply(
                embed=embeds.domme_profile_embed(profile, ctx.author),
                mention_author=False,
            )
            return

        if ctx.author.id in self.domme_service.sessions:
            await ctx.reply(
                "You already have a Domme profile setup in progress. Please check your DMs.",
                mention_author=False,
            )
            return

        started = await self.domme_service.start_setup(ctx.author)
        if not started:
            await ctx.reply(messages.DM_FAILURE_RESPONSE, mention_author=False)
            return

        await ctx.reply("Hey! Look in your DM’s!", mention_author=False)

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
