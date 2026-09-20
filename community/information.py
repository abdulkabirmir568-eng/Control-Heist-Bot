import discord
from discord import app_commands
from discord.ext import commands

from core.scope import get_guild_scope, SCOPE_COMMUNITY, reject_wrong_scope
from .information_config import (
    FAQ,
    INFORMATION_CHANNEL_ID,
    INFO_COLOR,
    INFO_FOOTER,
    INFO_PAGES,
    INFO_PANEL_DESCRIPTION,
    INFO_SELECT_OPTIONS,
    INFO_SELECT_PLACEHOLDER,
    INFO_TITLE_FORMAT,
    MESSAGES,
    OWNER_ID,
    ROLES,
    SOCIALS,
    STUDIO_INFO_FIELDS,
)


def _info_embed(title: str, description: str) -> discord.Embed:
    embed = discord.Embed(
        title=INFO_TITLE_FORMAT.format(title),
        description=description,
        color=INFO_COLOR,
    )
    embed.set_footer(text=INFO_FOOTER)
    return embed


def _studio_info_embed() -> discord.Embed:
    description = "\n\n".join(f"**{label}:** {value}" for label, value in STUDIO_INFO_FIELDS)
    return _info_embed("Studio Information", description)


def _faq_embed(question: str, answer: str) -> discord.Embed:
    return _info_embed("FAQ", f"**Q: {question}**\n\nA: {answer}")


def _roles_embed(role_name: str, description: str) -> discord.Embed:
    return _info_embed("Roles", f"**{role_name}**\n\n{description}")


def _socials_embed() -> discord.Embed:
    lines = [f"**{platform}:** {link}" for platform, link in SOCIALS.items() if link]
    description = "\n\n".join(lines) if lines else MESSAGES["socials_empty"]
    return _info_embed("Socials", description)


class InformationSelect(discord.ui.Select):
    def __init__(self) -> None:
        options = [
            discord.SelectOption(label=label, value=value, description=description)
            for label, value, description in INFO_SELECT_OPTIONS
        ]
        super().__init__(
            placeholder=INFO_SELECT_PLACEHOLDER,
            min_values=1,
            max_values=1,
            options=options,
            custom_id="information_select",
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        if get_guild_scope(interaction.guild_id) != SCOPE_COMMUNITY:
            await reject_wrong_scope(interaction)
            return

        key = self.values[0]

        if key == "studio_info":
            await interaction.response.send_message(embed=_studio_info_embed(), ephemeral=True)

        elif key in INFO_PAGES:
            title, description = INFO_PAGES[key]
            await interaction.response.send_message(embed=_info_embed(title, description), ephemeral=True)

        elif key == "faq":
            options = [
                discord.SelectOption(label=question[:100], value=question[:100])
                for question in FAQ.keys()
            ]
            if not options:
                await interaction.response.send_message(MESSAGES["faq_empty"], ephemeral=True)
                return

            view = discord.ui.View(timeout=None)
            select = discord.ui.Select(
                placeholder=MESSAGES["faq_placeholder"],
                min_values=1,
                max_values=1,
                options=options,
                custom_id="faq_select",
            )

            async def faq_callback(inter: discord.Interaction):
                selected = inter.data["values"][0]
                answer = FAQ.get(selected, MESSAGES["faq_no_answer"])
                await inter.response.send_message(embed=_faq_embed(selected, answer), ephemeral=True)

            select.callback = faq_callback
            view.add_item(select)
            await interaction.response.send_message(MESSAGES["faq_prompt"], view=view, ephemeral=True)

        elif key == "roles":
            options = [
                discord.SelectOption(label=role_name[:100], value=role_name[:100])
                for role_name in ROLES.keys()
            ]
            if not options:
                await interaction.response.send_message(MESSAGES["roles_empty"], ephemeral=True)
                return

            view = discord.ui.View(timeout=None)
            select = discord.ui.Select(
                placeholder=MESSAGES["roles_placeholder"],
                min_values=1,
                max_values=1,
                options=options,
                custom_id="roles_select",
            )

            async def role_callback(inter: discord.Interaction):
                selected = inter.data["values"][0]
                description = ROLES.get(selected, MESSAGES["roles_no_description"])
                await inter.response.send_message(embed=_roles_embed(selected, description), ephemeral=True)

            select.callback = role_callback
            view.add_item(select)
            await interaction.response.send_message(MESSAGES["roles_prompt"], view=view, ephemeral=True)

        elif key == "socials":
            await interaction.response.send_message(embed=_socials_embed(), ephemeral=True)


class InformationView(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=None)
        self.add_item(InformationSelect())


class InformationCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.bot.add_view(InformationView())

    @app_commands.command(
        name="infopanel",
        description="Post the information panel (wipes the channel first)",
    )
    async def infopanel(self, interaction: discord.Interaction) -> None:
        if get_guild_scope(interaction.guild_id) != SCOPE_COMMUNITY:
            await reject_wrong_scope(interaction)
            return
        if interaction.user.id != OWNER_ID:
            return await interaction.response.send_message(MESSAGES["owner_only"], ephemeral=True)

        channel = interaction.guild.get_channel(INFORMATION_CHANNEL_ID)
        if not channel:
            return await interaction.response.send_message(MESSAGES["channel_missing"], ephemeral=True)

        await interaction.response.defer(ephemeral=True)
        await channel.purge(limit=100)

        embed = discord.Embed(description=INFO_PANEL_DESCRIPTION, color=INFO_COLOR)
        embed.set_footer(text=INFO_FOOTER)

        await channel.send(embed=embed, view=InformationView())
        await interaction.followup.send(MESSAGES["panel_posted"], ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    from core.bot_config import COMMUNITY_GUILD_ID

    await bot.add_cog(InformationCog(bot), guild=discord.Object(id=COMMUNITY_GUILD_ID))
