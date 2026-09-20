import asyncio
import os
from dotenv import load_dotenv

load_dotenv()


import discord
from discord.ext import commands

from core.bot_config import COMMUNITY_GUILD_ID, OWNER_ID, TOKEN

intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents, owner_id=OWNER_ID)


@bot.event
async def on_ready():
    if COMMUNITY_GUILD_ID:
        await bot.tree.sync(guild=discord.Object(id=COMMUNITY_GUILD_ID))
    try:
        global_synced = await bot.tree.sync()
        print(f"[Main] Global sync: {len(global_synced)} commands")
    except Exception as exc:
        print(f"[Main] Global sync failed: {exc}")
    print(f"Bot ready: {bot.user}")


@bot.event
async def on_error(event, *args, **kwargs):
    import traceback

    print(f"Error in {event}")
    traceback.print_exc()


@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: Exception):
    import traceback

    print(f"[App Command Error] {error}")
    traceback.print_exc()


async def main():
    try:
        async with bot:
            print("Loading extensions...")
            await bot.load_extension("tickets.ticket")
            print("tickets loaded")
            await bot.load_extension("rules.rules")
            print("rules loaded")
            await bot.load_extension("careers.careers")
            print("careers loaded")
            await bot.load_extension("community.community")
            print("community loaded")
            await bot.load_extension("community.information")
            print("information loaded")
            await bot.load_extension("moderation.moderation")
            print("moderation loaded")
            await bot.load_extension("moderation.automod")
            print("automod loaded")
            print("Starting bot...")
            await bot.start(TOKEN)
    except discord.LoginFailure:
        print("INVALID TOKEN - go reset it in the developer portal")
    except discord.PrivilegedIntentsRequired:
        print("INTENTS ERROR - enable all intents in the developer portal")
    except Exception as exc:
        import traceback

        print(f"UNKNOWN ERROR: {exc}")
        traceback.print_exc()
    finally:
        if TOKEN:
            print("Bot stopped.")
        else:
            print("Bot stopped. TOKEN was not set; check your .env file.")


if __name__ == "__main__":
    asyncio.run(main())
