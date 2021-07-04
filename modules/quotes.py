from discord.ext import commands, tasks
from colorama import Fore
from datetime import datetime as dt
import discord, os, asyncio, configparser, datetime, requests, aiohttp


class quotes(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def quote(self, ctx, *args):
        sess = aiohttp.ClientSession()
        output = ""
        for word in args:
            output += word.replace("'", '')
            output += " "
        output = output.replace(" ", "+")
        # quote = requests.get(f"https://twitch.center/customapi/quote?token=b6ab24d1&data={output}")
        req = await sess.get(f"https://twitch.center/customapi/quote?token=b6ab24d1&data={output}")
        quote = await req.text()
        await ctx.send(quote)
        await sess.close()
    
    @commands.command()
    async def byejaye(self, ctx):
        await ctx.send("bye jaye 👋")


def setup(bot):
    bot.add_cog(quotes(bot))