from core.bot_config import OWNER_ID

RULES_CHANNEL_ID: int = 1508133388018516159

APPEAL_SERVER: str = "https://discord.gg/6wVXH2UufV"


RULES: dict[str, tuple[str, str]] = {
    "general": (
        "General Rules",
        (
            "## 1. Respect All Members\n"
            "**Harassment, discrimination, hate speech, and targeted insults of any kind are strictly prohibited.**\n"
            "This includes comments regarding race, ethnicity, gender, religion, sexuality, "
            "nationality, or disability. Disrespectful behaviour toward any member — regardless of their "
            "rank or standing — will result in an immediate punishment with no prior warning.\n\n"

            "## 2. No Spamming or Flooding\n"
            "**Repeated messages, excessive line breaks, walls of text, or flooding any channel are not permitted.**\n"
            "This applies to all channels including general chat, media channels, and bot command channels. "
            "Violators will be muted without warning.\n\n"

            "## 3. No Advertising or Self-Promotion\n"
            "**Advertising other Discord servers, Roblox games, YouTube channels, or any external platforms is strictly forbidden**\n"
            "unless you have received explicit written permission from a member of the administration team. "
            "Unsolicited advertising will result in an immediate permanent ban.\n\n"

            "## 4. Use Channels for Their Intended Purpose\n"
            "**Every channel has a designated purpose outlined in its description.**\n"
            "Posting off-topic content, derailing conversations, or misusing channels is not allowed. Staff "
            "reserve the right to delete any message that does not belong in its respective channel.\n\n"

            "## 5. No NSFW or Inappropriate Content\n"
            "**Sharing, linking, or referencing any sexually explicit, graphically violent, or inappropriate content is completely forbidden.**\n"
            "This includes profile pictures, usernames, status messages, and any shared media. Any member "
            "found violating this rule will be permanently banned with no possibility of appeal.\n\n"

            "## 6. English Only in Main Channels\n"
            "**All communication in public channels must be in English** so that staff can moderate effectively.\n"
            "Non-English conversations must be kept to direct messages or designated channels if available.\n\n"

            "## 7. Staff Instructions Must Be Followed\n"
            "**All members are required to comply with instructions given by staff members acting within their authority.**\n"
            "Arguing with, ignoring, or disrespecting staff in the execution of their duties is considered "
            "a serious offence and will be escalated accordingly."
        )
    ),

    "discord_tos": (
        "Discord Terms of Service",
        (
            "**All members of this server are required to comply fully with Discord's Terms of Service "
            "and Community Guidelines at all times.**\n"
            "Violating Discord TOS within this server — or being found to have violated it externally — "
            "may result in removal from the server.\n\n"

            "## Age Requirement\n"
            "**Discord requires all users to be at least 13 years of age.**\n"
            "Any member found to be underage will be reported to Discord's Trust and Safety team and "
            "permanently banned from this server immediately.\n\n"

            "## No Threats or Incitement of Violence\n"
            "**Making threats of real-world violence, encouraging self-harm, or inciting harm toward any individual or group is strictly forbidden.**\n"
            "This is a direct violation of Discord's Terms of Service and will result in an immediate "
            "permanent ban as well as a report to Discord's Trust and Safety team.\n\n"

            "## No Account Sharing or Impersonation\n"
            "**Sharing your account with another individual or impersonating any person is prohibited.**\n"
            "This includes staff members, other users, or public figures. Account sharing may result "
            "in both accounts being permanently banned.\n\n"

            "## No Unauthorised Automation\n"
            "**The use of self-bots, user-bots, or any automated account activity that violates Discord's TOS is strictly forbidden.**\n"
            "Any member found using such tools will be permanently banned without appeal.\n\n"

            "-# You can read Discord's full Terms of Service at: https://discord.com/terms\n"
            "-# You can read Discord's Community Guidelines at: https://discord.com/guidelines"
        )
    ),

    "roblox_tos": (
        "Roblox Terms of Service",
        (
            "**As this server is affiliated with a Roblox game, all members are expected to behave in "
            "accordance with Roblox's Terms of Use and Community Standards.**\n"
            "Violations of Roblox TOS that are reported and verified within this server's jurisdiction will be actioned.\n\n"

            "## No Exploiting or Cheating\n"
            "**Using exploits, scripts, hacks, or any third-party software to gain an unfair advantage is strictly forbidden.**\n"
            "Exploiters will be permanently banned from both the game and this Discord server. Evidence must "
            "be submitted via a Data Issues ticket and will be reviewed by the administration team.\n\n"

            "## No Account Trading or Selling\n"
            "**Trading, selling, or purchasing Roblox accounts is a direct violation of Roblox's Terms of Use.**\n"
            "Any member found engaging in account trading — even outside the server — may be removed at "
            "the discretion of the administration team.\n\n"

            "## No Scamming\n"
            "**Attempting to scam other players of in-game items, Robux, or any other assets is prohibited.**\n"
            "This constitutes a violation of Roblox's Community Standards. Verified scamming will result "
            "in a permanent ban from the server and a report to Roblox.\n\n"

            "## No Inappropriate Usernames or Content\n"
            "**Members whose Roblox usernames, profile descriptions, or in-game behaviour violate Roblox's Community Standards may be removed.**\n"
            "Removal is at staff discretion.\n\n"

            "-# You can read Roblox's Terms of Use at: https://en.help.roblox.com/hc/en-us/articles/115004647846\n"
            "-# You can read Roblox's Community Standards at: https://en.help.roblox.com/hc/en-us/articles/203313410"
        )
    ),

    "punishments": (
        "Punishment Guidelines",
        (
            "**Punishments are issued at the discretion of the moderation and administration team.**\n"
            "The severity depends on the nature of the offence, its frequency, and the intent behind it. "
            "Staff are not required to issue warnings before taking action on serious violations.\n\n"

            "## Verbal Warning\n"
            "**Issued for minor first-time offences** such as mild off-topic behaviour, mild language, "
            "or accidental rule violations. A verbal warning is not logged but serves as a formal notice.\n\n"

            "## Formal Warn\n"
            "**Issued for repeated minor offences or moderate violations.**\n"
            "Warns are logged against your account and accumulate over time. Multiple warns will result "
            "in escalating punishments.\n\n"

            "## Mute\n"
            "**Issued for disruptive behaviour, spamming, repeated offences, or failure to comply with staff instructions.**\n"
            "Mute durations range from **1 hour to 28 days** depending on severity and history.\n\n"

            "## Kick\n"
            "**Issued for serious violations or repeated mutable offences.**\n"
            "A kick removes you from the server but does not prevent you from rejoining. Kicks are logged "
            "and considered when determining future punishments.\n\n"

            "## Temporary Ban\n"
            "**Issued for severe rule violations, accumulation of punishments, or serious misconduct.**\n"
            "Temporary bans range from **1 day to 30 days**. Attempting to evade a temporary ban using "
            "an alternate account will result in a permanent ban.\n\n"

            "## Permanent Ban\n"
            "**Issued for the most serious offences** including but not limited to: exploiting, NSFW "
            "content, threats, doxxing, impersonation of staff, or ban evasion.\n"
            "Permanent bans may be appealed at the appeal server: " + APPEAL_SERVER
        )
    ),

    "appeals": (
        "Appeals & Ban Information",
        (
            "**If you believe a punishment was unjust or wish to appeal a permanent ban, you must follow the correct procedure.**\n"
            "Appeals submitted incorrectly or through the wrong channel will not be reviewed.\n\n"

            "## Warn and Mute Appeals\n"
            "**Must be submitted through a General Support ticket in this server.**\n"
            "When submitting an appeal you must include the exact date the punishment was issued, the "
            "reason provided by the staff member, and a clear explanation of why you believe the "
            "punishment was unjust. Incomplete appeals will be closed without review.\n\n"

            "## Ban Appeals\n"
            "**Permanent and temporary ban appeals must be submitted exclusively through our appeal server.**\n"
            "You will not be able to appeal a ban through this server as you will no longer have access to it.\n\n"
            "-# Appeal server: " + APPEAL_SERVER + "\n\n"

            "## Appeal Rules\n"
            "**Appeals must be submitted in good faith.**\n"
            "Submitting false information, being disrespectful toward staff reviewing your appeal, or "
            "submitting multiple appeals for the same punishment will result in your appeal being denied "
            "and may result in additional consequences.\n\n"

            "## Appeal Outcomes\n"
            "**Appeals are reviewed by the administration team and decisions are final.**\n"
            "Not all appeals will be accepted. If your appeal is denied you will be informed of the reason. "
            "You may resubmit an appeal after **30 days** if new information becomes available."
        )
    ),

    "staff_conduct": (
        "Staff Conduct & Expectations",
        (
            "**All staff members of Heist Control are held to a higher standard of conduct than regular members.**\n"
            "Staff are representatives of the server and are expected to act professionally "
            "and impartially at all times.\n\n"

            "## Staff Are Not Exempt from Rules\n"
            "**Being a staff member does not grant immunity from the server rules.**\n"
            "Staff members who violate the rules are subject to the same punishments as regular members "
            "and may additionally lose their staff position.\n\n"

            "## Abuse of Power Is Strictly Prohibited\n"
            "**Staff members must not use their permissions for personal gain, to target specific members, or to act outside their assigned role.**\n"
            "Any verified abuse of power will result in immediate demotion and a permanent ban.\n\n"

            "## Reporting Staff Misconduct\n"
            "**If you believe a staff member has acted improperly, report it through an Admin Support ticket.**\n"
            "Provide as much evidence as possible. Reports will be reviewed exclusively by the administration "
            "team and handled confidentially.\n\n"

            "## Do Not Argue with Staff Decisions in Public\n"
            "**If you disagree with a moderation decision, do not argue about it in public channels.**\n"
            "Open a ticket to discuss the matter privately. Public disputes with staff decisions "
            "will be considered disruptive behaviour and may result in a mute."
        )
    ),
}


RULES_COLOR = 0xE74C3C
RULES_FOOTER = "Heist Control — Rules & Guidelines"
RULES_PANEL_FOOTER = "Last updated by the Heist Control Administration Team."
RULES_SELECT_PLACEHOLDER = "Select a category to view the rules..."

RULES_PANEL_DESCRIPTION = (
    "# __**Control Interactive DevNet — Server Rules**__\n\n"
    "All members of this server are required to read, understand, "
    "and fully comply with all listed rules.\n"
    "__Ignorance of the rules will not be accepted as an excuse for any violation.__\n\n"
    "By remaining in this server, you automatically agree to abide by all rules listed below, "
    "alongside Discord's Terms of Service and Roblox's Terms of Use at all times.\n\n"
    "> **FAILURE TO FOLLOW THESE RULES MAY RESULT IN WARNINGS, MUTES, "
    "KICKS, OR A PERMANENT BAN DEPENDING ON THE SEVERITY OF THE OFFENCE.**\n\n"
    "__**IMPORTANT:**__\n"
    "Select a category from the dropdown menu below to review the rules "
    "for that specific section.\n"
    "You are expected to read all applicable categories before participating within the server."
)

RULES_SELECT_OPTIONS: list[tuple[str, str, str]] = [
    ("General Rules", "general", "Core server rules all members must follow."),
    ("Discord Terms of Service", "discord_tos", "Discord TOS requirements enforced in this server."),
    ("Roblox Terms of Service", "roblox_tos", "Roblox TOS and Community Standards."),
    ("Punishment Guidelines", "punishments", "How punishments are issued and escalated."),
    ("Appeals & Ban Information", "appeals", "How to appeal warns, mutes, and bans."),
    ("Staff Conduct", "staff_conduct", "Standards expected of all staff members."),
]

MESSAGES: dict[str, str] = {
    "owner_only": "Only the bot owner can use this command.",
    "channel_missing": "RULES_CHANNEL_ID is not set or the channel no longer exists.",
    "panel_posted": "Rules panel posted.",
}
