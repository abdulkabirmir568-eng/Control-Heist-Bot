from core.bot_config import COMMUNITY_GUILD_ID

TICKET_CATEGORY_ID: int = 1501542352328720474

TICKET_PANEL_CHANNEL_ID: int = 1500965651127205928
BUG_REPORT_PANEL_CHANNEL_ID: int = 1501305984226951309

BUG_REPORT_CATEGORY_ID: int = 0

BUG_REPORT_LOG_CHANNEL_ID: int = 0

TICKET_LOG_CHANNEL_ID: int = 1501510289601069086

STAFF_ROLE_IDS: list[int] = [
    1501237504269881525,
    1501237422577418423,
    1501237056272076841,
    1497586822799298711,
    1507681497799327784,
]

SUPPORT_PING_IDS: list[int] = [
    1501237504269881525,
    1501237422577418423,
]

ADMIN_PING_IDS: list[int] = [
    1501237056272076841,
    1497586822799298711,
    1507681497799327784,
]

MODERATOR_REPORT_ROLE_IDS: list[int] = [
    1501237056272076841,
    1497586822799298711,
    1507681497799327784,
]

BUG_REPORT_ROLE_IDS: list[int] = [
    1497590193174085803,
    1500957611632099471,
]

QA_TEAM_ROLE_IDS: list[int] = BUG_REPORT_ROLE_IDS
LEAD_DEVELOPER_ROLE_IDS: list[int] = [
    1500957611632099471,
]
STUDIO_DIRECTOR_ROLE_IDS: list[int] = [
    1497586822799298711,
]
BUG_REPORT_OWNER_ROLE_IDS: list[int] = [
    1497586822799298711,
]

PANEL_ADMIN_ROLE_IDS: list[int] = [
    1501237056272076841,
    1497586822799298711,
]

COOLDOWN_SECONDS: int = 600

COLOR_RED = 0xE74C3C
COLOR_BLUE = 0x3498DB
COLOR_ORANGE = 0xE67E22
COLOR_GREEN = 0x2ECC71

BUG_REPORTS_LINK = f"https://discord.com/channels/{COMMUNITY_GUILD_ID}/{BUG_REPORT_PANEL_CHANNEL_ID}"

SUPPORT_PANEL_COLOR = COLOR_RED
SUPPORT_PANEL_DESCRIPTION = (
    "# Discord Support\n\n"
    "__**Member Report**__\n"
    "For reporting members who have violated the server rules **outside of Heist Control**.\n"
    "Evidence is mandatory — you must attach uncropped screenshots or video "
    "clearly showing the full Discord client and the accused member's profile. "
    "Reports submitted without valid proof will be closed immediately.\n\n"
    "__**General Support**__\n"
    "For server related questions, warn appeals, and mute appeals.\n"
    "When appealing a punishment, you must include the exact date, the reason given, "
    "and any relevant context. Vague or incomplete appeals will not be reviewed.\n\n"
    "__**Moderator Report**__\n"
    "Reserved for reporting moderator misconduct. These tickets are restricted "
    "to senior leadership and should include clear evidence where possible.\n\n"
    "```diff\n"
    "- IN-GAME ISSUES ARE NOT HANDLED HERE\n"
    "```\n"
    f"**HEAD TO [BUG REPORTS]({BUG_REPORTS_LINK}) FOR IN-GAME ISSUES**"
)

SUPPORT_BUTTON_MEMBER_REPORT = "Member Report"
SUPPORT_BUTTON_GENERAL_SUPPORT = "General Support"
SUPPORT_BUTTON_MODERATOR_REPORT = "Moderator Report"

BUG_PANEL_COLOR = COLOR_BLUE
BUG_PANEL_FOOTER = "Heist Control - Quality Assurance Department"
BUG_PANEL_DESCRIPTION = (
    "#  Heist Control Bug Reports\n\n"
    "****__Bug Report__****\n\n"
    "Use this ticket for reporting gameplay issues, broken systems, visual glitches, UI problems, progression issues, mission problems, interaction failures, and any feature that is not functioning as intended.\n\n"
    "When creating a report, provide clear and accurate information. Reports containing detailed reproduction steps and supporting evidence can be investigated significantly faster by the development team.\n\n"
    "****__Exploit Report__****\n\n"
    "Use this option when reporting economy abuse, duplication methods, security vulnerabilities, unintended access methods, progression exploits, or any issue that could negatively impact game integrity.\n\n"
    "Exploit reports are treated with high priority and reviewed privately by senior development staff.\n\n"
    "****Evidence Requirements****\n\n"
    "The following information is strongly recommended:\n\n"
    "- Screenshots\n"
    "- Video recordings\n"
    "- Reproduction steps\n"
    "- Exact location\n"
    "- Device information\n"
    "- Platform information\n"
    "- Error messages\n"
    "- Console output where applicable\n\n"
    "Reports lacking sufficient information may require additional clarification before investigation can begin.\n\n"
    "```fix\n"
    "ALL REPORTS ARE REVIEWED BY THE QUALITY ASSURANCE TEAM\n"
    "```\n\n"
    "**FALSE REPORTS OR ABUSE OF THE BUG REPORT SYSTEM MAY RESULT IN MODERATION ACTION.**"
)

BUG_BUTTON_BUG_REPORT = "BUG REPORT"
BUG_BUTTON_EXPLOIT_REPORT = "EXPLOIT REPORT"

BUG_CATEGORY_NAME = "BUG REPORTS"
BUG_LOG_CHANNEL_NAME = "bug-report-logs"
BUG_PANEL_CHANNEL_NAME = "bug-reports"

TICKET_CONTROL_FOOTER = "Support staff: use the buttons below to manage this ticket."

TICKET_WELCOME_FOOTER_LINE = "A support member will be with you shortly."

TICKET_CLOSE_CONFIRM_TITLE = "Confirm Ticket Closure"
TICKET_CLOSE_CONFIRM_DESCRIPTION = (
    "This will save a transcript, post it to the ticket log, and delete this channel.\n\n"
    "Confirm only when the ticket is fully resolved."
)

TICKET_MODAL_FIELDS: dict[str, dict[str, dict]] = {
    "Member Report": {
        "primary": {"label": "Who are you reporting?", "max_length": 120},
        "secondary": {"label": "What rule was broken?", "max_length": 200},
        "details": {"label": "Evidence and context", "max_length": 1500},
    },
    "General Support": {
        "primary": {"label": "What do you need help with?", "max_length": 160},
        "secondary": {"label": "When did it happen?", "max_length": 120, "required": False},
        "details": {"label": "Explain the situation", "max_length": 1500},
    },
    "Moderator Report": {
        "primary": {"label": "Which moderator are you reporting?", "max_length": 120},
        "secondary": {"label": "What happened?", "max_length": 200},
        "details": {"label": "Evidence and full context", "max_length": 1500},
    },
    "Bug Report": {
        "primary": {"label": "Bug title", "max_length": 120},
        "secondary": {"label": "Device/platform", "max_length": 120},
        "details": {"label": "Steps to reproduce and expected result", "max_length": 1500},
    },
}

TICKET_INSTRUCTIONS: dict[str, str] = {
    "Member Report": (
        "**Required format — fill this in before a staff member joins:**\n"
        "```\n"
        "Reported user  : (username + ID)\n"
        "Rule broken    : (exact rule)\n"
        "Where          : (channel name or DMs)\n"
        "Evidence       : (attach uncropped screenshots or video below)\n"
        "```\n"
        "Screenshots must show the full Discord client. Cropped images will not be accepted."
    ),
    "General Support": (
        "**Required format — fill this in before a staff member joins:**\n"
        "```\n"
        "Issue          : (brief description)\n"
        "Date occurred  : (YYYY-MM-DD)\n"
        "Punishment     : (warn / mute / other — include reason if appealing)\n"
        "Additional info: \n"
        "```"
    ),
    "Admin Support": (
        "**Required format — fill this in before a staff member joins:**\n"
        "```\n"
        "Subject        : (brief description)\n"
        "Staff involved : (username + ID if applicable)\n"
        "Evidence       : (attach screenshots or video below)\n"
        "```\n"
        "This ticket type is for extreme situations only reporting staff or major server issues."
    ),
    "Moderator Report": (
        "**Private moderator report:**\n"
        "```\n"
        "Staff involved : (username + ID if applicable)\n"
        "Issue          : (what happened)\n"
        "Evidence       : (attach screenshots or video below)\n"
        "```\n"
        "This ticket is restricted to senior leadership."
    ),
    "Bug Report": (
        "**Bug report workflow:**\n"
        "```\n"
        "Bug title      : (short title)\n"
        "Platform       : (PC / mobile / console)\n"
        "Steps          : (how staff can reproduce it)\n"
        "Expected result: (what should have happened)\n"
        "```\n"
        "Attach screenshots or clips if they help the development team reproduce the issue."
    ),
}
DEFAULT_INSTRUCTION = "Describe your issue."

MESSAGES: dict[str, str] = {
    "no_permission": "You don't have permission to use this command.",
    "owner_only": "Only the server owner can use this command.",
    "ticket_only": "This command can only be used inside a ticket.",
    "staff_only_reopen": "Only support staff can reopen tickets.",
    "staff_only_close": "Only support staff can close tickets.",
    "staff_only_claim": "Only support staff can claim tickets.",
    "staff_only_buttons": "Only support staff can use these buttons.",
    "staff_only_add_member": "Only support staff can add members to tickets.",
    "staff_only_remove_member": "Only support staff can remove members from tickets.",
    "staff_only_add_role": "Only support staff can add roles to tickets.",
    "staff_only_remove_role": "Only support staff can remove roles from tickets.",
    "already_claimed": "Already claimed by <@{user_id}>.",
    "claimed": "{user} has claimed this ticket.",
    "claimed_label": "Claimed by {name}",
    "already_open": "You already have an open ticket: {channel}",
    "cooldown": "You must wait **{minutes}m {seconds}s** before opening another ticket.",
    "ticket_created": "Ticket created: {channel}",
    "ticket_reopened": "Ticket reopened: {channel}",
    "reopened_label": "Reopened as #{number:04d}",
    "closing": "Closing ticket...",
    "system_not_loaded": "Ticket system is not loaded. Contact an admin.",
    "panel_posted": "Panel posted.",
    "panel_channel_missing": (
        "TICKET_PANEL_CHANNEL_ID is not set or the channel no longer exists.\n"
        "Edit `tickets/ticket_config.py` to fix this."
    ),
    "bug_panel_channel_missing": "Could not find #bug-reports. Set BUG_REPORT_PANEL_CHANNEL_ID or create the channel.",
    "community_unavailable": "The Community Server is not available to this bot session.",
    "bug_panel_posted": "Bug report panel posted in {guild} / #{channel}.",
    "user_already_has_access": "{target} already has access to this ticket.",
    "user_added": "{target} has been added to this ticket by {user}.",
    "user_removed": "{target} has been removed from this ticket by {user}.",
    "close_cancelled_title": "Ticket Close Cancelled",
    "close_cancelled_description": "The ticket will remain open.",
    "open_cancelled_title": "Ticket Cancelled",
    "open_cancelled_description": "No ticket was opened.",
    "confirm_summary_intro": "Review your information before opening a private ticket.",
    "confirm_summary_outro": "Click **Open Ticket** to continue.",
    "not_provided": "Not provided",
}
