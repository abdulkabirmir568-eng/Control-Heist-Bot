from __future__ import annotations

import asyncio
import re
from datetime import timedelta

import discord

from .moderation_embeds import error_embed

_DURATION_RE = re.compile(r"(?P<amount>\d+)\s*(?P<unit>w|week|weeks|d|day|days|h|hour|hours|m|min|minute|minutes|s|sec|second|seconds)", re.I)
_UNIT_SECONDS = {
    "w": 604800,
    "week": 604800,
    "weeks": 604800,
    "d": 86400,
    "day": 86400,
    "days": 86400,
    "h": 3600,
    "hour": 3600,
    "hours": 3600,
    "m": 60,
    "min": 60,
    "minute": 60,
    "minutes": 60,
    "s": 1,
    "sec": 1,
    "second": 1,
    "seconds": 1,
}


def parse_duration(value: str) -> timedelta | None:
    total = 0
    matched = False
    for match in _DURATION_RE.finditer(value or ""):
        matched = True
        total += int(match.group("amount")) * _UNIT_SECONDS[match.group("unit").lower()]
    if not matched or total <= 0:
        return None
    return timedelta(seconds=total)


def format_duration(delta: timedelta) -> str:
    seconds = int(delta.total_seconds())
    parts: list[str] = []
    for label, size in (("w", 604800), ("d", 86400), ("h", 3600), ("m", 60), ("s", 1)):
        amount, seconds = divmod(seconds, size)
        if amount:
            parts.append(f"{amount}{label}")
    return " ".join(parts) or "0s"


async def deny(interaction: discord.Interaction, title: str, message: str) -> None:
    embed = error_embed(title, message)
    if interaction.response.is_done():
        await interaction.followup.send(embed=embed, ephemeral=True)
    else:
        await interaction.response.send_message(embed=embed, ephemeral=True)


def can_moderate(
    moderator: discord.Member,
    target: discord.Member,
    *,
    bot_member: discord.Member | None = None,
) -> tuple[bool, str]:
    if moderator.id == target.id:
        return False, "You cannot moderate yourself."
    if target.bot:
        return False, "Bot accounts cannot be moderated with this command."
    if target.id == target.guild.owner_id:
        return False, "The server owner cannot be moderated."
    if moderator.guild.owner_id != moderator.id and target.top_role >= moderator.top_role:
        return False, "You cannot moderate a member with an equal or higher top role."
    if bot_member and target.top_role >= bot_member.top_role:
        return False, "My bot role is not high enough to moderate that member."
    return True, "OK"


def has_mod_permission(member: discord.Member, permission: str) -> bool:
    perms = member.guild_permissions
    return bool(getattr(perms, permission, False) or perms.administrator)


async def audit_actor(guild: discord.Guild, action: discord.AuditLogAction, target_id: int) -> str:
    if not guild.me or not guild.me.guild_permissions.view_audit_log:
        return "System or Unknown"
    try:
        async for entry in guild.audit_logs(limit=5, action=action):
            if getattr(entry.target, "id", None) == target_id:
                return f"{entry.user.mention} (`{entry.user.id}`)" if entry.user else "System or Unknown"
    except discord.HTTPException:
        return "System or Unknown"
    return "System or Unknown"