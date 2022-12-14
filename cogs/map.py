import asyncio
import json
import os

import discord
import matplotlib.pyplot as plt
import pandas as pd
import pendulum

from collections import namedtuple
from discord import app_commands
from discord.app_commands import Choice
from discord.ext import commands
from enum import Enum
from siegeapi import Auth


def the_day_before(dt):
    return (
        pendulum.from_format(dt, "YYYYMMDD", tz="Asia/Tokyo")
        .subtract(days=1)
        .format("YYYYMMDD")
    )


Period = namedtuple("Period", ["start", "end"])

FILE_NAME = "map_stats.png"

# NOTE: https://ja.wikipedia.org/wiki/%E3%83%AC%E3%82%A4%E3%83%B3%E3%83%9C%E3%83%BC%E3%82%B7%E3%83%83%E3%82%AF%E3%82%B9_%E3%82%B7%E3%83%BC%E3%82%B8#%E3%82%A2%E3%83%83%E3%83%97%E3%83%87%E3%83%BC%E3%83%88
class Season(Enum):
    BRUTAL_SWARM = "20220906"
    VECTOR_GLARE = "20220614"
    DEMON_VEIL = "20220315"
    HIGH_CALIBRE = "20211130"
    CRYSTAL_GUARD = "20210907"
    NORTH_STAR = "20210615"
    CRIMSON_HEIST = "20210316"


class Side(Enum):
    ATK = "atk"
    DEF = "def"


class map(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="map", description="ランクマップごとの戦績を取得")
    @app_commands.describe(user="ユーザ名", season="集計対象シーズン")
    # NOTE: Cannot use Enum.
    # TypeError: invalid Choice value type given, expected int, str, or float
    @app_commands.choices(
        season=[
            Choice(name=Season.BRUTAL_SWARM.name, value=Season.BRUTAL_SWARM.name),
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
        period = self._period_of_season(season)
        (ok, e) = await self._fetch_map_stats(user, period.start, period.end)
        if ok:
            fp = discord.File(FILE_NAME)
            await interaction.response.send_message(
                "",
                file=fp,
            )
        else:
            await interaction.response.send_message(f"Error: {e}")

    def _period_of_season(self, season: str) -> Period:
        season_table = {
            Season.BRUTAL_SWARM.name: Period(
                Season.BRUTAL_SWARM.value,
                pendulum.yesterday("Asia/Tokyo").format("YYYYMMDD"),
            ),
            Season.VECTOR_GLARE.name: Period(
                Season.VECTOR_GLARE.value,
                the_day_before(Season.BRUTAL_SWARM.value),
            ),
            Season.DEMON_VEIL.name: Period(
                Season.DEMON_VEIL.value, the_day_before(Season.VECTOR_GLARE.value)
            ),
            Season.HIGH_CALIBRE.name: Period(
                Season.HIGH_CALIBRE.value, the_day_before(Season.DEMON_VEIL.value)
            ),
            Season.CRYSTAL_GUARD.name: Period(
                Season.CRYSTAL_GUARD.value, the_day_before(Season.HIGH_CALIBRE.value)
            ),
            Season.NORTH_STAR.name: Period(
                Season.NORTH_STAR.value, the_day_before(Season.CRYSTAL_GUARD.value)
            ),
            Season.CRIMSON_HEIST.name: Period(
                Season.CRIMSON_HEIST.value, the_day_before(Season.NORTH_STAR.value)
            ),
        }
        return season_table[season]

    async def _fetch_map_stats(self, user: str, start_date: str, end_date: str):
        # print(f"auth: {os.getenv('EMAIL')}:{os.getenv('PASSWORD')}")
        print(f"_fetch_map_stats: {user} ({start_date} - {end_date})")

        ok = True
        error = ""
        try:
            auth = Auth(os.getenv("EMAIL"), os.getenv("PASSWORD"))
            player = await auth.get_player(name=user)

            player.set_timespan_dates(start_date=start_date, end_date=end_date)

            await player.load_maps()

            pd.options.display.precision = 3

            all_stats = [m.__dict__ for m in player.maps.ranked.all]
            df = pd.DataFrame(all_stats)
            df = df.assign(win=df["matches_won"] / df["matches_played"] * 100.0)
            df = df[["map_name", "matches_played", "matches_won", "win"]]
            df = df.rename(columns={"matches_played": "matches"})
            df = df.sort_values(["matches", "win"], ascending=[False, False])

            ax = df.plot(
                kind="bar",
                x="map_name",
                y="matches",
                title=f"{user} ({start_date} - {end_date})",
                xlabel="Map",
                ylabel="Matches",
                mark_right=False,
                color="silver",
                width=0.8,
            )

            wr_color = [
                {wr > 50: "dodgerblue", wr == 50: "sandybrown", wr < 50: "lightcoral"}[
                    True
                ]
                for wr in df["win"]
            ]

            df.plot(
                kind="bar",
                x="map_name",
                y="matches_won",
                xlabel="Map",
                ax=ax,
                width=0.8,
                color=wr_color,
            )

            ax.bar_label(ax.containers[0], labels=df["matches"], fontsize=8)
            ax.bar_label(
                ax.containers[1],
                labels=round(df["win"], 1),
                label_type="center",
                color="snow",
                fontsize=8,
            )

            ax.get_figure().tight_layout()

            plt.savefig(FILE_NAME)

        except Exception as e:
            ok = False
            error = e

        finally:
            await auth.close()

        return (ok, error)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(map(bot), guilds=[discord.Object(id=os.getenv("GUILD_ID"))])
