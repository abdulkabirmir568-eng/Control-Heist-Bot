from __future__ import annotations

import discord

from .moderation_config import MOD_LOG_CHANNEL_ID, MOD_LOG_CHANNEL_NAME
from .moderation_database import ModerationDatabase
from .moderation_embeds import base_embed


class ModerationLogger:
    def __init__(self, database: ModerationDatabase):
        self.database = database

    async def get_log_channel(self, guild: discord.Guild) -> discord.TextChannel | None:
        configured = await self.database.get_setting(guild.id, "mod_log_channel_id")
        channel_id = int(configured) if configured and configured.isdigit() else MOD_LOG_CHANNEL_ID
        if channel_id:
            channel = guild.get_channel(channel_id)
            if isinstance(channel, discord.TextChannel):
                return channel

        existing = discord.utils.get(guild.text_channels, name=MOD_LOG_CHANNEL_NAME)
        if existing:
            await self.database.set_setting(guild.id, "mod_log_channel_id", str(existing.id))
            return existing

        me = guild.me
        if me and me.guild_permissions.manage_channels:
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(view_channel=False),
                me: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
            }
            for role in guild.roles:
                if role.permissions.manage_guild or role.permissions.administrator:
                    overwrites[role] = discord.PermissionOverwrite(view_channel=True, read_message_history=True)
            channel = await guild.create_text_channel(
                MOD_LOG_CHANNEL_NAME,
                overwrites=overwrites,
                reason="Heist Control moderation log channel setup",
            )
            await self.database.set_setting(guild.id, "mod_log_channel_id", str(channel.id))
            return channel
        return None

    async def log(self, guild: discord.Guild, embed: discord.Embed) -> None:
        channel = await self.get_log_channel(guild)
        if channel:
            await channel.send(embed=embed)


def audit_event_embed(title: str, event_type: str, actor: str, target: str, details: str, color: int = 0x3498DB) -> discord.Embed:
    embed = base_embed(title, color)
    embed.add_field(name="Event Type", value=event_type, inline=True)
    embed.add_field(name="Actor", value=actor, inline=True)
    embed.add_field(name="Target", value=target, inline=True)
    embed.add_field(name="Details", value=details[:1024], inline=False)
    return embed
