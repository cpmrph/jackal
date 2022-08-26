import os

import discord

from discord.ext import commands
from dotenv import load_dotenv


load_dotenv()


class Jackal(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="/",
            intents=discord.Intents.all(),
            application_id=os.getenv("APP_ID"),
        )

        self.initial_extensions = ["cogs.map"]

    async def setup_hook(self):
        for ext in self.initial_extensions:
            await self.load_extension(ext)

        await bot.tree.sync(guild=discord.Object(id=os.getenv("GUILD_ID")))

    async def on_ready(self):
        print(f"{self.user} has connected to Discord!")


bot = Jackal()
bot.run(os.getenv("DISCORD_TOKEN"))
