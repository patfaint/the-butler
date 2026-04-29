from __future__ import annotations

from typing import TYPE_CHECKING

import discord

from bot import messages
from bot.embeds import help_page_embed

if TYPE_CHECKING:
    from bot.verification import VerificationService


class VerificationPanelView(discord.ui.View):
    def __init__(self, service: VerificationService) -> None:
        super().__init__(timeout=None)
        self.service = service

    @discord.ui.button(
        label="Verify",
        style=discord.ButtonStyle.primary,
        custom_id="verify_start",
    )
    async def verify_start(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        await self.service.start_verification(interaction)


class RoleSelectionView(discord.ui.View):
    def __init__(self, user_id: int) -> None:
        super().__init__(timeout=300)
        self.user_id = user_id
        self.selection: str | None = None
        self.message: discord.Message | None = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id == self.user_id:
            return True
        await interaction.response.send_message(
            "This role selection is not for you.",
            ephemeral=True,
        )
        return False

    @discord.ui.button(label="Domme", style=discord.ButtonStyle.secondary)
    async def domme(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        await self._select(interaction, "Domme")

    @discord.ui.button(label="Submissive", style=discord.ButtonStyle.secondary)
    async def submissive(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        await self._select(interaction, "Submissive")

    async def _select(self, interaction: discord.Interaction, value: str) -> None:
        self.selection = value
        self._disable_all()
        await interaction.response.edit_message(view=self)
        self.stop()

    async def on_timeout(self) -> None:
        self._disable_all()
        if self.message:
            try:
                await self.message.edit(view=self)
            except discord.HTTPException:
                pass

    def _disable_all(self) -> None:
        for item in self.children:
            if hasattr(item, "disabled"):
                item.disabled = True


class StaffReviewView(discord.ui.View):
    def __init__(
        self,
        service: VerificationService | None,
        request_id: int,
        *,
        link_url: str | None = None,
        disabled: bool = False,
    ) -> None:
        super().__init__(timeout=None)
        self.service = service
        self.request_id = request_id

        approve = discord.ui.Button(
            label="Approve",
            style=discord.ButtonStyle.success,
            custom_id=f"verification:approve:{request_id}",
            disabled=disabled,
        )
        approve.callback = self._approve
        self.add_item(approve)

        deny_underage = discord.ui.Button(
            label="Deny (Under 18)",
            style=discord.ButtonStyle.danger,
            custom_id=f"verification:deny_underage:{request_id}",
            disabled=disabled,
        )
        deny_underage.callback = self._deny_underage
        self.add_item(deny_underage)

        deny_invalid = discord.ui.Button(
            label="Deny (Invalid Service)",
            style=discord.ButtonStyle.danger,
            custom_id=f"verification:deny_invalid:{request_id}",
            disabled=disabled,
        )
        deny_invalid.callback = self._deny_invalid
        self.add_item(deny_invalid)

        if link_url:
            self.add_item(
                discord.ui.Button(
                    label="Open Link",
                    style=discord.ButtonStyle.link,
                    url=link_url,
                    disabled=disabled,
                )
            )

    async def _approve(self, interaction: discord.Interaction) -> None:
        if self.service:
            await self.service.review_request(interaction, self.request_id, "approve")

    async def _deny_underage(self, interaction: discord.Interaction) -> None:
        if self.service:
            await self.service.review_request(interaction, self.request_id, "deny_underage")

    async def _deny_invalid(self, interaction: discord.Interaction) -> None:
        if self.service:
            await self.service.review_request(interaction, self.request_id, "deny_invalid")


class FormLinkView(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=None)
        self.add_item(
            discord.ui.Button(
                label="Open Form",
                style=discord.ButtonStyle.link,
                url=messages.FORM_URL,
            )
        )


class HelpView(discord.ui.View):
    def __init__(self, user_id: int) -> None:
        super().__init__(timeout=180)
        self.user_id = user_id
        self.current_page = 0
        self.total_pages = 3

        self.previous_button = discord.ui.Button(
            label="<",
            style=discord.ButtonStyle.secondary,
            custom_id=f"help:previous:{user_id}",
        )
        self.previous_button.callback = self._previous
        self.add_item(self.previous_button)

        self.page_button = discord.ui.Button(
            label="Page 1/3",
            style=discord.ButtonStyle.secondary,
            disabled=True,
        )
        self.add_item(self.page_button)

        self.next_button = discord.ui.Button(
            label=">",
            style=discord.ButtonStyle.secondary,
            custom_id=f"help:next:{user_id}",
        )
        self.next_button.callback = self._next
        self.add_item(self.next_button)

        self.close_button = discord.ui.Button(
            label="Close",
            style=discord.ButtonStyle.danger,
            custom_id=f"help:close:{user_id}",
        )
        self.close_button.callback = self._close
        self.add_item(self.close_button)
        self._sync_buttons()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id == self.user_id and interaction.user.id in messages.HELP_ALLOWED_USER_IDS:
            return True
        await interaction.response.send_message(
            messages.UNAUTHORISED_HELP_RESPONSE,
            ephemeral=True,
        )
        return False

    async def _previous(self, interaction: discord.Interaction) -> None:
        self.current_page = max(0, self.current_page - 1)
        await self._update(interaction)

    async def _next(self, interaction: discord.Interaction) -> None:
        self.current_page = min(self.total_pages - 1, self.current_page + 1)
        await self._update(interaction)

    async def _close(self, interaction: discord.Interaction) -> None:
        self._disable_all()
        await interaction.response.edit_message(
            content="Help menu closed.",
            embed=None,
            view=None,
        )
        self.stop()

    async def _update(self, interaction: discord.Interaction) -> None:
        self._sync_buttons()
        await interaction.response.edit_message(
            embed=help_page_embed(self.current_page, self.total_pages),
            view=self,
        )

    def _sync_buttons(self) -> None:
        self.previous_button.disabled = self.current_page == 0
        self.next_button.disabled = self.current_page == self.total_pages - 1
        self.page_button.label = f"Page {self.current_page + 1}/{self.total_pages}"

    def _disable_all(self) -> None:
        for item in self.children:
            if hasattr(item, "disabled"):
                item.disabled = True
