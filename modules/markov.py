from discord.ext import commands, tasks
from colorama import Fore
from datetime import datetime as dt
import discord, os, asyncio, configparser, datetime, requests, aiohttp, markovify, motor.motor_asyncio

# Read connection config
config = configparser.ConfigParser()
config.read('config.ini')

# DB stuff
client = motor.motor_asyncio.AsyncIOMotorClient(config["mongodb"]["url"], serverSelectionTimeoutMS=5000)
db = client.pengubot
markovDB = db.markov


class markov(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.markov_model = None
        self.markov_compile_loop.start()
    
    def cog_unload(self):
        self.markov_compile_loop.cancel()

    @commands.Cog.listener()
    async def on_message(self, message):
        author = message.author
        if author.bot is False:
            if message.channel.name == "general" or message.channel.name == "no-mic-chat":
                message_content = message.clean_content
                if message_content[0] == "!":
                    return
                print(message_content)
                data = {
                    "message": message_content,
                    "inserted_at": dt.utcnow()
                }
                await markovDB.insert_one(data)

    @commands.Command
    async def markov(self, ctx):
        #message = await ctx.channel.send("I'm thinking up a message")
        async with ctx.typing():
            """ combined_model = None
            cursor = markovDB.find({})
            for document in cursor:
                try:
                    model = markovify.Text(document["message"], retain_original=True)
                except KeyError:
                    pass

                if combined_model:
                    combined_model = markovify.combine(models=[combined_model, model])
                else:
                    combined_model = model
            message_to_send = combined_model.make_sentence(tries=100, max_overlap_total=5) """
            #await message.delete()
            message_to_send = self.markov_model.make_sentence(tries=100, max_overlap_total=5)
        if message_to_send is not None:
            await ctx.message.reply(message_to_send)
        else:
            await ctx.message.reply("Unfortunately I didn't think of anything. << This is not a generated message. I was actually unable to generate a sentence.")

    @tasks.loop(minutes=5)
    async def markov_compile_loop(self):
        print(f"{Fore.YELLOW}Compiling Markov's model.")
        combined_model = None
        cursor = markovDB.find({}, {"_id": False, "message": 1})
        items = await cursor.to_list(length=None)
        result_list = []
        for dict in items:
            result_list.append(dict["message"])
        result_string = "\n".join(result_list)
        combined_model = markovify.NewlineText(result_string)
        text_model = combined_model.compile()
        self.markov_model = text_model
        print(f"{Fore.GREEN}Compilation complete")
    
    @markov_compile_loop.before_loop
    async def before_markov_compile_loop(self):
        await self.bot.wait_until_ready()


def setup(bot):
    bot.add_cog(markov(bot))
