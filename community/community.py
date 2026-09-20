from __future__ import annotations

from datetime import datetime, timezone

import discord
from discord import app_commands
from discord.ext import commands

from core.scope import member_is_lead, require_community
from .community_config import (
    COMMUNITY_COLOR,
    EMBEDS,
    FEEDBACK_BODY_LABEL,
    FEEDBACK_CHANNEL_ID,
    FEEDBACK_CHANNEL_NAME,
    FEEDBACK_MODAL_TITLE,
    FEEDBACK_SUBJECT_LABEL,
    POLL_BUTTON_A_LABEL,
    POLL_BUTTON_B_LABEL,
)


def config_embed(key: str, **values: str) -> discord.Embed:
    title, body = EMBEDS[key]
    return build_public_embed(title.format(**values), body.format(**values))


class PollView(discord.ui.View):
    def __init__(self, question: str, option_a: str, option_b: str):
        super().__init__(timeout=None)
        self.question = question
        self.option_a = option_a
        self.option_b = option_b
        self.votes: dict[int, str] = {}

    def _embed(self) -> discord.Embed:
        a_count = list(self.votes.values()).count("A")
        b_count = list(self.votes.values()).count("B")
        return config_embed(
            "poll",
            question=self.question,
            option_a=self.option_a,
            option_b=self.option_b,
            a_count=a_count,
            b_count=b_count,
        )

    async def _vote(self, interaction: discord.Interaction, option: str) -> None:
        if not await require_community(interaction):
            return
        self.votes[interaction.user.id] = option
        if interaction.message:
            await interaction.message.edit(embed=self._embed(), view=self)
        await interaction.response.send_message(
            embed=config_embed("vote_recorded", option=option),
            ephemeral=True,
        )

    @discord.ui.button(label=POLL_BUTTON_A_LABEL, style=discord.ButtonStyle.primary)
    async def option_a_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._vote(interaction, "A")

    @discord.ui.button(label=POLL_BUTTON_B_LABEL, style=discord.ButtonStyle.primary)
    async def option_b_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._vote(interaction, "B")


def build_public_embed(title: str, body: str) -> discord.Embed:
    return discord.Embed(
        title=title,
        description=body,
        color=COMMUNITY_COLOR,
        timestamp=datetime.now(timezone.utc),
    )


class FeedbackModal(discord.ui.Modal, title=FEEDBACK_MODAL_TITLE):
    subject = discord.ui.TextInput(label=FEEDBACK_SUBJECT_LABEL, max_length=100)
    feedback = discord.ui.TextInput(label=FEEDBACK_BODY_LABEL, style=discord.TextStyle.paragraph, max_length=1500)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        if not await require_community(interaction):
            return
        embed = config_embed(
            "feedback",
            subject=self.subject.value,
            feedback=self.feedback.value,
            user=interaction.user.mention,
        )
        channel = None
        if interaction.guild:
            resolved = interaction.guild.get_channel(FEEDBACK_CHANNEL_ID) if FEEDBACK_CHANNEL_ID else None
            channel = resolved or discord.utils.get(interaction.guild.text_channels, name=FEEDBACK_CHANNEL_NAME)
        if isinstance(channel, discord.TextChannel):
            await channel.send(embed=embed)
        await interaction.response.send_message(embed=embed, ephemeral=True)


class CommunityCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _lead_only(self, interaction: discord.Interaction) -> bool:
        if not await require_community(interaction):
            return False
        if not isinstance(interaction.user, discord.Member) or not member_is_lead(interaction.user):
            await interaction.response.send_message(
                embed=config_embed("access_denied"),
                ephemeral=True,
            )
            return False
        return True

    async def announce(self, interaction: discord.Interaction, title: str, body: str):
        if not await self._lead_only(interaction):
            return
        embed = config_embed("announcement", title=title.upper(), body=body)
        await interaction.channel.send(embed=embed)
        await interaction.response.send_message(
            embed=config_embed("announcement_posted"),
            ephemeral=True,
        )

    async def poll(self, interaction: discord.Interaction, question: str, option_a: str, option_b: str):
        if not await self._lead_only(interaction):
            return
        view = PollView(question, option_a, option_b)
        await interaction.channel.send(embed=view._embed(), view=view)
        await interaction.response.send_message(
            embed=config_embed("poll_posted"),
            ephemeral=True,
        )

    async def feedback(self, interaction: discord.Interaction):
        if not await require_community(interaction):
            return
        await interaction.response.send_modal(FeedbackModal())

    async def update_post(self, interaction: discord.Interaction, title: str, body: str):
        if not await self._lead_only(interaction):
            return
        embed = config_embed("update", title=title.upper(), body=body)
        await interaction.channel.send(embed=embed)
        await interaction.response.send_message(
            embed=config_embed("update_posted"),
            ephemeral=True,
        )


async def setup(bot: commands.Bot):
    from core.bot_config import COMMUNITY_GUILD_ID

    await bot.add_cog(CommunityCog(bot), guild=discord.Object(id=COMMUNITY_GUILD_ID))
