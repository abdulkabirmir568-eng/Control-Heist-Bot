from __future__ import annotations

import discord

from .bot_config import COMMUNITY_GUILD_ID, LEAD_ROLE_IDS, LEAD_ROLE_NAMES, OWNER_ID

SCOPE_COMMUNITY = "COMMUNITY"
SCOPE_INVALID = "INVALID"


def is_community_guild(guild_id: int | None) -> bool:
    return guild_id == COMMUNITY_GUILD_ID


def get_guild_scope(guild_id: int | None) -> str:
    if is_community_guild(guild_id):
        return SCOPE_COMMUNITY
    return SCOPE_INVALID


def scope_error_embed() -> discord.Embed:
    return discord.Embed(
        title="# __ENVIRONMENT LOCKED__",
        description="**** This command is not available in this environment.",
        color=0xFF6600,
    )


async def reject_wrong_scope(interaction: discord.Interaction) -> None:
    if interaction.response.is_done():
        await interaction.followup.send(embed=scope_error_embed(), ephemeral=True)
    else:
        await interaction.response.send_message(embed=scope_error_embed(), ephemeral=True)


def member_is_lead(member: discord.Member) -> bool:
    if member.id == OWNER_ID or member.guild_permissions.administrator:
        return True
    names = {name.casefold() for name in LEAD_ROLE_NAMES}
    return any(role.id in LEAD_ROLE_IDS or role.name.casefold() in names for role in member.roles)


async def require_scope(interaction: discord.Interaction, scope: str) -> bool:
    if get_guild_scope(interaction.guild_id) == scope:
        return True
    await reject_wrong_scope(interaction)
    return False


async def require_community(interaction: discord.Interaction) -> bool:
    return await require_scope(interaction, SCOPE_COMMUNITY)