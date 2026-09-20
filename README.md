# Control Heist Bot

Discord bot for the Heist Control community server: support and bug-report tickets, rules and information panels, careers applications, community tools, and moderation.

## Setup

1. Install dependencies: `pip install discord.py python-dotenv`
2. Copy `.env.example` to `.env` and fill it in:

   | Variable | Purpose |
   | --- | --- |
   | `TOKEN` | Bot token from the Discord developer portal |
   | `COMMUNITY_GUILD_ID` | ID of the server the bot runs in |
   | `OWNER_ID` | Discord user ID of the bot owner |
   | `LEAD_ROLE_IDS` | Comma-separated role IDs treated as leads |

3. Run `python main.py`

## Configuration

Every package keeps its editable settings in a `*_config.py` file, so panel text, embed wording, button labels, form fields, colors, channel IDs and role IDs can be changed without touching the logic.

| Package | Config file | What it controls |
| --- | --- | --- |
| `tickets` | `ticket_config.py` | Support and bug panels, ticket form fields, instructions, staff roles, cooldown |
| `rules` | `rules_config.py` | Rule categories and text, panel wording, appeal link |
| `community` | `information_config.py`, `community_config.py` | Information pages, FAQ, roles, socials, poll and feedback wording |
| `careers` | `careers_config.py` | Careers embed, application form link, review workflow wording |
| `moderation` | `moderation_config.py` | Log channels, embed colors and footers, timeout limit, messages |
| `core` | `bot_config.py` | Environment-driven settings shared by every package |

## Layout

```
main.py          entry point, loads every extension
core/            environment config and guild scope checks
tickets/         support tickets and bug/exploit reports
rules/           rules panel
community/       information panel, polls, announcements, feedback
careers/         careers panel and application review
moderation/      moderation commands, automod logging, case database
```
