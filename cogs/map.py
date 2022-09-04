import asyncio
import json
import os

import discord
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
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
    VECTOR_GLARE
    DEMON_VEIL
    HIGH_CALIBRE
    CRYSTAL_GUARD
    NORTH_STAR
    CRIMSON_HEIST


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
            Choice(name=Season.VECTOR_GLARE.name, value=Season.VECTOR_GLARE.name),
            # TODO: Temporarily disabled
            # Choice(name=Season.DEMON_VEIL.name, value=Season.DEMON_VEIL.name),
            # Choice(name=Season.HIGH_CALIBRE.name, value=Season.HIGH_CALIBRE.name),
            # Choice(name=Season.CRYSTAL_GUARD.name, value=Season.CRYSTAL_GUARD.name),
            # Choice(name=Season.NORTH_STAR.name, value=Season.NORTH_STAR.name),
            # Choice(name=Season.CRIMSON_HEIST.name, value=Season.CRIMSON_HEIST.name),
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

    def _period_of_season(season: str) -> Period:
        season_table = {
            Season.VECTOR_GLARE.name: Period(
                "20220614", pendulum.yesterday("Asia/Tokyo").format("YYYYMMDD")
            ),
            Season.DEMON_VEIL.name: Period(
                "20220315", the_day_before(VECTOR_GLARE.start)
            ),
            Season.HIGH_CALIBRE.name: Period(
                "20211130", the_day_before(DEMON_VEIL.start)
            ),
            Season.CRYSTAL_GUARD.name: Period(
                "20210907", the_day_before(HIGH_CALIBRE.start)
            ),
            Season.NORTH_STAR.name: Period(
                "20210615", the_day_before(CRYSTAL_GUARD.start)
            ),
            Season.CRIMSON_HEIST.name: Period(
                "20210316", the_day_before(NORTH_STAR.start)
            ),
        }
        return season_table[season]

    def _round_stats(self, stats, side: Side):
        df = pd.DataFrame(stats)
        df = df.assign(win=df["rounds_won"] / df["rounds_played"] * 100.0)
        df = df[["map_name", "rounds_played", "win"]]
        df = df.rename(
            columns={
                "rounds_played": f"{side.value}_rounds",
                "win": f"{side.value}_win",
            }
        )
        return df

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
            df = df[["map_name", "matches_played", "win"]]
            df = df.rename(columns={"matches_played": "matches"})
            df = df.sort_values(["win", "matches"], ascending=[False, False])

            # atk_stats = [m.__dict__ for m in player.maps.ranked.attacker]
            # atkdf = self._round_stats(atk_stats, Side.ATK)

            # def_stats = [m.__dict__ for m in player.maps.ranked.defender]
            # defdf = self._round_stats(def_stats, Side.DEF)

            # df = pd.merge(df, atkdf, on="map_name")
            # df = pd.merge(df, defdf, on="map_name")

            # print(df.to_string(index=False))

            ax = df.plot(
                kind="bar",
                x="map_name",
                y=["win", "matches"],
                secondary_y="matches",
                title=f"{user} ({start_date} - {end_date})",
                xlabel="Map",
                ylabel="Win Rate",
                mark_right=False,
                colormap="tab20c",
            )
            ax.yaxis.set_major_formatter(mtick.PercentFormatter())
            ax.axhline(50.0, linestyle="--", color="black")
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
