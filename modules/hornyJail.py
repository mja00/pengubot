from discord.ext import commands, tasks
from colorama import Fore
from datetime import datetime as dt
from datetime import timezone
from pymongo import MongoClient
import discord, os, asyncio, pymongo, configparser, datetime

# Read connection config
config = configparser.ConfigParser()
config.read('config.ini')

# DB stuff
client = pymongo.MongoClient(config["mongodb"]["url"])
db = client.pengubot
hornyjailDB = db.hornyjail
sentences_db = db.sentences
users_db = db.users

intervals = (
    ('weeks', 604800),  # 60 * 60 * 24 * 7
    ('days', 86400),  # 60 * 60 * 24
    ('hours', 3600),  # 60 * 60
    ('minutes', 60),
    ('seconds', 1),
)


def display_time(seconds, granularity=2):
    result = []

    for name, count in intervals:
        value = seconds // count
        if value:
            seconds -= value * count
            if value == 1:
                name = name.rstrip('s')
            result.append("{} {}".format(int(value), name))
    return ', '.join(result[:granularity])


def is_in_jail(discord_id):
    document = hornyjailDB.find_one({"discordID": discord_id})
    if document is None:
        return False
    else:
        return True


def get_inmate(discord_id):
    return hornyjailDB.find_one({"discordID": discord_id})


def time_convert(time):
    time_convert = {"s": 1, "m": 60, "h": 3600, "d": 86400}
    return int(time[:-1]) * time_convert[time[-1]]


def upsert_db(user: discord.Member, time_released, author):
    prisoner = {"discordID": user.id,
                "expires": time_released,
                "username": user.name,
                "sentenced_by_name": author.name,
                "sentenced_by_id": author.id
                }
    key = {"discordID": user.id}
    hornyjailDB.update(key, prisoner, upsert=True)


def sentence_user(user, time, author):
    temp_role_time = time_convert(time)
    time_released = dt.utcnow() + datetime.timedelta(seconds=temp_role_time)
    time_released_formatted = time_released.strftime("%m/%d/%Y at %H:%M:%S")
    upsert_db(user, time_released, author)
    return time_released_formatted


def current_time_and_date():
    return dt.now().strftime('%m/%d/%Y %H:%M:%S')


class hornyJail(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.horny_jail_loop.start()

    def cog_unload(self):
        self.horny_jail_loop.cancel()

    @commands.command()
    @commands.has_any_role("Potato", "vlerry rules everyone")
    async def hornyjail(self, ctx, user: discord.Member = None, time=None):
        if user == None or time == None:
            await ctx.send("You must include a user and the time. IE: !hornjail @mja00 100d")
        else:
            horny_jail_role = discord.utils.get(ctx.guild.roles, name="In Horny Jail")
            time_released_formatted = sentence_user(user, time, ctx.message.author)
            await ctx.send(
                f"Hands up! <@{user.id}>, you're coming with me. I've got a nice cell in Horny Jail for you. They will be released from Horny Jail on {time_released_formatted} UTC")
            await user.add_roles(horny_jail_role)
            print(
                f"{Fore.RED}{current_time_and_date()} | ❌ | {user.name} has been placed in Horny Jail till {time_released_formatted}")

    @commands.command()
    @commands.has_any_role("Potato", "vlerry rules everyone")
    async def pardon(self, ctx, user: discord.Member = None):
        if user == None:
            await ctx.send("You must specify a user to pardon.")
        else:
            horny_jail_role = discord.utils.get(ctx.guild.roles, name="In Horny Jail")
            hornyjailDB.delete_one({"discordID": user.id})
            await user.remove_roles(horny_jail_role)
            await ctx.send(f"Looks like you're lucky <@{user.id}>. The Warden has decided to pardon you.")

    @commands.command()
    async def sentence(self, ctx, user: discord.Member = None):
        if user is None:
            author_id = ctx.message.author.id
            other = False
        else:
            author_id = user.id
            other = True
        document = hornyjailDB.find_one({"discordID": author_id})
        if document is None:
            await ctx.send("You are currently not in horny jail")
        else:
            release_time = document["expires"]
            delta = release_time - dt.utcnow()
            total_seconds = delta.total_seconds()
            formatted_time = display_time(total_seconds, 4)
            await ctx.send(
                f"<@{ctx.message.author.id}> >> {'They' if other else 'You'} are in jail for another {formatted_time}.")

    @commands.command()
    async def sentences(self, ctx):
        # Get all the documents
        all_sentences = hornyjailDB.find()
        # Start embed creation
        embed = discord.Embed(title="Current Sentences", color=0x0fb4eb)
        for sentence in all_sentences:
            release_time = sentence["expires"]
            delta = release_time - dt.utcnow()
            total_seconds = delta.total_seconds()
            formatted_time = display_time(total_seconds, 4)
            embed.add_field(name=sentence["username"], value=formatted_time, inline=False)
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_any_role("Potato", "vlerry rules everyone")
    async def extend(self, ctx, user: discord.Member = None, time=None):
        if user is None or time is None:
            await ctx.send("You must include the user and a time. IE: !extend @Xolost 69d")
        elif is_in_jail(user.id) is True:
            inmate_doc = get_inmate(user.id)
            current_sentence = inmate_doc["expires"]
            time_released = current_sentence + datetime.timedelta(seconds=time_convert(time))
            time_released_formatted = time_released.strftime("%m/%d/%Y at %H:%M:%S")
            upsert_db(user, time_released, ctx.message.author)
            await ctx.send(
                f"<@{user.id}>'s sentence has been extended. They will now be released at {time_released_formatted} EST.")
            print(
                f"{Fore.RED}{current_time_and_date()} | ❌ | {user.name} has had their sentence in Horny Jail extended by {time} till {time_released_formatted}")
        else:
            await ctx.send("This person currently isn't in jail.")

    # Loops for releasing people from horny jail

    @tasks.loop(seconds=10)
    async def horny_jail_loop(self):
        for document in hornyjailDB.find():
            if document["expires"] < dt.utcnow():
                discordID = document["discordID"]
                # Generate object for the previous sentences collection

                sentence_date = document["_id"].generation_time
                delta = dt.now(timezone.utc) - sentence_date
                total_seconds = delta.total_seconds()
                formatted_time = display_time(total_seconds, 4)
                data = {
                    "discord_id": discordID,
                    "sentence_date": sentence_date,
                    "released_date": dt.utcnow(),
                    "username": document["username"],
                    "sentenced_by_name": document["sentenced_by_name"],
                    "sentenced_by_id": document["sentenced_by_id"],
                    "time_in": formatted_time
                }
                sentences_db.insert_one(data)

                # Preform the unjailing
                guild = self.bot.get_guild(689541509523046480)
                user = guild.get_member(discordID)
                print(f"{Fore.GREEN}{current_time_and_date()} | ✅ | {document['username']} has been released.")
                hornyjailDB.delete_one({"discordID": discordID})
                horny_jail_role = discord.utils.get(guild.roles, name="In Horny Jail")
                try:
                    await user.remove_roles(horny_jail_role)
                    channel = discord.utils.get(guild.channels, name="general")
                    await channel.send(
                        f"Today's your day <@{discordID}>. You're free from Horny Jail. Try not to get sent back.")
                except AttributeError:
                    print(
                        f"{Fore.RED}{current_time_and_date()} | ❌ | Failed to remove the role from {discordID}. Most likely isn't in the guild.")

    @horny_jail_loop.before_loop
    async def before_horny_jail_loop(self):
        await self.bot.wait_until_ready()

    @commands.Cog.listener()
    async def on_member_update(self, before, after: discord.Member):
        dict = {
            "avatar_url": str(after.avatar_url),
            "name": after.name,
            "discriminator": after.discriminator,
            "nickname": after.display_name,
            "id": after.id
        }
        key = {"id": after.id}
        users_db.update(key, dict, upsert=True)

    @commands.Cog.listener()
    async def on_user_update(self, before, after: discord.User):
        dict = {
            "avatar_url": str(after.avatar_url),
            "name": after.name,
            "discriminator": after.discriminator,
            "nickname": after.display_name,
            "id": after.id
        }
        key = {"id": after.id}
        users_db.update(key, dict, upsert=True)


def setup(bot):
    bot.add_cog(hornyJail(bot))
