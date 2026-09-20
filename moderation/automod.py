from __future__ import annotations

from datetime import datetime, timezone

import discord
from discord import app_commands
from discord.ext import commands

from core.scope import get_guild_scope, reject_wrong_scope, SCOPE_COMMUNITY

from .moderation_config import AUTOMOD_CHANNEL_ID, AUTOMOD_MESSAGES
from .moderation_embeds import BLUE, DARK_RED, GREEN, ORANGE, PURPLE, RED, YELLOW, base_embed, success_embed, error_embed
from .moderation_utils import deny
from .moderation_utils import audit_actor

VALID_SCOPES = {SCOPE_COMMUNITY}


class AutoModCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _auto_channel(self, guild: discord.Guild) -> discord.TextChannel | None:
        channel = guild.get_channel(AUTOMOD_CHANNEL_ID)
        if isinstance(channel, discord.TextChannel):
            return channel
        return None

    async def cog_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError) -> None:
        if isinstance(error, app_commands.CommandInvokeError):
            original = error.original
        else:
            original = error
        message = AUTOMOD_MESSAGES["generic"]
        if isinstance(original, discord.Forbidden):
            message = AUTOMOD_MESSAGES["forbidden"]
        elif isinstance(original, discord.NotFound):
            message = AUTOMOD_MESSAGES["not_found"]
        elif isinstance(original, discord.HTTPException):
            message = AUTOMOD_MESSAGES["http"]

        embed = error_embed("AutoMod Error", message)
        if interaction.response.is_done():
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message(embed=embed, ephemeral=True)

    async def _scope_ok(self, interaction: discord.Interaction) -> bool:
        if interaction.guild is None or not isinstance(interaction.user, discord.Member):
            await deny(interaction, "Server Only", AUTOMOD_MESSAGES["server_only"])
            return False
        if get_guild_scope(interaction.guild_id) not in VALID_SCOPES:
            await reject_wrong_scope(interaction)
            return False
        return True

    async def _require_admin(self, interaction: discord.Interaction) -> bool:
        if not await self._scope_ok(interaction):
            return False
        from core.bot_config import LEAD_ROLE_IDS, LEAD_ROLE_NAMES, OWNER_ID
        member = interaction.user
        if member.id == OWNER_ID or member.guild_permissions.administrator:
            return True
        has_lead = any(role.id in LEAD_ROLE_IDS or role.name in LEAD_ROLE_NAMES for role in member.roles)
        if has_lead:
            return True
        await deny(interaction, "Access Denied", AUTOMOD_MESSAGES["access_denied"])
        return False

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if before.author.bot:
            return
        if before.content == after.content:
            return
        if not after.guild:
            return
        if get_guild_scope(after.guild.id) not in VALID_SCOPES:
            return
        channel = await self._auto_channel(after.guild)
        if not channel:
            return
        embed = base_embed("Message Edited", BLUE)
        embed.add_field(name="User", value=before.author.mention, inline=True)
        embed.add_field(name="Channel", value=after.channel.mention, inline=True)
        embed.add_field(name="Before", value=(before.content or "")[:1024] or "*empty*", inline=False)
        embed.add_field(name="After", value=(after.content or "")[:1024] or "*empty*", inline=False)
        embed.add_field(name="Jump", value=f"[Go to message]({after.jump_url})", inline=False)
        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if message.author.bot:
            return
        if not message.guild:
            return
        if get_guild_scope(message.guild.id) not in VALID_SCOPES:
            return
        channel = await self._auto_channel(message.guild)
        if not channel:
            return
        embed = base_embed("Message Deleted", DARK_RED)
        embed.add_field(name="User", value=message.author.mention, inline=True)
        embed.add_field(name="Channel", value=message.channel.mention, inline=True)
        embed.add_field(name="Content", value=(message.content or "")[:1024] or "*empty*", inline=False)
        if message.attachments:
            embed.add_field(name="Attachments", value=", ".join(a.url for a in message.attachments), inline=False)
        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        if get_guild_scope(after.guild.id) not in VALID_SCOPES:
            return
        channel = await self._auto_channel(after.guild)
        if not channel:
            return

        if before.nick != after.nick:
            actor = await audit_actor(after.guild, discord.AuditLogAction.member_update, after.id)
            embed = base_embed("Nickname Changed", ORANGE)
            embed.add_field(name="Actor", value=actor, inline=True)
            embed.add_field(name="Target", value=after.mention, inline=True)
            embed.add_field(name="Before", value=before.nick or before.name, inline=False)
            embed.add_field(name="After", value=after.nick or after.name, inline=False)
            await channel.send(embed=embed)

        before_roles = {role.id for role in before.roles}
        after_roles = {role.id for role in after.roles}
        if before_roles != after_roles:
            actor = await audit_actor(after.guild, discord.AuditLogAction.member_role_update, after.id)
            added = after_roles - before_roles
            removed = before_roles - after_roles
            if added or removed:
                embed = base_embed("Role Change", PURPLE)
                embed.add_field(name="Actor", value=actor, inline=True)
                embed.add_field(name="Target", value=after.mention, inline=True)
                details = []
                if added:
                    details.append("Added: " + ", ".join(f"<@&{rid}>" for rid in added))
                if removed:
                    details.append("Removed: " + ", ".join(f"<@&{rid}>" for rid in removed))
                embed.add_field(name="Details", value="\n".join(details), inline=False)
                await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        if not member.guild:
            return
        if get_guild_scope(member.guild.id) not in VALID_SCOPES:
            return
        channel = await self._auto_channel(member.guild)
        if not channel:
            return
        if before.channel == after.channel:
            return
        if before.channel is None and after.channel is not None:
            action = "Voice Join"
            color = GREEN
            target_channel = after.channel
        elif before.channel is not None and after.channel is None:
            action = "Voice Leave"
            color = DARK_RED
            target_channel = before.channel
        else:
            action = "Voice Move"
            color = BLUE
            target_channel = after.channel
        embed = base_embed(action, color)
        embed.add_field(name="User", value=member.mention, inline=True)
        embed.add_field(name="Channel", value=target_channel.mention if target_channel else "N/A", inline=True)
        await channel.send(embed=embed)

    @app_commands.command(name="add_role", description="Add a role to a member.")
    @app_commands.describe(user="Member to give the role to", role="Role to add")
    async def add_role(self, interaction: discord.Interaction, user: discord.Member, role: discord.Role):
        if not await self._require_admin(interaction):
            return
        if role in user.roles:
            await deny(interaction, "Role Already Present", f"{user.mention} already has {role.mention}.")
            return
        if role >= interaction.guild.me.top_role:
            await deny(interaction, "Role Too High", "I cannot assign a role higher than or equal to my own.")
            return
        await interaction.response.defer(ephemeral=True)
        await user.add_roles(role, reason=f"Added by {interaction.user}")
        mod_channel = await self._auto_channel(interaction.guild)
        if mod_channel:
            embed = base_embed("Role Added", GREEN)
            embed.add_field(name="Actor", value=interaction.user.mention, inline=True)
            embed.add_field(name="Target", value=user.mention, inline=True)
            embed.add_field(name="Role", value=role.mention, inline=True)
            await mod_channel.send(embed=embed)
        await interaction.followup.send(embed=success_embed("Success", f"Added {role.mention} to {user.mention}."), ephemeral=True)

    @app_commands.command(name="remove_role", description="Remove a role from a member.")
    @app_commands.describe(user="Member to remove the role from", role="Role to remove")
    async def remove_role(self, interaction: discord.Interaction, user: discord.Member, role: discord.Role):
        if not await self._require_admin(interaction):
            return
        if role not in user.roles:
            await deny(interaction, "Role Not Present", f"{user.mention} does not have {role.mention}.")
            return
        if role >= interaction.guild.me.top_role:
            await deny(interaction, "Role Too High", "I cannot remove a role higher than or equal to my own.")
            return
        await interaction.response.defer(ephemeral=True)
        await user.remove_roles(role, reason=f"Removed by {interaction.user}")
        mod_channel = await self._auto_channel(interaction.guild)
        if mod_channel:
            embed = base_embed("Role Removed", DARK_RED)
            embed.add_field(name="Actor", value=interaction.user.mention, inline=True)
            embed.add_field(name="Target", value=user.mention, inline=True)
            embed.add_field(name="Role", value=role.mention, inline=True)
            await mod_channel.send(embed=embed)
        await interaction.followup.send(embed=success_embed("Success", f"Removed {role.mention} from {user.mention}."), ephemeral=True)


async def setup(bot: commands.Bot):
    from core.bot_config import COMMUNITY_GUILD_ID

    await bot.add_cog(AutoModCog(bot), guild=discord.Object(id=COMMUNITY_GUILD_ID))
