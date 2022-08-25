#!/usr/bin/env python


from dotenv import load_dotenv
from enum import Enum
from siegeapi import Auth
import asyncio
import json
import os
import pandas as pd
import typer


app = typer.Typer()
load_dotenv()


class Side(Enum):
    ATK = "atk"
    DEF = "def"


class SetupError(Exception):
    def __str__(self):
        return "Set environment variables: EMAIL, PASSWORD"


def round_stats(stats, side: Side):
    df = pd.DataFrame(stats)
    df = df.assign(win=df["rounds_won"] / df["rounds_played"] * 100.0)
    df = df[["map_name", "rounds_played", "win"]]
    df = df.rename(
        columns={"rounds_played": f"{side.value}_rounds", "win": f"{side.value}_win"}
    )
    return df


async def fetch_map_stats(user: str, start_date: str, end_date: str):
    email = os.getenv("EMAIL")
    password = os.getenv("PASSWORD")
    if email is None or password is None:
        raise SetupError

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

    atk_stats = [m.__dict__ for m in player.maps.ranked.attacker]
    atkdf = round_stats(atk_stats, Side.ATK)

    def_stats = [m.__dict__ for m in player.maps.ranked.defender]
    defdf = round_stats(def_stats, Side.DEF)

    df = pd.merge(df, atkdf, on="map_name")
    df = pd.merge(df, defdf, on="map_name")

    print(df.to_string(index=False))

    await auth.close()


@app.command()
def map(
    user: str = typer.Argument(..., help="Username"),
    start_date: str = typer.Argument("20220607"),
    end_date: str = typer.Argument("20220823"),
):
    asyncio.get_event_loop().run_until_complete(
        fetch_map_stats(user, start_date, end_date)
    )


if __name__ == "__main__":
    app()
