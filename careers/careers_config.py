from core.bot_config import OWNER_ID

CAREERS_CHANNEL_ID = 1508226281416687758
APPLICATION_REVIEW_CHANNEL_ID = 1510711986168528998
GOOGLE_FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSegorhryXX5mNevEMXwNLzyB071aJr-WJcXsQH_O3TDC4EYSA/viewform?usp=publish-editor"
STUDIO_DIRECTOR_ROLE_IDS = [1497586822799298711]
STUDIO_DIRECTOR_USER_IDS = [1497586822799298711]

CAREERS_COLOR = 0xFF6600

CAREERS_EMBED_TITLE = "**Careers**"
CAREERS_EMBED_DESCRIPTION = (
    "**We are recruiting developers and testers**\n\n"
    "Applications are handled **via form only**\n"
    "Must be **16+** and **serious applicants only**\n"
    "No guarantees of acceptance\n\n"
    "Click the button below to apply."
)
CAREERS_EMBED_FOOTER = "Heist Control — Applications via Google Form only"
APPLY_BUTTON_LABEL = "Apply Now"

REVIEW_EMBED_TITLE = "**Application Review**"
REVIEW_PASS_LABEL = "PASS"
REVIEW_FAIL_LABEL = "FAIL"

REVIEW_MODAL_TITLE = "New Application Review"
REVIEW_MODAL_FIELDS: dict[str, dict] = {
    "user_id": {"label": "Applicant Discord User ID", "placeholder": "e.g. 123456789012345678", "required": True},
    "username": {"label": "Applicant Username", "placeholder": "e.g. username", "required": True},
    "position": {"label": "Position Applied For", "placeholder": "e.g. Developer / Bug Tester", "required": True},
    "notes": {"label": "Notes (optional)", "placeholder": "Any additional notes...", "required": False},
}

DECISIONS: dict[str, dict[str, str]] = {
    "ACCEPTED": {
        "applicant_message": (
            "Your application for **{position}** has been **ACCEPTED**.\n\n"
            "You will be contacted shortly with next steps."
        ),
        "notify_title": "Application Accepted",
    },
    "REJECTED": {
        "applicant_message": (
            "Your application for **{position}** has been **REJECTED**.\n\n"
            "Thank you for your interest."
        ),
        "notify_title": "Application Rejected",
    },
}
APPLICANT_DM_TITLE = "Application Update"

MESSAGES: dict[str, str] = {
    "not_authorised": "You are not authorised to use this.",
    "review_not_found": "Review data not found.",
    "marked": "Marked as {status}.",
    "invalid_user_id": "Invalid User ID. Must be a number.",
    "review_channel_missing": "Review channel not found. ID: {channel_id}",
    "review_created": "Review created in {channel}.",
    "wrong_guild": "This command can only be used in the community server.",
    "careers_channel_missing": "Careers channel not found. Check CAREERS_CHANNEL_ID in config.",
    "careers_exists": "A careers embed already exists in this channel. Delete it first if you want to repost.",
    "careers_posted": "Careers embed posted.",
}