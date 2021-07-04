from discord.ext import commands
from colorama import init, Fore, Style, Back
from datetime import datetime as dt
from os import listdir
from os.path import isfile, join
import discord, os, sys, traceback, asyncio

print(f"{Fore.GREEN}Starting")

# Needed Discord intents
intents = discord.Intents.default()
intents.members = True

startingActivity = discord.Activity(type=discord.ActivityType.watching, name="my code")
bot = commands.Bot(command_prefix="!", status=discord.Status.do_not_disturb, activity=startingActivity, intents=intents)
bot.remove_command("help")

# Read token file
try:
    tokenFile = open("token", "r")
    tokenForm = tokenFile.readline()
    token = str.strip(tokenForm)
    print(f"{Fore.GREEN}✅ | Token file found and loaded")
except FileNotFoundError:
    print(f"{Fore.RED}❌ | Token file not found. Qutting")
    sys.exit(1)

# We now do windows related things
import platform

if platform.system() == "Windows":
    init(convert=True)
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy)

# Cogs dir check and loading
print(f"{Fore.YELLOW}🔄 | Checking for cogs directory")
if not os.path.exists("modules"):
    print(f"{Fore.LIGHTRED_EX}❌ | Cogs directory not found. Creating")
    os.makedirs("modules")
else:
    print(f"{Fore.GREEN}✅ | Cogs directory found")
cogsDir = "modules"

# Hard coded list of cogs to load, pretty bad but I don't use a proper config file
initHandlers = ['hornyJail', 'quotes', 'markov']

# Load all extensions automatically before starting bot
print(f"{Fore.YELLOW}🔄 | Loading cogs")
for extension in initHandlers:
    try:
        bot.load_extension(cogsDir + "." + extension)
        print(f"{Fore.GREEN}✅ | {extension} loaded")
    except commands.ExtensionAlreadyLoaded:
        print(f"{Fore.LIGHTRED_EX}❌ | The extension {extension} is already loaded")
    except commands.ExtensionNotLoaded:
        bot.load_extension(cogsDir + "." + extension)
    except commands.ExtensionNotFound:
        print(f"{Fore.YELLOW}⚠️ | The extension {extension} was not found")
    except commands.ExtensionFailed as error:
        print(f"{Fore.RED}❌ | {extension} cannot be loaded [{error}]")

# Create the logs dir
print(f"{Fore.YELLOW}🔄 | Checking for log directories")
if not os.path.exists("logs"):
    print(f"{Fore.LIGHTRED_EX}❌ | Main logs directory not found. Creating it.")
    os.makedirs("logs")
else:
    print(f"{Fore.GREEN}✅ | Main directory found")
if not os.path.exists("logs/chat"):
    print(f"{Fore.LIGHTRED_EX}❌ | Chat log directory not found. Creating it")
    os.makedirs("logs/chat")
else:
    print(f"{Fore.GREEN}✅ | Chat log directory found")


# All initialization is done now

@bot.event
async def on_ready():
    print(f"{Fore.GREEN}✅ | Bot has been initialized and is ready")
    await bot.change_presence(status=discord.Status.online,
                              activity=discord.Activity(type=discord.ActivityType.watching, name="general chat"))


# Shutdown bot - rarely needed
@bot.command()
@commands.is_owner()
async def shutdown(ctx):
    await bot.change_presence(status=discord.Status.do_not_disturb, activity=discord.Activity(type=discord.ActivityType.watching, name="my code turn off"))
    await ctx.channel.send("Shutting down :(")
    await bot.close()


# Load cog
@bot.command()
@commands.is_owner()
async def load(ctx, extension):
    try:
        bot.load_extension(cogsDir + "." + extension)
        await ctx.channel.send(f"{extension} loaded.")
    except commands.ExtensionAlreadyLoaded:
        await ctx.channel.send(f"The extension {extension} is already loaded.")
    except commands.ExtensionNotLoaded:
        bot.load_extension(cogsDir + "." + extension)
    except commands.ExtensionNotFound:
        await ctx.channel.send("The extension was not found")
    except commands.ExtensionFailed as error:
        await ctx.channel.send(f"{extension} cannot be loaded. [{error}]")


# Unload cog command
@bot.command()
@commands.is_owner()
async def unload(ctx, extension):
    try:
        bot.unload_extension(cogsDir + "." + extension)
        await ctx.channel.send(f"{extension} unloaded.")
    except commands.ExtensionNotFound:
        await ctx.channel.send(f"The extension {extension} was not found.")
    except commands.ExtensionFailed as error:
        await ctx.channel.send("{} cannot be unloaded. [{}]".format(extension, error))


# Reload cog
@bot.command()
@commands.is_owner()
async def reload(ctx, extension):
    try:
        bot.reload_extension(cogsDir + "." + extension)
        await ctx.channel.send(f"{extension} reloaded.")
    except commands.ExtensionAlreadyLoaded:
        await ctx.channel.send(f"The extension {extension} is already loaded.")
    except commands.ExtensionNotLoaded:
        bot.load_extension(cogsDir + "." + extension)
    except commands.ExtensionNotFound:
        await ctx.channel.send(f"The extension {extension} was not found.")
    except commands.ExtensionFailed as error:
        await ctx.channel.send("{} cannot be reloaded. [{}]".format(extension, error))


# Handle command errors
@bot.event
async def on_command_error(ctx, error):
    if hasattr(ctx.command, 'on_error'):
        return
    ignored = (commands.CommandNotFound, commands.UserInputError)

    error = getattr(error, 'original', error)

    if isinstance(error, ignored):
        return

    elif isinstance(error, commands.DisabledCommand):
        return await ctx.send(f'{ctx.command} has been disabled.')
    elif isinstance(error, commands.NotOwner):
        return await ctx.send(f'This command can only be ran by mja00')
    elif isinstance(error, commands.MissingAnyRole):
        return await ctx.send(error)
    elif isinstance(error, commands.CommandOnCooldown):
        return await ctx.send(f'{ctx.command} is on cooldown.')
    elif isinstance(error, commands.NoPrivateMessage):
        try:
            return await ctx.author.send(f'{ctx.command} cannot be used in DMs')
        except discord.DiscordException:
            pass
    elif isinstance(error, commands.BadArgument):
        if ctx.command.qualified_name == 'tag list':
            return await ctx.send("I could not find that member. Please try again")
    print('Ignoring exception in command {}:'.format(ctx.command), file=sys.stderr)
    traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)


bot.run(token)
