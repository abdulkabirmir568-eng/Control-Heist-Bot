APPEAL_SERVER = "https://discord.gg/9pJ5JwCqJB"
DATABASE_PATH = "moderation/heist_moderation.sqlite3"
MOD_LOG_CHANNEL_ID = 1497586192323969134
MOD_LOG_CHANNEL_NAME = "moderation-logs"
AUTOMOD_CHANNEL_ID = 1514655073769230376
CASE_PAGE_SIZE = 5
HISTORY_PAGE_SIZE = 6

COMMUNITY_INVITE = "https://discord.gg/H4VwjcbgYT"

EMBED_FOOTER = "Heist Control - Moderation System"
CASE_PAGE_FOOTER = "Heist Control - Page {page}"

MAX_TIMEOUT_DAYS = 28

RED = 0xE74C3C
DARK_RED = 0x8B0000
ORANGE = 0xF39C12
YELLOW = 0xF1C40F
GREEN = 0x2ECC71
BLUE = 0x3498DB
GRAY = 0x2B2D31
PURPLE = 0x9B59B6

ACTION_COLORS = {
    "BAN": RED,
    "TEMPBAN": RED,
    "KICK": RED,
    "TIMEOUT": ORANGE,
    "UNTIMEOUT": GREEN,
    "WARN": YELLOW,
    "UNBAN": GREEN,
    "PURGE": BLUE,
    "NOTE": BLUE,
}

MODERATION_MESSAGES = {
    "forbidden": "Discord blocked this action because my role or permissions are not high enough.",
    "not_found": "The requested Discord object could not be found.",
    "http": "Discord rejected the request. Please check the target and try again.",
    "generic": "The moderation system could not complete that action.",
    "server_only": "Moderation commands can only be used inside a server.",
    "access_denied": "You do not have permission to use this moderation action.",
    "invalid_timeout": "Timeout duration must be between 1 second and {days} days.",
}

AUTOMOD_MESSAGES = {
    "forbidden": "Discord blocked this action because my role or permissions are not high enough.",
    "not_found": "The requested Discord object could not be found.",
    "http": "Discord rejected the request. Please check and try again.",
    "generic": "The automod system could not complete that action.",
    "server_only": "AutoMod commands can only be used inside a server.",
    "access_denied": "You need the admin/lead role to use this command.",
}
