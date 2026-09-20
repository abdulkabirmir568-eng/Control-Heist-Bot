import asyncio
import discord
from discord import app_commands
from discord.ext import commands
import io
import time
from datetime import timezone
import re
from dataclasses import dataclass, field
from core.scope import require_community

from tickets.ticket_config import (
    BUG_REPORT_PANEL_CHANNEL_ID,
    BUG_REPORT_CATEGORY_ID,
    BUG_REPORT_LOG_CHANNEL_ID,
    BUG_REPORT_ROLE_IDS,
    BUG_REPORT_OWNER_ROLE_IDS,
    LEAD_DEVELOPER_ROLE_IDS,
    MODERATOR_REPORT_ROLE_IDS,
    QA_TEAM_ROLE_IDS,
    STUDIO_DIRECTOR_ROLE_IDS,
    TICKET_CATEGORY_ID,
    TICKET_PANEL_CHANNEL_ID,
    TICKET_LOG_CHANNEL_ID,
    STAFF_ROLE_IDS,
    SUPPORT_PING_IDS,
    ADMIN_PING_IDS,
    COOLDOWN_SECONDS,
    PANEL_ADMIN_ROLE_IDS,
    COLOR_RED,
    COLOR_BLUE,
    COLOR_ORANGE,
    COLOR_GREEN,
    SUPPORT_PANEL_COLOR,
    SUPPORT_PANEL_DESCRIPTION,
    SUPPORT_BUTTON_MEMBER_REPORT,
    SUPPORT_BUTTON_GENERAL_SUPPORT,
    SUPPORT_BUTTON_MODERATOR_REPORT,
    BUG_PANEL_COLOR,
    BUG_PANEL_FOOTER,
    BUG_PANEL_DESCRIPTION,
    BUG_BUTTON_BUG_REPORT,
    BUG_BUTTON_EXPLOIT_REPORT,
    BUG_CATEGORY_NAME,
    BUG_LOG_CHANNEL_NAME,
    BUG_PANEL_CHANNEL_NAME,
    TICKET_CONTROL_FOOTER,
    TICKET_WELCOME_FOOTER_LINE,
    TICKET_CLOSE_CONFIRM_TITLE,
    TICKET_CLOSE_CONFIRM_DESCRIPTION,
    TICKET_MODAL_FIELDS,
    TICKET_INSTRUCTIONS,
    DEFAULT_INSTRUCTION,
    MESSAGES,
)


_cooldowns: dict[int, float] = {}
_open_tickets: dict[int, int] = {}
_ticket_count: int = 0
_bug_count: int = 0
_exploit_count: int = 0

BUG_STATUS_OPEN = "OPEN"
BUG_STATUS_UNDER_REVIEW = "UNDER REVIEW"
BUG_STATUS_INVESTIGATING = "INVESTIGATING"
BUG_STATUS_AWAITING_USER = "AWAITING USER RESPONSE"
BUG_STATUS_FIX_IN_PROGRESS = "FIX IN PROGRESS"
BUG_STATUS_FIXED = "FIXED"
BUG_STATUS_CLOSED = "CLOSED"


@dataclass
class BugReportRecord:
    ticket_id: str
    report_type: str
    reporter_id: int
    channel_id: int
    title: str
    status: str = BUG_STATUS_OPEN
    priority: str = "NORMAL"
    staff_member_id: int | None = None
    status_history: list[str] = field(default_factory=list)


_bug_records: dict[int, BugReportRecord] = {}

def _next_ticket_number() -> int:
    global _ticket_count
    _ticket_count += 1
    return _ticket_count


def _next_bug_number(report_type: str) -> int:
    global _bug_count, _exploit_count
    if report_type == "Exploit Report":
        _exploit_count += 1
        return _exploit_count
    _bug_count += 1
    return _bug_count

def _is_staff(member: discord.Member) -> bool:
    return any(role.id in STAFF_ROLE_IDS for role in member.roles)

def _is_ticket_channel(channel: discord.TextChannel) -> bool:
    return channel.name.startswith(("ticket-", "bug-", "exploit-"))


def _bug_staff_role_ids() -> list[int]:
    role_ids: list[int] = []
    for group in (
        QA_TEAM_ROLE_IDS,
        LEAD_DEVELOPER_ROLE_IDS,
        STUDIO_DIRECTOR_ROLE_IDS,
        BUG_REPORT_OWNER_ROLE_IDS,
    ):
        for role_id in group:
            if role_id not in role_ids:
                role_ids.append(role_id)
    return role_ids


def _is_bug_staff(member: discord.Member) -> bool:
    allowed = set(_bug_staff_role_ids()) | set(STAFF_ROLE_IDS)
    return any(role.id in allowed for role in member.roles)


def _ticket_staff_role_ids(ticket_type: str) -> list[int]:
    if ticket_type == "Moderator Report":
        return MODERATOR_REPORT_ROLE_IDS
    if ticket_type == "Bug Report":
        return BUG_REPORT_ROLE_IDS
    return SUPPORT_PING_IDS


def _ticket_ping_role_ids(ticket_type: str) -> list[int]:
    if ticket_type in {"Member Report", "General Support"}:
        return SUPPORT_PING_IDS
    if ticket_type == "Moderator Report":
        return ADMIN_PING_IDS
    if ticket_type == "Bug Report":
        return BUG_REPORT_ROLE_IDS
    return []


def _clean_channel_part(value: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9-]+", "-", value.lower()).strip("-")
    return value[:40] or "ticket"


def _report_timestamp() -> str:
    return discord.utils.utcnow().strftime("%Y-%m-%d %H:%M UTC")


def _field_value(value: str | None) -> str:
    value = (value or "").strip()
    return value if value else MESSAGES["not_provided"]


async def _get_bug_category(guild: discord.Guild) -> discord.CategoryChannel | None:
    if BUG_REPORT_CATEGORY_ID:
        category = guild.get_channel(BUG_REPORT_CATEGORY_ID)
        if isinstance(category, discord.CategoryChannel):
            return category

    existing = discord.utils.get(guild.categories, name=BUG_CATEGORY_NAME)
    if existing:
        return existing

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
    }
    for role_id in _bug_staff_role_ids():
        role = guild.get_role(role_id)
        if role:
            overwrites[role] = discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
            )
    return await guild.create_category(name=BUG_CATEGORY_NAME, overwrites=overwrites)


async def _get_bug_log_channel(guild: discord.Guild) -> discord.TextChannel | None:
    if BUG_REPORT_LOG_CHANNEL_ID:
        channel = guild.get_channel(BUG_REPORT_LOG_CHANNEL_ID)
        if isinstance(channel, discord.TextChannel):
            return channel

    existing = discord.utils.get(guild.text_channels, name=BUG_LOG_CHANNEL_NAME)
    if existing:
        return existing

    category = await _get_bug_category(guild)
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
    }
    for role_id in _bug_staff_role_ids():
        role = guild.get_role(role_id)
        if role:
            overwrites[role] = discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
            )
    return await guild.create_text_channel(
        name=BUG_LOG_CHANNEL_NAME,
        category=category,
        overwrites=overwrites,
    )


async def _log_bug_event(
    guild: discord.Guild,
    title: str,
    record: BugReportRecord,
    actor: discord.abc.User | discord.Member,
    details: str,
    *,
    color: int = COLOR_BLUE,
    file: discord.File | None = None,
) -> None:
    log_channel = await _get_bug_log_channel(guild)
    if not log_channel:
        return

    embed = discord.Embed(
        title=title,
        description=details,
        color=color,
        timestamp=discord.utils.utcnow(),
    )
    embed.add_field(name="Ticket ID", value=record.ticket_id, inline=True)
    embed.add_field(name="Reporter", value=f"<@{record.reporter_id}>", inline=True)
    embed.add_field(name="Staff Member", value=f"<@{record.staff_member_id}>" if record.staff_member_id else "Unassigned", inline=True)
    embed.add_field(name="Status", value=record.status, inline=True)
    embed.add_field(name="Priority", value=record.priority, inline=True)
    embed.add_field(name="Actioned By", value=actor.mention, inline=True)
    if record.status_history:
        embed.add_field(
            name="Status History",
            value="\n".join(record.status_history[-8:]),
            inline=False,
        )
    embed.set_footer(text=BUG_PANEL_FOOTER)
    if file:
        await log_channel.send(embed=embed, file=file)
    else:
        await log_channel.send(embed=embed)


def _bug_panel_embed() -> discord.Embed:
    embed = discord.Embed(description=BUG_PANEL_DESCRIPTION, color=BUG_PANEL_COLOR)
    embed.set_footer(text=BUG_PANEL_FOOTER)
    return embed


async def _get_transcript_html(channel: discord.TextChannel, opener_id: int, reason: str, closed_by: discord.Member) -> str:
    messages = []
    async for msg in channel.history(oldest_first=True, limit=None):
        messages.append(msg)

    opened_at = messages[0].created_at.strftime("%Y-%m-%d %H:%M UTC") if messages else "Unknown"
    closed_at = messages[-1].created_at.strftime("%Y-%m-%d %H:%M UTC") if messages else "Unknown"

    rows = ""
    for msg in messages:
        if not msg.content and not msg.attachments and not msg.embeds:
            continue

        t        = msg.created_at.strftime("%Y-%m-%d %H:%M")
        is_bot   = msg.author.bot
        is_staff = isinstance(msg.author, discord.Member) and _is_staff(msg.author)
        role_tag = ""
        if is_bot:
            role_tag = '<span class="tag bot">BOT</span>'
        elif is_staff:
            role_tag = '<span class="tag staff">STAFF</span>'

        avatar_url = msg.author.display_avatar.url if msg.author.display_avatar else ""

        content = discord.utils.escape_mentions(msg.content or "")
        content = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', content)
        content = re.sub(r'\*(.+?)\*',     r'<em>\1</em>',         content)
        content = re.sub(r'`(.+?)`',       r'<code>\1</code>',     content)
        content = content.replace("\n", "<br>")

        attachments_html = ""
        for a in msg.attachments:
            if a.content_type and a.content_type.startswith("image"):
                attachments_html += f'<a href="{a.url}" target="_blank"><img src="{a.url}" class="attachment-img"></a>'
            else:
                attachments_html += f'<a href="{a.url}" class="attachment-link" target="_blank">📎 {a.filename}</a>'

        embeds_html = ""
        for e in msg.embeds:
            embed_title = f"<div class='embed-title'>{e.title}</div>" if e.title else ""
            embed_desc  = f"<div class='embed-desc'>{e.description}</div>" if e.description else ""
            color       = f"#{e.color.value:06x}" if e.color else "#4f545c"
            embeds_html += f"""
            <div class="embed" style="border-left: 4px solid {color};">
                {embed_title}
                {embed_desc}
            </div>"""

        rows += f"""
        <div class="message {'bot-msg' if is_bot else ''}">
            <img class="avatar" src="{avatar_url}" onerror="this.style.display='none'">
            <div class="message-body">
                <div class="message-header">
                    <span class="author">{msg.author.display_name}</span>
                    {role_tag}
                    <span class="timestamp">{t} UTC</span>
                </div>
                <div class="message-content">{content}</div>
                {attachments_html}
                {embeds_html}
            </div>
        </div>"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Transcript — {channel.name}</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            background: #1a1a2e;
            color: #dcddde;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            font-size: 15px;
        }}
        .header {{
            background: linear-gradient(135deg, #e74c3c, #c0392b);
            padding: 30px 40px;
            display: flex;
            align-items: center;
            gap: 20px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.4);
        }}
        .header-icon {{ font-size: 40px; }}
        .header-info h1 {{ font-size: 22px; font-weight: 700; color: #fff; }}
        .header-info p {{ font-size: 13px; color: rgba(255,255,255,0.75); margin-top: 4px; }}
        .meta {{
            background: #16213e;
            padding: 16px 40px;
            display: flex;
            flex-wrap: wrap;
            gap: 24px;
            border-bottom: 1px solid #0f3460;
            font-size: 13px;
        }}
        .meta-item {{ display: flex; flex-direction: column; gap: 2px; }}
        .meta-item .label {{
            color: #e74c3c;
            font-weight: 700;
            text-transform: uppercase;
            font-size: 11px;
            letter-spacing: 0.5px;
        }}
        .meta-item .value {{ color: #dcddde; }}
        .messages {{
            padding: 24px 40px;
            display: flex;
            flex-direction: column;
            gap: 2px;
            max-width: 1000px;
            margin: 0 auto;
        }}
        .message {{
            display: flex;
            gap: 14px;
            padding: 8px 10px;
            border-radius: 6px;
            transition: background 0.1s;
        }}
        .message:hover {{ background: rgba(255,255,255,0.03); }}
        .bot-msg {{ background: rgba(88, 101, 242, 0.05); }}
        .avatar {{
            width: 40px;
            height: 40px;
            border-radius: 50%;
            object-fit: cover;
            flex-shrink: 0;
            margin-top: 2px;
        }}
        .message-body {{ flex: 1; min-width: 0; }}
        .message-header {{
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 4px;
        }}
        .author {{ font-weight: 700; color: #fff; font-size: 15px; }}
        .tag {{
            font-size: 10px;
            font-weight: 700;
            padding: 1px 5px;
            border-radius: 3px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .tag.staff {{ background: #e74c3c; color: #fff; }}
        .tag.bot {{ background: #5865f2; color: #fff; }}
        .timestamp {{ font-size: 11px; color: #72767d; }}
        .message-content {{ color: #dcddde; line-height: 1.5; word-break: break-word; }}
        .message-content code {{
            background: #2f3136;
            padding: 1px 5px;
            border-radius: 3px;
            font-family: monospace;
            font-size: 13px;
        }}
        .attachment-img {{
            max-width: 400px;
            max-height: 300px;
            border-radius: 6px;
            margin-top: 8px;
            display: block;
        }}
        .attachment-link {{
            display: inline-block;
            margin-top: 8px;
            color: #00b0f4;
            text-decoration: none;
            font-size: 13px;
        }}
        .attachment-link:hover {{ text-decoration: underline; }}
        .embed {{
            margin-top: 8px;
            background: #2f3136;
            border-radius: 4px;
            padding: 10px 14px;
            max-width: 500px;
        }}
        .embed-title {{ font-weight: 700; color: #fff; margin-bottom: 6px; font-size: 14px; }}
        .embed-desc {{ color: #dcddde; font-size: 13px; line-height: 1.5; }}
        .footer {{
            text-align: center;
            padding: 30px;
            color: #72767d;
            font-size: 12px;
            border-top: 1px solid #0f3460;
            margin-top: 20px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <div class="header-icon">🎫</div>
        <div class="header-info">
            <h1>{channel.name}</h1>
            <p>Ticket Transcript — Control Heist Bot</p>
        </div>
    </div>
    <div class="meta">
        <div class="meta-item">
            <span class="label">Ticket</span>
            <span class="value">{channel.name}</span>
        </div>
        <div class="meta-item">
            <span class="label">Reason</span>
            <span class="value">{reason}</span>
        </div>
        <div class="meta-item">
            <span class="label">Opened By</span>
            <span class="value"><@{opener_id}> ({opener_id})</span>
        </div>
        <div class="meta-item">
            <span class="label">Closed By</span>
            <span class="value">{closed_by.display_name} ({closed_by.id})</span>
        </div>
        <div class="meta-item">
            <span class="label">Opened At</span>
            <span class="value">{opened_at}</span>
        </div>
        <div class="meta-item">
            <span class="label">Closed At</span>
            <span class="value">{closed_at}</span>
        </div>
        <div class="meta-item">
            <span class="label">Messages</span>
            <span class="value">{len(messages)}</span>
        </div>
    </div>
    <div class="messages">
        {rows}
    </div>
    <div class="footer">
        Generated by Control Heist Bot • {closed_at}
    </div>
</body>
</html>"""

    return html


class ClosedTicketControl(discord.ui.View):
    def __init__(self, opener_id: int, reason: str, original_name: str):
        super().__init__(timeout=None)
        self.opener_id     = opener_id
        self.reason        = reason
        self.original_name = original_name

    @discord.ui.button(label="Reopen Ticket", style=discord.ButtonStyle.success,
                       custom_id="tc_reopen")
    async def reopen(self, interaction: discord.Interaction,
                     button: discord.ui.Button):
        if not await require_community(interaction):
            return
        if not _is_staff(interaction.user):
            await interaction.response.send_message(
                MESSAGES["staff_only_reopen"], ephemeral=True
            )
            return

        guild    = interaction.guild
        category = guild.get_channel(TICKET_CATEGORY_ID)
        number   = _next_ticket_number()

        overwrites: dict = {
            guild.default_role:               discord.PermissionOverwrite(view_channel=False),
            guild.get_member(self.opener_id): discord.PermissionOverwrite(
                                                  view_channel=True, send_messages=True)
            if guild.get_member(self.opener_id) else discord.PermissionOverwrite(),
            guild.me:                         discord.PermissionOverwrite(
                                                  view_channel=True, send_messages=True),
        }
        for role_id in _ticket_staff_role_ids(self.reason):
            role = guild.get_role(role_id)
            if role:
                overwrites[role] = discord.PermissionOverwrite(
                    view_channel=True, send_messages=True
                )

        channel = await guild.create_text_channel(
            name=f"ticket-{number:04d}-{_clean_channel_part(self.reason)}",
            category=category,
            overwrites=overwrites,
        )

        embed = discord.Embed(
            title=f"Ticket #{number:04d} — {self.reason} (Reopened)",
            description=(
                f"Originally opened by <@{self.opener_id}>\n"
                f"Reopened by {interaction.user.mention}\n\n"
                "Previous transcript is attached above."
            ),
            color=COLOR_ORANGE,
        )
        embed.set_footer(text=TICKET_CONTROL_FOOTER)
        await channel.send(embed=embed, view=TicketControl(self.opener_id))

        button.disabled = True
        button.label    = MESSAGES["reopened_label"].format(number=number)
        await interaction.message.edit(view=self)
        await interaction.response.send_message(
            MESSAGES["ticket_reopened"].format(channel=channel.mention), ephemeral=True
        )


async def close_ticket_channel(interaction: discord.Interaction, opener_id: int) -> None:
    await interaction.response.defer(ephemeral=True)
    _open_tickets.pop(opener_id, None)

    reason = "Unknown"
    async for msg in interaction.channel.history(oldest_first=True, limit=5):
        if msg.embeds and msg.author.id == interaction.guild.me.id:
            title = msg.embeds[0].title or ""
            if "—" in title:
                reason = title.split("—")[-1].strip().split("(")[0].strip()
            elif "â€”" in title:
                reason = title.split("â€”")[-1].strip().split("(")[0].strip()
            break

    html = await _get_transcript_html(interaction.channel, opener_id, reason, interaction.user)
    transcript_file = discord.File(
        fp=io.BytesIO(html.encode()),
        filename=f"transcript-{interaction.channel.name}.html",
    )

    if TICKET_LOG_CHANNEL_ID:
        log_ch = interaction.guild.get_channel(TICKET_LOG_CHANNEL_ID)
        if log_ch:
            embed = discord.Embed(
                title=f"Ticket Closed - {interaction.channel.name}",
                color=COLOR_RED,
            )
            embed.add_field(name="Opened By", value=f"<@{opener_id}>", inline=True)
            embed.add_field(name="Closed By", value=interaction.user.mention, inline=True)
            embed.add_field(name="Reason", value=reason, inline=True)
            await log_ch.send(
                embed=embed,
                file=transcript_file,
                view=ClosedTicketControl(opener_id, reason, interaction.channel.name),
            )

    await interaction.followup.send(MESSAGES["closing"], ephemeral=True)
    await interaction.channel.delete()


class TicketCloseConfirm(discord.ui.View):
    def __init__(self, opener_id: int):
        super().__init__(timeout=60)
        self.opener_id = opener_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if not await require_community(interaction):
            return False
        if _is_staff(interaction.user):
            return True
        await interaction.response.send_message(
            MESSAGES["staff_only_close"], ephemeral=True
        )
        return False

    @discord.ui.button(label="Confirm Close", style=discord.ButtonStyle.danger, custom_id="tc_confirm_close")
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        await close_ticket_channel(interaction, self.opener_id)

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary, custom_id="tc_cancel_close")
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title=MESSAGES["close_cancelled_title"],
            description=MESSAGES["close_cancelled_description"],
            color=COLOR_BLUE,
        )
        await interaction.response.edit_message(embed=embed, view=None)


class TicketControl(discord.ui.View):
    def __init__(self, opener_id: int):
        super().__init__(timeout=None)
        self.opener_id  = opener_id
        self.claimed_by: int | None = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if not await require_community(interaction):
            return False
        if _is_staff(interaction.user):
            return True
        if interaction.user.id == self.opener_id:
            return True
        await interaction.response.send_message(
            MESSAGES["staff_only_buttons"], ephemeral=True
        )
        return False

    @discord.ui.button(label="Claim Ticket", style=discord.ButtonStyle.primary,
                       custom_id="tc_claim")
    async def claim(self, interaction: discord.Interaction,
                    button: discord.ui.Button):
        if not _is_staff(interaction.user):
            await interaction.response.send_message(
                MESSAGES["staff_only_claim"], ephemeral=True
            )
            return

        if self.claimed_by is not None:
            await interaction.response.send_message(
                MESSAGES["already_claimed"].format(user_id=self.claimed_by), ephemeral=True
            )
            return

        self.claimed_by = interaction.user.id

        for member in interaction.channel.members:
            if member.id in (interaction.user.id, self.opener_id,
                             interaction.guild.me.id):
                continue
            if _is_staff(member):
                await interaction.channel.set_permissions(
                    member,
                    view_channel=True,
                    send_messages=False
                )

        button.label    = MESSAGES["claimed_label"].format(name=interaction.user.display_name)
        button.disabled = True
        button.style    = discord.ButtonStyle.secondary
        await interaction.message.edit(view=self)
        await interaction.response.send_message(
            MESSAGES["claimed"].format(user=interaction.user.mention)
        )

    @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.danger,
                       custom_id="tc_close")
    async def close(self, interaction: discord.Interaction,
                    button: discord.ui.Button):
        if not _is_staff(interaction.user):
            await interaction.response.send_message(
                MESSAGES["staff_only_close"],
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title=TICKET_CLOSE_CONFIRM_TITLE,
            description=TICKET_CLOSE_CONFIRM_DESCRIPTION,
            color=COLOR_ORANGE,
        )
        await interaction.response.send_message(
            embed=embed,
            view=TicketCloseConfirm(self.opener_id),
            ephemeral=True,
        )


class TicketOpenModal(discord.ui.Modal):
    def __init__(self, ticket_type: str):
        super().__init__(title=f"Open {ticket_type}")
        self.ticket_type = ticket_type

        fields = TICKET_MODAL_FIELDS.get(ticket_type, TICKET_MODAL_FIELDS["Bug Report"])
        self.primary = discord.ui.TextInput(**fields["primary"])
        self.secondary = discord.ui.TextInput(**fields["secondary"])
        self.details = discord.ui.TextInput(style=discord.TextStyle.paragraph, **fields["details"])

        self.add_item(self.primary)
        self.add_item(self.secondary)
        self.add_item(self.details)

    async def on_submit(self, interaction: discord.Interaction):
        not_provided = MESSAGES["not_provided"]
        embed = discord.Embed(
            title=f"Confirm {self.ticket_type}",
            description=(
                f"{MESSAGES['confirm_summary_intro']}\n\n"
                f"**Summary:** {self.primary.value}\n"
                f"**Extra:** {self.secondary.value or not_provided}\n\n"
                f"{MESSAGES['confirm_summary_outro']}"
            ),
            color=COLOR_BLUE,
        )
        view = TicketOpenConfirm(
            ticket_type=self.ticket_type,
            answers={
                "Summary": str(self.primary.value),
                "Extra": str(self.secondary.value or not_provided),
                "Details": str(self.details.value),
            },
        )
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


class TicketOpenConfirm(discord.ui.View):
    def __init__(self, ticket_type: str, answers: dict[str, str]):
        super().__init__(timeout=180)
        self.ticket_type = ticket_type
        self.answers = answers

    @discord.ui.button(label="Open Ticket", style=discord.ButtonStyle.success, custom_id="tc_open_confirm")
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        cog: TicketCog = interaction.client.cogs.get("TicketCog")
        if cog is None:
            await interaction.response.send_message(
                MESSAGES["system_not_loaded"], ephemeral=True
            )
            return
        await cog.create_ticket(interaction, self.ticket_type, self.answers)

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary, custom_id="tc_open_cancel")
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(
            embed=discord.Embed(
                title=MESSAGES["open_cancelled_title"],
                description=MESSAGES["open_cancelled_description"],
                color=COLOR_BLUE,
            ),
            view=None,
        )


class DiscordSupportPanel(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def _open(self, interaction: discord.Interaction, reason: str):
        if not await require_community(interaction):
            return
        await interaction.response.send_modal(TicketOpenModal(reason))

    @discord.ui.button(label=SUPPORT_BUTTON_MEMBER_REPORT, style=discord.ButtonStyle.secondary,
                       custom_id="panel_member_report")
    async def member_report(self, interaction: discord.Interaction,
                            button: discord.ui.Button):
        await self._open(interaction, "Member Report")

    @discord.ui.button(label=SUPPORT_BUTTON_GENERAL_SUPPORT, style=discord.ButtonStyle.secondary,
                       custom_id="panel_general_support")
    async def general_support(self, interaction: discord.Interaction,
                              button: discord.ui.Button):
        await self._open(interaction, "General Support")

    @discord.ui.button(label=SUPPORT_BUTTON_MODERATOR_REPORT, style=discord.ButtonStyle.danger,
                       custom_id="panel_admin_support")
    async def admin_support(self, interaction: discord.Interaction,
                            button: discord.ui.Button):
        await self._open(interaction, "Moderator Report")


class BugReportPanel(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label=BUG_BUTTON_BUG_REPORT, style=discord.ButtonStyle.primary, custom_id="panel_bug_report")
    async def bug_report(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await require_community(interaction):
            return
        await interaction.response.send_modal(TicketOpenModal("Bug Report"))

    @discord.ui.button(label=BUG_BUTTON_EXPLOIT_REPORT, style=discord.ButtonStyle.danger, custom_id="panel_exploit_report")
    async def exploit_report(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await require_community(interaction):
            return
        await interaction.response.send_modal(TicketOpenModal("Exploit Report"))


class TicketCog(commands.Cog):
    add = app_commands.Group(name="add", description="Ticket access commands.")
    remove = app_commands.Group(name="remove", description="Ticket access removal commands.")

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.bot.add_view(DiscordSupportPanel())
        self.bot.add_view(BugReportPanel())
        self.bot.add_view(TicketControl(opener_id=0))
        self.bot.add_view(ClosedTicketControl(opener_id=0, reason="", original_name=""))

    async def create_ticket(self, interaction: discord.Interaction, reason: str, answers: dict[str, str] | None = None):
        uid = interaction.user.id

        if uid in _open_tickets:
            existing = interaction.guild.get_channel(_open_tickets[uid])
            if existing:
                await interaction.response.send_message(
                    MESSAGES["already_open"].format(channel=existing.mention),
                    ephemeral=True
                )
                return
            else:
                del _open_tickets[uid]

        now  = time.monotonic()
        left = COOLDOWN_SECONDS - (now - _cooldowns.get(uid, 0))
        if left > 0:
            m, s = int(left // 60), int(left % 60)
            await interaction.response.send_message(
                MESSAGES["cooldown"].format(minutes=m, seconds=s),
                ephemeral=True
            )
            return

        _cooldowns[uid] = now

        guild    = interaction.guild
        category = guild.get_channel(TICKET_CATEGORY_ID)
        number   = _next_ticket_number()

        overwrites: dict = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user:   discord.PermissionOverwrite(
                                    view_channel=True, send_messages=True),
            guild.me:           discord.PermissionOverwrite(
                                    view_channel=True, send_messages=True),
        }
        for role_id in STAFF_ROLE_IDS:
            role = guild.get_role(role_id)
            if role:
                overwrites[role] = discord.PermissionOverwrite(
                    view_channel=True, send_messages=True
                )

        channel = await guild.create_text_channel(
            name=f"ticket-{number:04d}",
            category=category,
            overwrites=overwrites,
        )

        _open_tickets[uid] = channel.id

        ping_ids = _ticket_ping_role_ids(reason)
        if ping_ids:
            await channel.send(" ".join(f"<@&{i}>" for i in ping_ids))

        answer_lines = ""
        if answers:
            answer_lines = "\n\n# Submitted Information\n" + "\n".join(
                f"**{key}:**\n{value}" for key, value in answers.items()
            )

        embed = discord.Embed(
            title=f"Ticket #{number:04d} — {reason}",
            description=(
                f"Opened by {interaction.user.mention}\n\n"
                f"{TICKET_INSTRUCTIONS.get(reason, DEFAULT_INSTRUCTION)}"
                f"{answer_lines}\n\n"
                f"{TICKET_WELCOME_FOOTER_LINE}"
            ),
            color=COLOR_RED,
        )
        embed.set_footer(text=TICKET_CONTROL_FOOTER)
        await channel.send(embed=embed, view=TicketControl(uid))
        await interaction.response.send_message(
            MESSAGES["ticket_created"].format(channel=channel.mention), ephemeral=True
        )

    @add.command(name="user", description="Add a member to the current ticket.")
    @app_commands.describe(member="The member to add to this ticket")
    async def add_user(self, interaction: discord.Interaction, member: discord.Member):
        if not await require_community(interaction):
            return
        if not isinstance(interaction.channel, discord.TextChannel) or not _is_ticket_channel(interaction.channel):
            await interaction.response.send_message(
                MESSAGES["ticket_only"], ephemeral=True
            )
            return
        if not _is_staff(interaction.user):
            await interaction.response.send_message(
                MESSAGES["staff_only_add_member"], ephemeral=True
            )
            return

        current_overwrites = interaction.channel.overwrites
        if member in current_overwrites and current_overwrites[member].view_channel:
            await interaction.response.send_message(
                MESSAGES["user_already_has_access"].format(target=member.mention), ephemeral=True
            )
            return

        await interaction.channel.set_permissions(
            member,
            view_channel=True,
            send_messages=True,
            read_message_history=True,
        )

        embed = discord.Embed(
            description=MESSAGES["user_added"].format(target=member.mention, user=interaction.user.mention),
            color=COLOR_GREEN,
        )
        await interaction.response.send_message(embed=embed)

    @remove.command(name="user", description="Remove a member from the current ticket.")
    @app_commands.describe(member="The member to remove from this ticket")
    async def remove_user(self, interaction: discord.Interaction, member: discord.Member):
        if not await require_community(interaction):
            return
        if not isinstance(interaction.channel, discord.TextChannel) or not _is_ticket_channel(interaction.channel):
            await interaction.response.send_message(
                MESSAGES["ticket_only"], ephemeral=True
            )
            return
        if not _is_staff(interaction.user):
            await interaction.response.send_message(
                MESSAGES["staff_only_remove_member"], ephemeral=True
            )
            return

        await interaction.channel.set_permissions(member, overwrite=None)
        embed = discord.Embed(
            description=MESSAGES["user_removed"].format(target=member.mention, user=interaction.user.mention),
            color=COLOR_RED,
        )
        await interaction.response.send_message(embed=embed)


    async def add_player(self, interaction: discord.Interaction, member: discord.Member):
        if not await require_community(interaction):
            return

        if not _is_ticket_channel(interaction.channel):
            await interaction.response.send_message(
                MESSAGES["ticket_only"], ephemeral=True
            )
            return

        if not _is_staff(interaction.user):
            await interaction.response.send_message(
                MESSAGES["staff_only_add_member"], ephemeral=True
            )
            return

        current_overwrites = interaction.channel.overwrites
        if member in current_overwrites and current_overwrites[member].view_channel:
            await interaction.response.send_message(
                MESSAGES["user_already_has_access"].format(target=member.mention), ephemeral=True
            )
            return

        await interaction.channel.set_permissions(
            member,
            view_channel=True,
            send_messages=True,
            read_message_history=True,
        )

        embed = discord.Embed(
            description=MESSAGES["user_added"].format(target=member.mention, user=interaction.user.mention),
            color=COLOR_GREEN,
        )
        await interaction.response.send_message(embed=embed)


    async def add_role(self, interaction: discord.Interaction, role: discord.Role):
        if not await require_community(interaction):
            return

        if not _is_ticket_channel(interaction.channel):
            await interaction.response.send_message(
                MESSAGES["ticket_only"], ephemeral=True
            )
            return

        if not _is_staff(interaction.user):
            await interaction.response.send_message(
                MESSAGES["staff_only_add_role"], ephemeral=True
            )
            return

        current_overwrites = interaction.channel.overwrites
        if role in current_overwrites and current_overwrites[role].view_channel:
            await interaction.response.send_message(
                MESSAGES["user_already_has_access"].format(target=role.mention), ephemeral=True
            )
            return

        await interaction.channel.set_permissions(
            role,
            view_channel=True,
            send_messages=True,
            read_message_history=True,
        )

        embed = discord.Embed(
            description=MESSAGES["user_added"].format(target=role.mention, user=interaction.user.mention),
            color=COLOR_GREEN,
        )
        await interaction.response.send_message(embed=embed)


    async def remove_player(self, interaction: discord.Interaction, member: discord.Member):
        if not await require_community(interaction):
            return

        if not _is_ticket_channel(interaction.channel):
            await interaction.response.send_message(
                MESSAGES["ticket_only"], ephemeral=True
            )
            return

        if not _is_staff(interaction.user):
            await interaction.response.send_message(
                MESSAGES["staff_only_remove_member"], ephemeral=True
            )
            return

        await interaction.channel.set_permissions(member, overwrite=None)

        embed = discord.Embed(
            description=MESSAGES["user_removed"].format(target=member.mention, user=interaction.user.mention),
            color=COLOR_RED,
        )
        await interaction.response.send_message(embed=embed)


    async def remove_role(self, interaction: discord.Interaction, role: discord.Role):
        if not await require_community(interaction):
            return

        if not _is_ticket_channel(interaction.channel):
            await interaction.response.send_message(
                MESSAGES["ticket_only"], ephemeral=True
            )
            return

        if not _is_staff(interaction.user):
            await interaction.response.send_message(
                MESSAGES["staff_only_remove_role"], ephemeral=True
            )
            return

        await interaction.channel.set_permissions(role, overwrite=None)

        embed = discord.Embed(
            description=MESSAGES["user_removed"].format(target=role.mention, user=interaction.user.mention),
            color=COLOR_RED,
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(
        name="ticketpanel",
        description="Post the support ticket panel (wipes the channel first)"
    )
    @app_commands.checks.has_any_role(*PANEL_ADMIN_ROLE_IDS)
    async def ticketpanel(self, interaction: discord.Interaction):
        if not await require_community(interaction):
            return
        channel = interaction.guild.get_channel(TICKET_PANEL_CHANNEL_ID)

        if not channel:
            return await interaction.response.send_message(
                MESSAGES["panel_channel_missing"],
                ephemeral=True
            )

        await interaction.response.defer(ephemeral=True)
        await channel.purge(limit=100)

        embed = discord.Embed(
            description=SUPPORT_PANEL_DESCRIPTION,
            color=SUPPORT_PANEL_COLOR,
        )
        await channel.send(embed=embed, view=DiscordSupportPanel())
        await interaction.followup.send(MESSAGES["panel_posted"], ephemeral=True)

    @ticketpanel.error
    async def ticketpanel_error(self, interaction: discord.Interaction,
                                error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingAnyRole):
            await interaction.response.send_message(
                MESSAGES["no_permission"], ephemeral=True
            )


class BugPanelCog(commands.Cog):
    bugpanel = app_commands.Group(name="bugpanel", description="Bug report panel commands.")

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @bugpanel.command(name="setup", description="Post the permanent Heist Control bug reporting panel.")
    async def setup_panel(self, interaction: discord.Interaction):
        from core.bot_config import OWNER_ID

        if interaction.user.id != OWNER_ID:
            await interaction.response.send_message(
                MESSAGES["owner_only"], ephemeral=True
            )
            return

        from core.bot_config import COMMUNITY_GUILD_ID

        community_guild = self.bot.get_guild(COMMUNITY_GUILD_ID)
        if community_guild is None:
            await interaction.response.send_message(
                MESSAGES["community_unavailable"],
                ephemeral=True,
            )
            return

        channel = community_guild.get_channel(BUG_REPORT_PANEL_CHANNEL_ID)
        if not isinstance(channel, discord.TextChannel):
            channel = discord.utils.get(community_guild.text_channels, name=BUG_PANEL_CHANNEL_NAME)

        if not isinstance(channel, discord.TextChannel):
            await interaction.response.send_message(
                MESSAGES["bug_panel_channel_missing"],
                ephemeral=True,
            )
            return

        await interaction.response.defer(ephemeral=True)
        await channel.purge(limit=100)
        await channel.send(embed=_bug_panel_embed(), view=BugReportPanel())
        await interaction.followup.send(
            MESSAGES["bug_panel_posted"].format(guild=community_guild.name, channel=channel.name),
            ephemeral=True,
        )

    @setup_panel.error
    async def setup_panel_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingAnyRole):
            await interaction.response.send_message(
                MESSAGES["no_permission"],
                ephemeral=True,
            )
            return
        raise error


async def setup(bot: commands.Bot):
    from core.bot_config import COMMUNITY_GUILD_ID

    await bot.add_cog(TicketCog(bot), guild=discord.Object(id=COMMUNITY_GUILD_ID))