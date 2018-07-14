import asyncio
import json
import logging
import os
import signal
import sys

import aiohttp
import discord
from aiomysql.sa import create_engine
from discord.ext import commands

from cogs.utils import checks


def initLogging():
    logformat = "%(asctime)s %(name)s:%(levelname)s:%(message)s"
    logging.basicConfig(level=logging.INFO, format=logformat,
                        datefmt='%Y-%m-%d %H:%M:%S')
    logging.getLogger("discord").setLevel(logging.WARNING)
    return logging.getLogger("kneedeepatron")


def sig_handler(signum, frame):
    logger.info("Exiting...")
    # logger.shutdown()
    sys.exit()


if __name__ == "__main__":
    logger = initLogging()
    logger.info("Initializing...")
    signal.signal(signal.SIGTERM, sig_handler)
    signal.signal(signal.SIGINT, sig_handler)
    try:
        import uvloop
    except ImportError:
        logger.info("Import Error: uvloop")
        pass
    else:
        logger.info("asyncio loop policy")
        asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
        logger.info("asyncio loop policy done")
    try:
        with open("config.json") as c:
            config = json.load(c)
    except FileNotFoundError:
        logger.critical("Config file not found, quitting!")
        sys.exit(-1)
    bot = commands.Bot(command_prefix=config['prefix'],
                       description='kneedeepatron',
                       max_messages=100)
    bot.config = config
    logger.info("Config Loaded")
    bot.is_setup = asyncio.Event(loop=bot.loop)

    async def wait_for_setup():
        await bot.is_setup.wait()
    bot.wait_for_setup = wait_for_setup

    @checks.check_permissions_or_owner(administrator=True)
    @bot.command(hidden=True)
    async def restart(ctx):
        logger.info("Restarting on {}'s request...".format(ctx.author.name))
        await ctx.send("Restarting...")
        await bot.logout()
        os._exit(1)

    @checks.check_permissions_or_owner(administrator=True)
    @bot.command(hidden=True)
    async def shutdown(ctx):
        logger.info("Terminating on {}'s request...".format(ctx.author.name))
        await ctx.send("Shutting down...")
        await bot.logout()
        os._exit(0)

    @bot.event
    async def on_command_error(ctx, error):
        error = getattr(error, 'original', error)
        if hasattr(ctx.command, 'on_error') or hasattr(ctx.cog, '_{0.__class__.__name__}__error'.format(ctx.cog)):
            return
        if isinstance(error, discord.ext.commands.CommandNotFound):
            return
        if isinstance(error, discord.ext.commands.CheckFailure):
            await ctx.send("{} You don't have permission to use this command.".format(ctx.message.author.mention))
        elif isinstance(error, discord.ext.commands.MissingRequiredArgument):
            await ctx.send("{} You are missing required arguments.".format(ctx.message.author.mention))
        elif isinstance(error, commands.BotMissingPermissions):
            await ctx.send("⚠ I don't have the permissions to do this.")
        else:
            if ctx.command:
                await ctx.send("An error occurred while processing the `{}` command.".format(ctx.command.name))
            logger.exception(error, exc_info=error)

    @bot.event
    async def on_ready():
        logger.info("Bot Ready")
        bot.main_server = discord.utils.get(bot.guilds, id=141254489465159680)
        for channel, cid in config['channels'].items():
            setattr(bot, "{}_channel".format(channel), bot.main_server.get_channel(cid))
        for role, roleid in config['roles'].items():
            setattr(bot, "{}_role".format(role), discord.utils.get(bot.main_server.roles, id=roleid))
        bot.session = aiohttp.ClientSession(loop=bot.loop, headers={"User-Agent": "kneedeepatron"})
        logger.info("Connected as UID {}.".format(bot.user.id))
        bot.is_setup.set()

    for extension in os.listdir("cogs"):
        if extension.endswith('.py') and extension != "__init__.py" and "_alt" not in extension:
            try:
                bot.load_extension("cogs." + extension[:-3])
            except Exception as e:
                logger.exception('Failed to load extension {}'.format(extension))

    try:
        logger.info("Attempting to run")
        bot.run(config['token'])
        logger.info("Running KneeDeepAtron")
    finally:
        sys.exit(-1)
