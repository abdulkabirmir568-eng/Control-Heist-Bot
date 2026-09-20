import discord
from discord import app_commands
from discord.ext import commands

from core.scope import get_guild_scope, SCOPE_COMMUNITY, reject_wrong_scope
from core.bot_config import OWNER_ID
from rules.rules_config import (
    MESSAGES,
    RULES,
    RULES_CHANNEL_ID,
    RULES_COLOR,
    RULES_FOOTER,
    RULES_PANEL_DESCRIPTION,
    RULES_PANEL_FOOTER,
    RULES_SELECT_OPTIONS,
    RULES_SELECT_PLACEHOLDER,
)


class RulesSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label=label, value=value, description=description)
            for label, value, description in RULES_SELECT_OPTIONS
        ]
        super().__init__(
            placeholder=RULES_SELECT_PLACEHOLDER,
            min_values=1,
            max_values=1,
            options=options,
            custom_id="rules_select"
        )

    async def callback(self, interaction: discord.Interaction):
        if get_guild_scope(interaction.guild_id) != SCOPE_COMMUNITY:
            await reject_wrong_scope(interaction)
            return

        key = self.values[0]
        title, content = RULES[key]

        embed = discord.Embed(
            title=title,
            description=content,
            color=RULES_COLOR,
        )
        embed.set_footer(text=RULES_FOOTER)
        await interaction.response.send_message(embed=embed, ephemeral=True)


class RulesView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(RulesSelect())


class RulesCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.bot.add_view(RulesView())

    @app_commands.command(
        name="rulespanel",
        description="Post the rules panel (wipes the channel first)"
    )
    async def rulespanel(self, interaction: discord.Interaction):
        if get_guild_scope(interaction.guild_id) != SCOPE_COMMUNITY:
            await reject_wrong_scope(interaction)
            return
        if interaction.user.id != OWNER_ID:
            return await interaction.response.send_message(
                MESSAGES["owner_only"], ephemeral=True
            )

        channel = interaction.guild.get_channel(RULES_CHANNEL_ID)
        if not channel:
            return await interaction.response.send_message(
                MESSAGES["channel_missing"],
                ephemeral=True
            )

        await interaction.response.defer(ephemeral=True)
        await channel.purge(limit=100)

        embed = discord.Embed(description=RULES_PANEL_DESCRIPTION, color=RULES_COLOR)
        embed.set_footer(text=RULES_PANEL_FOOTER)

        await channel.send(embed=embed, view=RulesView())
        await interaction.followup.send(MESSAGES["panel_posted"], ephemeral=True)


async def setup(bot: commands.Bot):
    from core.bot_config import COMMUNITY_GUILD_ID

    await bot.add_cog(RulesCog(bot), guild=discord.Object(id=COMMUNITY_GUILD_ID))