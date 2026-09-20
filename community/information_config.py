from core.bot_config import OWNER_ID

INFORMATION_CHANNEL_ID = 1501497012745539705

APPLICATION_ID = ""


STUDIO_NAME = "Heist Control"
PROJECT_STATUS = "In Development"
DEVELOPMENT_STATUS = "Active"
COMMUNITY_STATUS = "Open"
TESTING_STATUS = "Not Available"
RELEASE_STATUS = "Not Released"


GAME_DESCRIPTION = (
    "Heist Control is a large-scale cooperative robbery experience currently in active development.\n\n"
    "The project focuses on teamwork, planning, execution, progression, and replayability.\n\n"
    "Players will work together to complete operations, overcome security systems, gather valuable assets, "
    "and execute carefully planned objectives.\n\n"
    "The goal is to create a polished and long-term experience rather than rushing content for release."
)


RELEASE_INFO = (
    "**There is currently no public release date.**\n\n"
    "Development will continue until the team is satisfied with the quality and stability of the game.\n\n"
    "The project is large in scope and additional development time may be required to achieve the expected quality standards.\n\n"
    "Release estimates should never be provided by staff unless officially announced."
)


COMMUNITY_INFO = (
    "This server serves as the central hub for:\n\n"
    "- Announcements\n"
    "- Development Updates\n"
    "- Community Discussion\n"
    "- Feedback\n"
    "- Suggestions\n"
    "- Bug Reports\n"
    "- Recruitment Opportunities\n"
    "- Future Testing Information\n"
    "- Support Requests"
)


DEVELOPMENT_PHILOSOPHY = (
    "The goal of Heist Control is not rapid release.\n\n"
    "The goal is long-term quality.\n\n"
    "Development decisions prioritize stability, maintainability, player experience, and overall polish.\n\n"
    "The team focuses on creating systems that can support future expansion and continued development after release."
)


SUPPORT_INFO = (
    "Support requests should be submitted through the designated ticket systems.\n\n"
    "Bug reports should be submitted through the Bug Reports section.\n\n"
    "Moderation issues should be submitted through the Discord Support section.\n\n"
    "Staff members may require additional information before a request can be processed."
)


FAQ: dict[str, str] = {
    "When is Heist Control releasing?": (
        "There is currently no official release date. "
        "The game remains in active development and will be released once it meets the quality standards established by the studio."
    ),
    "Can I become a tester?": (
        "Testing opportunities may become available in the future. "
        "Any public testing phases will be announced through official server channels."
    ),
    "How can I support the project?": (
        "Being active in the community, providing constructive feedback, reporting issues, "
        "and supporting development updates are the best ways to contribute."
    ),
    "Can I apply for the development team?": (
        "When positions become available they will be posted through the careers and recruitment sections of the server."
    ),
    "Why are updates taking time?": (
        "The studio prioritizes quality, stability, and long-term maintainability over rushed development. "
        "Features are reviewed, tested, and refined before release."
    ),
    "Can staff provide release estimates?": (
        "No. Only officially published announcements should be considered accurate information regarding "
        "development milestones and release plans."
    ),
}


ROLES: dict[str, str] = {
    "Owner": "Responsible for overall ownership of the project and final authority across all studio operations.",
    "Studio Director": "Oversees project direction, production planning, development goals, and department coordination.",
    "Department Lead": "Manages a specific department and supervises team members within that department.",
    "Developer": "Responsible for creating, maintaining, and improving systems, assets, and features within their assigned field.",
    "Trial Developer": "Evaluation role for new development team members.",
    "Quality Assurance": "Tests systems, verifies fixes, investigates reports, and assists with maintaining product quality.",
    "Moderator": "Responsible for enforcing community standards and maintaining a healthy server environment.",
    "Community Member": "Standard member role for community participants.",
}


SOCIALS: dict[str, str] = {
    "Roblox Group": "",
    "Discord": "",
    "Twitter": "",
    "YouTube": "",
    "TikTok": "",
    "Website": "",
}


INFO_COLOR = 0x206694
INFO_FOOTER = "Heist Control — Information"
INFO_TITLE_FORMAT = "# __**{}**__"

INFO_PANEL_DESCRIPTION = (
    "# __**Heist Control — Information**__\n\n"
    "Select a category from the dropdown menu below to view official server information.\n\n"
    "All information shown here is maintained by the Heist Control administration team.\n\n"
    "> **If you cannot find the information you need, open a General Support ticket.**"
)

INFO_SELECT_PLACEHOLDER = "Select a category to view information..."
INFO_SELECT_OPTIONS: list[tuple[str, str, str]] = [
    ("Studio Information", "studio_info", "Overview of Heist Control studio status."),
    ("Game Description", "game_description", "What Heist Control is and what to expect."),
    ("Release Information", "release_info", "Current release status and expectations."),
    ("FAQ", "faq", "Frequently asked questions."),
    ("Roles", "roles", "Server and studio role descriptions."),
    ("Socials", "socials", "Official social and external links."),
    ("Community Info", "community_info", "What this server is used for."),
    ("Development Philosophy", "dev_philosophy", "How the project is being developed."),
    ("Support Information", "support_info", "How to get support and submit reports."),
]

INFO_PAGES: dict[str, tuple[str, str]] = {
    "game_description": ("Game Description", GAME_DESCRIPTION),
    "release_info": ("Release Information", RELEASE_INFO),
    "community_info": ("Community Information", COMMUNITY_INFO),
    "dev_philosophy": ("Development Philosophy", DEVELOPMENT_PHILOSOPHY),
    "support_info": ("Support Information", SUPPORT_INFO),
}

STUDIO_INFO_FIELDS: list[tuple[str, str]] = [
    ("Studio Name", STUDIO_NAME),
    ("Project Status", PROJECT_STATUS),
    ("Development Status", DEVELOPMENT_STATUS),
    ("Community Status", COMMUNITY_STATUS),
    ("Testing Status", TESTING_STATUS),
    ("Release Status", RELEASE_STATUS),
]

MESSAGES: dict[str, str] = {
    "owner_only": "Only the bot owner can use this command.",
    "channel_missing": "INFORMATION_CHANNEL_ID is not set or the channel no longer exists.",
    "panel_posted": "Information panel posted.",
    "faq_empty": "No FAQ entries have been configured.",
    "faq_placeholder": "Select a question...",
    "faq_prompt": "Select a question to view the answer.",
    "faq_no_answer": "No answer configured.",
    "roles_empty": "No roles have been configured.",
    "roles_placeholder": "Select a role...",
    "roles_prompt": "Select a role to view its description.",
    "roles_no_description": "No description configured.",
    "socials_empty": "No social links have been configured yet.",
}