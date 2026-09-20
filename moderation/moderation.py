from __future__ import annotations

import asyncio
from datetime import datetime, timezone

import discord
from discord import app_commands
from discord.ext import commands, tasks

from core.scope import get_guild_scope, reject_wrong_scope, SCOPE_COMMUNITY

from .moderation_config import (
    CASE_PAGE_FOOTER,
    CASE_PAGE_SIZE,
    DATABASE_PATH,
    HISTORY_PAGE_SIZE,
    MAX_TIMEOUT_DAYS,
    MODERATION_MESSAGES,
)
from .moderation_database import CaseRecord, ModerationDatabase, NoteRecord, WarningRecord, utc_now_iso
from .moderation_embeds import (
    BLUE,
    DARK_RED,
    GREEN,
    ORANGE,
    RED,
    YELLOW,
    action_embed,
    dm_notice,
    error_embed,
    info_embed,
    success_embed,
    unban_notice,
)
from .moderation_logging import ModerationLogger, audit_event_embed
from .moderation_utils import can_moderate, deny, format_duration, has_mod_permission, parse_duration
from .moderation_views import PagedEmbedView


VALID_SCOPES = {SCOPE_COMMUNITY}
URL_MARKERS = ("http://", "https://", "discord.gg/", "www.")


def _case_number(value: str) -> int | None:
    cleaned = value.upper().replace("CASE-", "").strip()
    return int(cleaned) if cleaned.isdigit() else None


def _warning_number(value: str) -> int | None:
    cleaned = value.upper().replace("HC-WARN-", "").strip()
    return int(cleaned) if cleaned.isdigit() else None


def _unix(iso_value: str | None) -> str:
    if not iso_value:
        return "N/A"
    try:
        dt = datetime.fromisoformat(iso_value)
    except ValueError:
        return iso_value
    return f"<t:{int(dt.timestamp())}:F>"


class ModerationCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = ModerationDatabase(DATABASE_PATH)
        self.logger = ModerationLogger(self.db)

    async def cog_load(self) -> None:
        self.tempban_worker.start()

    async def cog_unload(self) -> None:
        self.tempban_worker.cancel()

    async def cog_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError) -> None:
        if isinstance(error, app_commands.CommandInvokeError):
            original = error.original
        else:
            original = error
        if isinstance(original, discord.Forbidden):
            message = MODERATION_MESSAGES["forbidden"]
        elif isinstance(original, discord.NotFound):
            message = MODERATION_MESSAGES["not_found"]
        elif isinstance(original, discord.HTTPException):
            message = MODERATION_MESSAGES["http"]
        else:
            message = MODERATION_MESSAGES["generic"]
        embed = error_embed("Moderation Error", message)
        if interaction.response.is_done():
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message(embed=embed, ephemeral=True)

    async def _scope_ok(self, interaction: discord.Interaction) -> bool:
        if interaction.guild is None or not isinstance(interaction.user, discord.Member):
            await deny(interaction, "Server Only", MODERATION_MESSAGES["server_only"])
            return False
        if get_guild_scope(interaction.guild_id) not in VALID_SCOPES:
            await reject_wrong_scope(interaction)
            return False
        return True

    async def _require(self, interaction: discord.Interaction, permission: str) -> bool:
        if not await self._scope_ok(interaction):
            return False
        if not has_mod_permission(interaction.user, permission):
            await deny(interaction, "Access Denied", MODERATION_MESSAGES["access_denied"])
            return False
        return True

    async def _dm(self, target: discord.abc.User, *, action: str, reason: str, moderator: discord.Member, case_id: str | None = None) -> bool:
        try:
            embed = dm_notice(action=action, reason=reason, moderator=moderator)
            if case_id:
                embed.add_field(name="Case ID", value=case_id, inline=True)
            await target.send(embed=embed)
            return True
        except discord.HTTPException:
            return False

    async def _log_action(self, guild: discord.Guild, embed: discord.Embed) -> None:
        await self.logger.log(guild, embed)

    async def _create_action_case(
        self,
        interaction: discord.Interaction,
        *,
        action: str,
        target_id: int,
        reason: str,
        expires_at: str | None = None,
    ) -> CaseRecord:
        return await self.db.create_case(
            guild_id=interaction.guild.id,
            action_type=action,
            target_id=target_id,
            moderator_id=interaction.user.id,
            reason=reason,
            expires_at=expires_at,
        )

    def _target_ok(self, interaction: discord.Interaction, target: discord.Member) -> bool:
        ok, message = can_moderate(interaction.user, target, bot_member=interaction.guild.me)
        return ok

    async def _deny_target_if_needed(self, interaction: discord.Interaction, target: discord.Member) -> bool:
        ok, message = can_moderate(interaction.user, target, bot_member=interaction.guild.me)
        if not ok:
            await deny(interaction, "Action Blocked", message)
            return True
        return False

    def _cases_embeds(self, title: str, cases: list[CaseRecord]) -> list[discord.Embed]:
        if not cases:
            return [info_embed(title, "No cases found.")]
        embeds: list[discord.Embed] = []
        for index in range(0, len(cases), CASE_PAGE_SIZE):
            chunk = cases[index:index + CASE_PAGE_SIZE]
            embed = info_embed(title, "")
            for case in chunk:
                status = "Active" if case.active else "Closed"
                embed.add_field(
                    name=f"{case.case_id} - {case.action_type}",
                    value=(
                        f"Target: <@{case.target_id}> (`{case.target_id}`)\n"
                        f"Moderator: <@{case.moderator_id}>\n"
                        f"Reason: {case.reason}\n"
                        f"Date: {_unix(case.created_at)}\n"
                        f"Status: {status}"
                    )[:1024],
                    inline=False,
                )
            embed.set_footer(text=CASE_PAGE_FOOTER.format(page=len(embeds) + 1))
            embeds.append(embed)
        return embeds

    def _warnings_embeds(self, user: discord.abc.User | discord.Member, warnings: list[WarningRecord]) -> list[discord.Embed]:
        if not warnings:
            return [success_embed("Warnings", f"{user.mention} has no active warnings.")]
        embeds: list[discord.Embed] = []
        for index in range(0, len(warnings), HISTORY_PAGE_SIZE):
            embed = info_embed("Warning History", f"Warnings for {user.mention}")
            for warning in warnings[index:index + HISTORY_PAGE_SIZE]:
                embed.add_field(
                    name=warning.warning_id,
                    value=(
                        f"Reason: {warning.reason}\n"
                        f"Moderator: <@{warning.moderator_id}>\n"
                        f"Date: {_unix(warning.created_at)}\n"
                        f"Case: CASE-{warning.case_id:04d}"
                    )[:1024],
                    inline=False,
                )
            embeds.append(embed)
        return embeds

    @app_commands.command(name="ban", description="Ban a member with a logged moderation case.")
    @app_commands.describe(user="Member to ban", reason="Reason for the ban", delete_days="Days of messages to delete, 0-7")
    async def ban(self, interaction: discord.Interaction, user: discord.Member, reason: str, delete_days: app_commands.Range[int, 0, 7] = 0):
        if not await self._require(interaction, "ban_members") or await self._deny_target_if_needed(interaction, user):
            return
        await interaction.response.defer(ephemeral=True)
        case = await self._create_action_case(interaction, action="BAN", target_id=user.id, reason=reason)
        dm_sent = await self._dm(user, action="Ban", reason=reason, moderator=interaction.user, case_id=case.case_id)
        await interaction.guild.ban(user, reason=f"{case.case_id} by {interaction.user}: {reason}", delete_message_days=delete_days)
        embed = action_embed(
            action="BAN",
            target=user,
            moderator=interaction.user,
            reason=reason,
            case_id=case.case_id,
            color=DARK_RED,
            extra=[("DM Status", "Delivered" if dm_sent else "Failed - action continued", True)],
        )
        await self._log_action(interaction.guild, embed)
        await interaction.followup.send(embed=embed, ephemeral=True)

    async def tempban(self, interaction: discord.Interaction, user: discord.Member, duration: str, reason: str):
        if not await self._require(interaction, "ban_members") or await self._deny_target_if_needed(interaction, user):
            return
        delta = parse_duration(duration)
        if delta is None:
            await deny(interaction, "Invalid Duration", "Use a duration like `7d`, `12h`, or `30m`.")
            return
        await interaction.response.defer(ephemeral=True)
        expires_at = (datetime.now(timezone.utc) + delta).isoformat()
        case = await self._create_action_case(interaction, action="TEMPBAN", target_id=user.id, reason=reason, expires_at=expires_at)
        dm_sent = await self._dm(user, action=f"Tempban ({format_duration(delta)})", reason=reason, moderator=interaction.user)
        await interaction.guild.ban(user, reason=f"{case.case_id} by {interaction.user}: {reason}", delete_message_days=0)
        embed = action_embed(
            action="TEMPBAN",
            target=user,
            moderator=interaction.user,
            reason=reason,
            case_id=case.case_id,
            color=RED,
            extra=[("Expires", _unix(expires_at), True), ("DM Status", "Delivered" if dm_sent else "Failed - action continued", True)],
        )
        await self._log_action(interaction.guild, embed)
        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="unban", description="Unban a user by ID.")
    @app_commands.describe(user_id="The banned user's Discord ID", reason="Reason for the unban")
    async def unban(self, interaction: discord.Interaction, user_id: str, reason: str):
        if not await self._require(interaction, "ban_members"):
            return
        if not user_id.isdigit():
            await deny(interaction, "Invalid User ID", "Provide a numeric Discord user ID.")
            return
        await interaction.response.defer(ephemeral=True)
        target_id = int(user_id)
        user = await self.bot.fetch_user(target_id)
        await interaction.guild.unban(user, reason=f"Unbanned by {interaction.user}: {reason}")
        case = await self._create_action_case(interaction, action="UNBAN", target_id=target_id, reason=reason)
        try:
            await user.send(embed=unban_notice(moderator=interaction.user))
        except discord.HTTPException:
            pass
        embed = action_embed(action="UNBAN", target=target_id, moderator=interaction.user, reason=reason, case_id=case.case_id, color=GREEN)
        await self._log_action(interaction.guild, embed)
        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="kick", description="Kick a member with a logged moderation case.")
    @app_commands.describe(user="Member to kick", reason="Reason for the kick")
    async def kick(self, interaction: discord.Interaction, user: discord.Member, reason: str):
        if not await self._require(interaction, "kick_members") or await self._deny_target_if_needed(interaction, user):
            return
        await interaction.response.defer(ephemeral=True)
        case = await self._create_action_case(interaction, action="KICK", target_id=user.id, reason=reason)
        dm_sent = await self._dm(user, action="Kick", reason=reason, moderator=interaction.user)
        await user.kick(reason=f"{case.case_id} by {interaction.user}: {reason}")
        embed = action_embed(
            action="KICK",
            target=user,
            moderator=interaction.user,
            reason=reason,
            case_id=case.case_id,
            color=RED,
            extra=[("DM Status", "Delivered" if dm_sent else "Failed - action continued", True)],
        )
        await self._log_action(interaction.guild, embed)
        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="timeout", description="Timeout a member.")
    @app_commands.describe(user="Member to timeout", duration="Duration such as 1h, 2d, 30m", reason="Reason for the timeout")
    async def timeout(self, interaction: discord.Interaction, user: discord.Member, duration: str, reason: str):
        if not await self._require(interaction, "moderate_members") or await self._deny_target_if_needed(interaction, user):
            return
        delta = parse_duration(duration)
        if delta is None or delta.total_seconds() > MAX_TIMEOUT_DAYS * 86400:
            await deny(interaction, "Invalid Duration", MODERATION_MESSAGES["invalid_timeout"].format(days=MAX_TIMEOUT_DAYS))
            return
        await interaction.response.defer(ephemeral=True)
        until = datetime.now(timezone.utc) + delta
        case = await self._create_action_case(interaction, action="TIMEOUT", target_id=user.id, reason=reason, expires_at=until.isoformat())
        dm_sent = await self._dm(user, action=f"Timeout ({format_duration(delta)})", reason=reason, moderator=interaction.user)
        await user.timeout(until, reason=f"{case.case_id} by {interaction.user}: {reason}")
        embed = action_embed(
            action="TIMEOUT",
            target=user,
            moderator=interaction.user,
            reason=reason,
            case_id=case.case_id,
            color=ORANGE,
            extra=[("Expires", _unix(until.isoformat()), True), ("DM Status", "Delivered" if dm_sent else "Failed - action continued", True)],
        )
        await self._log_action(interaction.guild, embed)
        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="untimeout", description="Remove a member timeout.")
    @app_commands.describe(user="Member to remove timeout from", reason="Reason for removing the timeout")
    async def untimeout(self, interaction: discord.Interaction, user: discord.Member, reason: str):
        if not await self._require(interaction, "moderate_members") or await self._deny_target_if_needed(interaction, user):
            return
        await interaction.response.defer(ephemeral=True)
        await user.timeout(None, reason=f"Untimeout by {interaction.user}: {reason}")
        case = await self._create_action_case(interaction, action="UNTIMEOUT", target_id=user.id, reason=reason)
        embed = action_embed(action="UNTIMEOUT", target=user, moderator=interaction.user, reason=reason, case_id=case.case_id, color=GREEN)
        await self._log_action(interaction.guild, embed)
        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="warn", description="Warn a member and permanently store the warning.")
    @app_commands.describe(user="Member to warn", reason="Reason for the warning")
    async def warn(self, interaction: discord.Interaction, user: discord.Member, reason: str):
        if not await self._require(interaction, "moderate_members") or await self._deny_target_if_needed(interaction, user):
            return
        await interaction.response.defer(ephemeral=True)
        case = await self._create_action_case(interaction, action="WARN", target_id=user.id, reason=reason)
        warning = await self.db.add_warning(case_id=case.id, guild_id=interaction.guild.id, user_id=user.id, moderator_id=interaction.user.id, reason=reason)
        dm_sent = await self._dm(user, action="Warn", reason=reason, moderator=interaction.user)
        embed = action_embed(
            action="WARN",
            target=user,
            moderator=interaction.user,
            reason=reason,
            case_id=case.case_id,
            color=YELLOW,
            extra=[("Warning ID", warning.warning_id, True), ("DM Status", "Delivered" if dm_sent else "Failed - action continued", True)],
        )
        await self._log_action(interaction.guild, embed)
        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="warnings", description="View active warnings for a member.")
    async def warnings(self, interaction: discord.Interaction, user: discord.Member):
        if not await self._require(interaction, "moderate_members"):
            return
        warnings = await self.db.list_warnings(interaction.guild.id, user.id)
        embeds = self._warnings_embeds(user, warnings)
        await interaction.response.send_message(embed=embeds[0], view=PagedEmbedView(embeds, interaction.user.id), ephemeral=True)

    async def clearwarn(self, interaction: discord.Interaction, user: discord.Member, reason: str):
        if not await self._require(interaction, "moderate_members"):
            return
        count = await self.db.clear_warnings(interaction.guild.id, user.id)
        case = await self._create_action_case(interaction, action="CLEARWARN", target_id=user.id, reason=reason)
        embed = action_embed(action="CLEARWARN", target=user, moderator=interaction.user, reason=reason, case_id=case.case_id, color=GREEN, extra=[("Warnings Cleared", str(count), True)])
        await self._log_action(interaction.guild, embed)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def remove_warning(self, interaction: discord.Interaction, warning_id: str, reason: str):
        if not await self._require(interaction, "moderate_members"):
            return
        parsed = _warning_number(warning_id)
        if parsed is None:
            await deny(interaction, "Invalid Warning ID", "Use an ID like `HC-WARN-0001`.")
            return
        warning = await self.db.remove_warning(parsed)
        if warning is None or warning.guild_id != interaction.guild.id:
            await deny(interaction, "Warning Not Found", "No warning with that ID exists in this server.")
            return
        case = await self._create_action_case(interaction, action="REMOVE_WARNING", target_id=warning.user_id, reason=reason)
        embed = action_embed(action="REMOVE_WARNING", target=warning.user_id, moderator=interaction.user, reason=reason, case_id=case.case_id, color=GREEN, extra=[("Warning ID", warning.warning_id, True)])
        await self._log_action(interaction.guild, embed)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="history", description="View a member's moderation history.")
    async def history(self, interaction: discord.Interaction, user: discord.Member):
        if not await self._require(interaction, "moderate_members"):
            return
        cases = await self.db.list_cases(interaction.guild.id, user.id, limit=25)
        warnings = await self.db.list_warnings(interaction.guild.id, user.id, active_only=False)
        embed = info_embed("User History", f"Moderation history for {user.mention}")
        totals: dict[str, int] = {}
        for case in cases:
            totals[case.action_type] = totals.get(case.action_type, 0) + 1
        embed.add_field(name="Total Cases", value=str(len(cases)), inline=True)
        embed.add_field(name="Warnings", value=str(len(warnings)), inline=True)
        embed.add_field(name="Action Summary", value="\n".join(f"{k}: {v}" for k, v in sorted(totals.items())) or "No actions recorded.", inline=False)
        recent = "\n".join(f"{case.case_id} - {case.action_type} - {_unix(case.created_at)}" for case in cases[:8]) or "No recent cases."
        embed.add_field(name="Recent Cases", value=recent[:1024], inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def case_command(self, interaction: discord.Interaction, case_id: str):
        if not await self._require(interaction, "moderate_members"):
            return
        parsed = _case_number(case_id)
        case = await self.db.get_case(parsed) if parsed is not None else None
        if case is None or case.guild_id != interaction.guild.id:
            await deny(interaction, "Case Not Found", "No case with that ID exists in this server.")
            return
        embed = action_embed(
            action=case.action_type,
            target=case.target_id,
            moderator=case.moderator_id,
            reason=case.reason,
            case_id=case.case_id,
            extra=[("Created", _unix(case.created_at), True), ("Expires", _unix(case.expires_at), True), ("Status", "Active" if case.active else "Closed", True)],
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def cases(self, interaction: discord.Interaction, user: discord.Member | None = None):
        if not await self._require(interaction, "moderate_members"):
            return
        records = await self.db.list_cases(interaction.guild.id, user.id if user else None, limit=25)
        embeds = self._cases_embeds("Moderation Cases", records)
        await interaction.response.send_message(embed=embeds[0], view=PagedEmbedView(embeds, interaction.user.id), ephemeral=True)

    @app_commands.command(name="purge", description="Delete recent messages with optional filters.")
    @app_commands.describe(
        amount="Number of recent messages to scan",
        user="Only delete messages from this member",
        bots_only="Only delete bot messages",
        links_only="Only delete messages containing links",
        attachments_only="Only delete messages with attachments",
    )
    async def purge(
        self,
        interaction: discord.Interaction,
        amount: app_commands.Range[int, 1, 100],
        user: discord.Member | None = None,
        bots_only: bool = False,
        links_only: bool = False,
        attachments_only: bool = False,
    ):
        filters = []
        if user is not None:
            filters.append(("USER", lambda message: message.author.id == user.id))
        if bots_only:
            filters.append(("BOTS", lambda message: message.author.bot))
        if links_only:
            filters.append(("LINKS", lambda message: any(marker in (message.content or "").lower() for marker in URL_MARKERS)))
        if attachments_only:
            filters.append(("ATTACHMENTS", lambda message: bool(message.attachments)))

        def check(message: discord.Message) -> bool:
            return all(predicate(message) for _, predicate in filters) if filters else True

        action = "PURGE" if not filters else "PURGE_" + "_".join(name for name, _ in filters)
        await self._purge(interaction, amount, action, check, target=user)

    async def purge_user(self, interaction: discord.Interaction, user: discord.Member, amount: app_commands.Range[int, 1, 100]):
        await self._purge(interaction, amount, "PURGE_USER", lambda message: message.author.id == user.id, target=user)

    async def purge_bots(self, interaction: discord.Interaction, amount: app_commands.Range[int, 1, 100] = 50):
        await self._purge(interaction, amount, "PURGE_BOTS", lambda message: message.author.bot)

    async def purge_links(self, interaction: discord.Interaction, amount: app_commands.Range[int, 1, 100] = 50):
        await self._purge(interaction, amount, "PURGE_LINKS", lambda message: any(marker in (message.content or "").lower() for marker in URL_MARKERS))

    async def purge_images(self, interaction: discord.Interaction, amount: app_commands.Range[int, 1, 100] = 50):
        await self._purge(interaction, amount, "PURGE_IMAGES", lambda message: any((a.content_type or "").startswith("image/") for a in message.attachments))

    async def _purge(self, interaction: discord.Interaction, amount: int, action: str, check, target: discord.Member | None = None):
        if not await self._require(interaction, "manage_messages"):
            return
        if not isinstance(interaction.channel, discord.TextChannel):
            await deny(interaction, "Unsupported Channel", "Purges can only be used in text channels.")
            return
        await interaction.response.defer(ephemeral=True)
        deleted = await interaction.channel.purge(limit=amount, check=check, bulk=True, reason=f"{action} by {interaction.user}")
        case = await self._create_action_case(interaction, action="PURGE", target_id=target.id if target else interaction.channel.id, reason=f"{action}: {len(deleted)} messages deleted")
        embed = action_embed(
            action="PURGE",
            target=target.id if target else interaction.channel.id,
            moderator=interaction.user,
            reason=f"{action}: {len(deleted)} messages deleted in {interaction.channel.mention}",
            case_id=case.case_id,
            color=BLUE,
            extra=[("Messages Deleted", str(len(deleted)), True)],
        )
        await self._log_action(interaction.guild, embed)
        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="modstats", description="Open the moderation dashboard.")
    async def modstats(self, interaction: discord.Interaction):
        if not await self._require(interaction, "moderate_members"):
            return
        stats = await self.db.stats(interaction.guild.id)
        counts = stats["counts"]
        embed = info_embed("Moderator Dashboard", "Heist Control moderation overview")
        embed.add_field(name="Total Bans", value=str(counts.get("BAN", 0) + counts.get("TEMPBAN", 0)), inline=True)
        embed.add_field(name="Total Kicks", value=str(counts.get("KICK", 0)), inline=True)
        embed.add_field(name="Total Timeouts", value=str(counts.get("TIMEOUT", 0)), inline=True)
        embed.add_field(name="Total Warns", value=str(counts.get("WARN", 0)), inline=True)
        mods = "\n".join(f"<@{mod_id}> - {total} cases" for mod_id, total in stats["moderators"]) or "No moderator activity yet."
        embed.add_field(name="Most Active Moderators", value=mods, inline=False)
        recent = "\n".join(f"{case.case_id} - {case.action_type} - <@{case.target_id}>" for case in stats["recent"]) or "No recent cases."
        embed.add_field(name="Recent Cases", value=recent, inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @tasks.loop(minutes=1)
    async def tempban_worker(self):
        await self.bot.wait_until_ready()
        due = await self.db.active_tempbans_due(utc_now_iso())
        for case in due:
            guild = self.bot.get_guild(case.guild_id)
            if guild is None:
                continue
            try:
                user = await self.bot.fetch_user(case.target_id)
                await guild.unban(user, reason=f"{case.case_id} tempban expired")
                await self.db.close_case(case.id)
                embed = action_embed(
                    action="UNBAN",
                    target=case.target_id,
                    moderator="SYSTEM",
                    reason=f"Temporary ban expired for {case.case_id}.",
                    case_id=case.case_id,
                    color=GREEN,
                )
                await self._log_action(guild, embed)
            except discord.HTTPException:
                await asyncio.sleep(2)


async def setup(bot: commands.Bot):
    from core.bot_config import COMMUNITY_GUILD_ID

    await bot.add_cog(ModerationCog(bot), guild=discord.Object(id=COMMUNITY_GUILD_ID))
