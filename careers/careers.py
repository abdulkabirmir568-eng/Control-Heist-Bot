from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from core.bot_config import COMMUNITY_GUILD_ID
from .careers_config import (
    APPLICANT_DM_TITLE,
    APPLICATION_REVIEW_CHANNEL_ID,
    APPLY_BUTTON_LABEL,
    CAREERS_CHANNEL_ID,
    CAREERS_COLOR,
    CAREERS_EMBED_DESCRIPTION,
    CAREERS_EMBED_FOOTER,
    CAREERS_EMBED_TITLE,
    DECISIONS,
    GOOGLE_FORM_URL,
    MESSAGES,
    OWNER_ID,
    REVIEW_EMBED_TITLE,
    REVIEW_FAIL_LABEL,
    REVIEW_MODAL_FIELDS,
    REVIEW_MODAL_TITLE,
    REVIEW_PASS_LABEL,
    STUDIO_DIRECTOR_ROLE_IDS,
    STUDIO_DIRECTOR_USER_IDS,
)

review_messages: dict[int, dict] = {}


def _is_authorized(interaction: discord.Interaction) -> bool:
    if interaction.user.id == OWNER_ID:
        return True
    if isinstance(interaction.user, discord.Member):
        return any(role.id in STUDIO_DIRECTOR_ROLE_IDS for role in interaction.user.roles)
    return False


class CareersView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(
            discord.ui.Button(
                label=APPLY_BUTTON_LABEL,
                style=discord.ButtonStyle.link,
                url=GOOGLE_FORM_URL,
            )
        )


async def _resolve_review(interaction: discord.Interaction, view: discord.ui.View, decision: str) -> None:
    if not _is_authorized(interaction):
        await interaction.response.send_message(MESSAGES["not_authorised"], ephemeral=True)
        return

    review = review_messages.get(interaction.message.id)
    if not review:
        await interaction.response.send_message(MESSAGES["review_not_found"], ephemeral=True)
        return

    for child in view.children:
        child.disabled = True

    embed = interaction.message.embeds[0]
    embed.clear_fields()
    embed.add_field(name="Status", value=decision, inline=False)

    await interaction.message.edit(embed=embed, view=view)
    await interaction.response.send_message(MESSAGES["marked"].format(status=decision), ephemeral=True)

    applicant_id = review["applicant_id"]
    username = review["username"]
    position = review["position"]
    notes = review.get("notes", "")
    texts = DECISIONS[decision]

    try:
        user = await interaction.client.fetch_user(applicant_id)
        await user.send(
            embed=discord.Embed(
                title=APPLICANT_DM_TITLE,
                description=texts["applicant_message"].format(position=position),
                color=CAREERS_COLOR,
            )
        )
    except Exception as exc:
        print(f"[Careers] Failed to DM applicant: {exc}")

    notify_text = (
        f"**{username}** (`{applicant_id}`)\n"
        f"Position: **{position}**\n"
        f"Status: **{decision}**\n"
    )
    if notes:
        notify_text += f"Notes: {notes}\n"

    notify_embed = discord.Embed(
        title=texts["notify_title"],
        description=notify_text,
        color=CAREERS_COLOR,
    )

    recipients = [OWNER_ID] + [uid for uid in STUDIO_DIRECTOR_USER_IDS if uid != OWNER_ID]
    for user_id in recipients:
        try:
            recipient = await interaction.client.fetch_user(user_id)
            await recipient.send(embed=notify_embed)
        except Exception as exc:
            print(f"[Careers] Failed to notify {user_id}: {exc}")

    review_messages.pop(interaction.message.id, None)


class ReviewView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label=REVIEW_PASS_LABEL,
        style=discord.ButtonStyle.success,
        custom_id="appreview_pass",
    )
    async def pass_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await _resolve_review(interaction, self, "ACCEPTED")

    @discord.ui.button(
        label=REVIEW_FAIL_LABEL,
        style=discord.ButtonStyle.danger,
        custom_id="appreview_fail",
    )
    async def fail_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await _resolve_review(interaction, self, "REJECTED")


def build_careers_embed() -> discord.Embed:
    embed = discord.Embed(
        title=CAREERS_EMBED_TITLE,
        description=CAREERS_EMBED_DESCRIPTION,
        color=CAREERS_COLOR,
    )
    embed.set_footer(text=CAREERS_EMBED_FOOTER)
    return embed


def build_review_embed(user_id: int, username: str, position: str, notes: str = "") -> discord.Embed:
    description = (
        f"**Applicant:** {username}\n"
        f"**ID:** {user_id}\n"
        f"**Position:** {position}\n"
    )
    if notes:
        description += f"**Notes:** {notes}\n"
    description += "\n**Status:** PENDING"

    return discord.Embed(
        title=REVIEW_EMBED_TITLE,
        description=description,
        color=CAREERS_COLOR,
    )


class ReviewModal(discord.ui.Modal, title=REVIEW_MODAL_TITLE):
    user_id = discord.ui.TextInput(**REVIEW_MODAL_FIELDS["user_id"])
    username = discord.ui.TextInput(**REVIEW_MODAL_FIELDS["username"])
    position = discord.ui.TextInput(**REVIEW_MODAL_FIELDS["position"])
    notes = discord.ui.TextInput(style=discord.TextStyle.paragraph, **REVIEW_MODAL_FIELDS["notes"])

    async def on_submit(self, interaction: discord.Interaction):
        try:
            user_id = int(str(self.user_id.value).strip())
        except ValueError:
            await interaction.response.send_message(MESSAGES["invalid_user_id"], ephemeral=True)
            return

        channel = interaction.client.get_channel(APPLICATION_REVIEW_CHANNEL_ID)
        if channel is None:
            await interaction.response.send_message(
                MESSAGES["review_channel_missing"].format(channel_id=APPLICATION_REVIEW_CHANNEL_ID),
                ephemeral=True,
            )
            return

        username = str(self.username.value).strip()
        position = str(self.position.value).strip()
        notes = str(self.notes.value).strip()

        message = await channel.send(
            embed=build_review_embed(user_id=user_id, username=username, position=position, notes=notes),
            view=ReviewView(),
        )

        review_messages[message.id] = {
            "applicant_id": user_id,
            "username": username,
            "position": position,
            "notes": notes,
        }

        await interaction.response.send_message(
            MESSAGES["review_created"].format(channel=channel.mention), ephemeral=True
        )


class CareersCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._views_registered = False

    @commands.Cog.listener()
    async def on_ready(self):
        if self._views_registered:
            return
        self.bot.add_view(CareersView())
        self.bot.add_view(ReviewView())
        self._views_registered = True
        print("[Careers] Persistent views registered.")

    @app_commands.command(
        name="postcareers",
        description="Post the careers embed in #careers.",
    )
    @app_commands.default_permissions(administrator=True)
    async def post_careers(self, interaction: discord.Interaction):
        if interaction.guild_id != COMMUNITY_GUILD_ID:
            await interaction.response.send_message(MESSAGES["wrong_guild"], ephemeral=True)
            return
        channel = self.bot.get_channel(CAREERS_CHANNEL_ID)
        if channel is None:
            await interaction.response.send_message(MESSAGES["careers_channel_missing"], ephemeral=True)
            return

        async for msg in channel.history(limit=20):
            if msg.author.id == interaction.guild.me.id and msg.embeds:
                for embed in msg.embeds:
                    if embed.title and "Careers" in embed.title:
                        await interaction.response.send_message(MESSAGES["careers_exists"], ephemeral=True)
                        return

        await channel.send(embed=build_careers_embed(), view=CareersView())
        await interaction.response.send_message(MESSAGES["careers_posted"], ephemeral=True)

    @app_commands.command(
        name="appreview",
        description="Open the application review form (Owner + Studio Director only).",
    )
    async def appreview(self, interaction: discord.Interaction):
        if not _is_authorized(interaction):
            await interaction.response.send_message(MESSAGES["not_authorised"], ephemeral=True)
            return

        await interaction.response.send_modal(ReviewModal())


async def setup(bot: commands.Bot):
    await bot.add_cog(CareersCog(bot))
