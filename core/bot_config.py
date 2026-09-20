import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN", "")
COMMUNITY_GUILD_ID = int(os.getenv("COMMUNITY_GUILD_ID", "0"))
OWNER_ID = int(os.getenv("OWNER_ID", "0"))
LEAD_ROLE_IDS = [int(x.strip()) for x in os.getenv("LEAD_ROLE_IDS", "").split(",") if x.strip().isdigit()]
LEAD_ROLE_NAMES = ["Owner", "Project Lead", "Department Leads", "Department Lead"]
