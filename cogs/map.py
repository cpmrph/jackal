import os

import discord
import pendulum

from collections import namedtuple
from discord import app_commands
from discord.app_commands import Choice
from discord.ext import commands
from enum import Enum


def the_day_before(dt):
    return (
        pendulum.from_format(dt, "YYYYMMDD", tz="Asia/Tokyo")
        .subtract(days=1)
        .format("YYYYMMDD")
    )


Period = namedtuple("Period", ["start", "end"])


# NOTE: https://ja.wikipedia.org/wiki/%E3%83%AC%E3%82%A4%E3%83%B3%E3%83%9C%E3%83%BC%E3%82%B7%E3%83%83%E3%82%AF%E3%82%B9_%E3%82%B7%E3%83%BC%E3%82%B8#%E3%82%A2%E3%83%83%E3%83%97%E3%83%87%E3%83%BC%E3%83%88
class Season(Enum):
    VECTOR_GLARE = Period(
        "20220614", pendulum.yesterday("Asia/Tokyo").format("YYYYMMDD")
    )
    DEMON_VEIL = Period("20220315", the_day_before(VECTOR_GLARE.start))
    HIGH_CALIBRE = Period("20211130", the_day_before(DEMON_VEIL.start))
    CRYSTAL_GUARD = Period("20210907", the_day_before(HIGH_CALIBRE.start))
    NORTH_STAR = Period("20210615", the_day_before(CRYSTAL_GUARD.start))
    CRIMSON_HEIST = Period("20210316", the_day_before(NORTH_STAR.start))


# NOTE: TypeError: invalid Choice value type given, expected int, str, or float
SEASON_TABLE = {
    Season.DEMON_VEIL.name: Season.DEMON_VEIL.value,
    Season.VECTOR_GLARE.name: Season.VECTOR_GLARE.value,
    Season.HIGH_CALIBRE.name: Season.HIGH_CALIBRE.value,
    Season.CRYSTAL_GUARD.name: Season.CRYSTAL_GUARD.value,
    Season.NORTH_STAR.name: Season.NORTH_STAR.value,
    Season.CRIMSON_HEIST.name: Season.CRIMSON_HEIST.value,
}


class map(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="map", description="ランクマップごとの戦績を取得")
    @app_commands.describe(user="ユーザ名", season="集計対象シーズン")
    @app_commands.choices(
        season=[
            Choice(name=Season.VECTOR_GLARE.name, value=Season.VECTOR_GLARE.name),
            Choice(name=Season.DEMON_VEIL.name, value=Season.DEMON_VEIL.name),
            Choice(name=Season.HIGH_CALIBRE.name, value=Season.HIGH_CALIBRE.name),
            Choice(name=Season.CRYSTAL_GUARD.name, value=Season.CRYSTAL_GUARD.name),
            Choice(name=Season.NORTH_STAR.name, value=Season.NORTH_STAR.name),
            Choice(name=Season.CRIMSON_HEIST.name, value=Season.CRIMSON_HEIST.name),
        ]
    )
    async def map(
        self,
        interaction: discord.Interaction,
        user: str,
        season: str,
    ) -> None:
        await interaction.response.send_message(
            f"{user}'s map stats ({SEASON_TABLE[season].start} - {SEASON_TABLE[season].end})"
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(map(bot), guilds=[discord.Object(id=os.getenv("GUILD_ID"))])
