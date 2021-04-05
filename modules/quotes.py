from discord.ext import commands, tasks
from colorama import Fore
from datetime import datetime as dt
import discord, os, asyncio, configparser, datetime, requests


class quotes(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def quote(self, ctx, *args):
        output = ""
        for word in args:
            output += word.replace("'", '')
            output += " "
        output = output.replace(" ", "+")
        quote = requests.get(f"https://twitch.center/customapi/quote?token=b6ab24d1&data={output}")
        await ctx.send(quote)


def setup(bot):
    bot.add_cog(quotes(bot))