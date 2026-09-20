from __future__ import annotations

import discord

from .moderation_embeds import info_embed


class PagedEmbedView(discord.ui.View):
    def __init__(self, embeds: list[discord.Embed], owner_id: int):
        super().__init__(timeout=180)
        self.embeds = embeds or [info_embed("No Records", "No moderation records were found.")]
        self.owner_id = owner_id
        self.index = 0
        self._sync_buttons()

    def _sync_buttons(self) -> None:
        for item in self.children:
            if isinstance(item, discord.ui.Button):
                if item.custom_id == "hc_mod_prev":
                    item.disabled = self.index <= 0
                elif item.custom_id == "hc_mod_next":
                    item.disabled = self.index >= len(self.embeds) - 1

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id == self.owner_id:
            return True
        await interaction.response.send_message(embed=info_embed("Dashboard Locked", "Only the moderator who opened this view can use these controls."), ephemeral=True)
        return False

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.secondary, custom_id="hc_mod_prev")
    async def previous(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.index = max(0, self.index - 1)
        self._sync_buttons()
        await interaction.response.edit_message(embed=self.embeds[self.index], view=self)

    @discord.ui.button(label="Next", style=discord.ButtonStyle.secondary, custom_id="hc_mod_next")
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.index = min(len(self.embeds) - 1, self.index + 1)
        self._sync_buttons()
        await interaction.response.edit_message(embed=self.embeds[self.index], view=self)


class NoteModal(discord.ui.Modal, title="Add Moderator Note"):
    note = discord.ui.TextInput(
        label="Private staff note",
        style=discord.TextStyle.paragraph,
        min_length=3,
        max_length=1500,
        required=True,
    )

    def __init__(self, cog, target: discord.Member):
        super().__init__(timeout=300)
        self.cog = cog
        self.target = target

    async def on_submit(self, interaction: discord.Interaction) -> None:
        await self.cog.add_note_from_modal(interaction, self.target, str(self.note))