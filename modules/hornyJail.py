from discord.ext import commands, tasks
from colorama import Fore
from datetime import datetime as dt
from pymongo import MongoClient
import discord, os, asyncio, pymongo, configparser, datetime

#Read connection config
config = configparser.ConfigParser()
config.read('config.ini')

#DB stuff
client = pymongo.MongoClient(config["mongodb"]["url"])
db = client.pengubot
hornyjailDB = db.hornyjail


class hornyJail(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.horny_jail_loop.start()

    def cog_unload(self):
        self.horny_jail_loop.cancel()

    @commands.command()
    async def hornyjail(self, ctx, user: discord.Member = None, time=None):
        if user == None or time == None:
            await ctx.send("You must include a user and the time. IE: !hornjail @mja00 100d")
        else:
            horny_jail_role = discord.utils.get(ctx.guild.roles, name="In Horny Jail")
            time_convert = {"s": 1, "m": 60, "h": 3600, "d": 86400}
            temp_role_time = int(time[:-1]) * time_convert[time[-1]]
            time_released = dt.now() + datetime.timedelta(seconds=temp_role_time)
            time_released_formatted = time_released.strftime("%m/%d/%Y at %H:%M:%S")
            prisoner = {"discordID": user.id,
                        "expires": time_released,
                        "username": user.name}
            key = {"discordID": user.id}
            hornyjailDB.update(key, prisoner, upsert=True)
            await ctx.send(f"Hands up! <@{user.id}>, you're coming with me. I've got a nice cell in Horny Jail for you. They will be released from Horny Jail on {time_released_formatted} EST")
            await user.add_roles(horny_jail_role)
            print(f"{Fore.RED}{dt.now().strftime('%H:%M:%S')} | ❌ | {user.name} has been placed in Horny Jail till {time_released_formatted}")

    @commands.command()
    async def pardon(self, ctx, user: discord.Member = None):
        if user == None:
            await ctx.send("You must specify a user to pardon.")
        else:
            horny_jail_role = discord.utils.get(ctx.guild.roles, name="In Horny Jail")
            hornyjailDB.delete_one({"discordID": user.id})
            await user.remove_roles(horny_jail_role)
            await ctx.send(f"Looks like you're lucky <@{user.id}>. The Warden has decided to pardon you.")

    @tasks.loop(seconds=60)
    async def horny_jail_loop(self):
        print(f"{Fore.CYAN}{dt.now().strftime('%H:%M:%S')} | ❕ | Checking if anyone is set for release")
        for document in hornyjailDB.find():
            if document["expires"] < dt.now():
                discordID = document["discordID"]
                guild = self.bot.get_guild(529860954549125143)
                user = guild.get_member(discordID)
                print(f"{Fore.GREEN}{dt.now().strftime('%H:%M:%S')} | ✅ | {document['username']} has been released.")
                hornyjailDB.delete_one({"discordID": discordID})
                horny_jail_role = discord.utils.get(guild.roles, name="In Horny Jail")
                await user.remove_roles(horny_jail_role)
            else:
                print(f"{Fore.BLUE}{dt.now().strftime('%H:%M:%S')} | ❌ | {document['username']} isn't ready for release yet.")

    @horny_jail_loop.before_loop
    async def before_horny_jail_loop(self):
        await self.bot.wait_until_ready()



def setup(bot):
    bot.add_cog(hornyJail(bot))
