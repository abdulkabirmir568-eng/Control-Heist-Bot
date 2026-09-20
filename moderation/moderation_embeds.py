from __future__ import annotations

from datetime import datetime, timezone

import discord

from .moderation_config import (
    ACTION_COLORS,
    APPEAL_SERVER,
    BLUE,
    COMMUNITY_INVITE,
    DARK_RED,
    EMBED_FOOTER,
    GRAY,
    GREEN,
    ORANGE,
    PURPLE,
    RED,
    YELLOW,
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def user_line(user: discord.abc.User | discord.Member | int) -> str:
    if isinstance(user, int):
        return f"<@{user}> (`{user}`)"
    return f"{user.mention} (`{user.id}`)"


def base_embed(title: str, color: int, description: str | None = None) -> discord.Embed:
    embed = discord.Embed(
        title=title,
        description=description,
        color=color,
        timestamp=utc_now(),
    )
    embed.set_footer(text=EMBED_FOOTER)
    return embed


def action_embed(
    *,
    action: str,
    target: discord.abc.User | discord.Member | int,
    moderator: discord.abc.User | discord.Member | int | str,
    reason: str,
    case_id: str,
    color: int | None = None,
    extra: list[tuple[str, str, bool]] | None = None,
) -> discord.Embed:
    action_upper = action.upper()
    embed = base_embed(
        f"HEIST CONTROL - {action_upper}",
        color if color is not None else ACTION_COLORS.get(action_upper, BLUE),
    )
    embed.add_field(name="Action Type", value=action_upper, inline=True)
    embed.add_field(name="Target User", value=user_line(target), inline=True)
    if isinstance(moderator, str):
        moderator_value = moderator
    elif isinstance(moderator, int):
        moderator_value = f"<@{moderator}> (`{moderator}`)"
    else:
        moderator_value = f"{moderator.mention} (`{moderator.id}`)"
    embed.add_field(name="Moderator", value=moderator_value, inline=True)
    embed.add_field(name="Reason", value=reason[:1024], inline=False)
    embed.add_field(name="Case ID", value=case_id, inline=True)
    if extra:
        for name, value, inline in extra:
            embed.add_field(name=name, value=value[:1024], inline=inline)
    return embed


def dm_notice(
    *,
    action: str,
    reason: str,
    moderator: discord.abc.User | discord.Member,
) -> discord.Embed:
    color = DARK_RED if action.casefold().startswith("ban") else ACTION_COLORS.get(action.upper(), RED)
    embed = base_embed("HEIST CONTROL\nMODERATION UPDATE", color)
    embed.add_field(name="Action", value=action, inline=True)
    embed.add_field(name="Reason", value=reason[:1024], inline=False)
    embed.add_field(name="Moderator", value=f"{moderator} (`{moderator.id}`)", inline=True)
    embed.add_field(name="Date", value=f"<t:{int(utc_now().timestamp())}:F>", inline=False)
    embed.add_field(name="Appeal Server", value=APPEAL_SERVER, inline=False)
    return embed


def unban_notice(*, moderator: discord.abc.User | discord.Member) -> discord.Embed:
    embed = base_embed("HEIST CONTROL\nMODERATION UPDATE", GREEN)
    embed.add_field(name="Action", value="Unban", inline=True)
    embed.add_field(name="Moderator", value=f"{moderator} (`{moderator.id}`)", inline=True)
    embed.add_field(name="Date", value=f"<t:{int(utc_now().timestamp())}:F>", inline=False)
    embed.add_field(name="Status", value="Ban Removed", inline=True)
    embed.add_field(name="Community Invite", value=COMMUNITY_INVITE, inline=False)
    return embed


def success_embed(title: str, description: str) -> discord.Embed:
    return base_embed(title, GREEN, description)


def error_embed(title: str, description: str) -> discord.Embed:
    return base_embed(title, RED, description)


def info_embed(title: str, description: str) -> discord.Embed:
    return base_embed(title, BLUE, description)
