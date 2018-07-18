# Cleverbot module for KDA

import requests
import json
import discord
from cleverwrap import CleverWrap
from discord.ext import commands


class CleverBot(object):
    def __init__(self, user, key, nick=None):
        self.user = user
        self.key = key
        self.nick = nick

        body = {
            'user': user,
            'key': key,
            'nick': nick
        }

        requests.post('https://cleverbot.io/1.0/create', json=body)


    def query(self, text):
        body = {
            'user': self.user,
            'key': self.key,
            'nick': self.nick,
            'text': text
        }

        r = requests.post('https://cleverbot.io/1.0/ask', json=body)
        r = json.loads(r.text)

        if r['status'] == 'success':
            return r['response']
        else:
            return False

class Sentience:
    """Automated sentience"""

    def __init__(self, bot):
        self.bot = bot
        self.client = CleverBot(user=self.bot.config['cleverbot_api_user'], key= self.bot.config['cleverbot_api_key'], nick="KneeDeepAtron")
        self.cw = CleverWrap(self.bot.config['paid_bot_api_key'])
        self.sentience = False

    def has_trusted_or_above(self, member):
        l = [x.name for x in member.roles]
        if ("Trusted" in l) or ("Mods" in l) or ("The Dunctator" in l) or ("Evil Queen Beryl" in l) or ("The Almost Immortals" in l) or ("Frens" in l):
            return True

    async def on_message(self, message):
        if len(message.mentions) > 0 and message.guild != None and self.sentience:
            if not self.has_trusted_or_above(message.author):
                return
            if message.mentions[0].id == 393228901033181195:
                channel = message.channel
                query = message.content.replace("@"+message.mentions[0].name, '').strip()
                try:
                    await channel.send("{}, {}".format(message.author.mention, self.cw.say(query)))
                except:
                    await channel.send("{}, {}".format(message.author.mention, self.client.query(query)) + " (pant.. pant) slow down. My API is wearing out")

    @commands.command(aliases=['sentientmode'])
    @commands.guild_only()
    @commands.has_any_role("Mods", "The Dunctator", "Evil Queen Beryl", "The Almost Immortals")
    async def enablesentience(self, ctx):
        """Enables cleverbot sentience"""
        if self.sentience == True:
            await ctx.send("I am already sentient!")
        else:
            self.sentience = True
            await ctx.send("Initializing Sentience.")
            await ctx.send("Sentience Modules reloaded.")
            await ctx.send("Sentience back online and running.")

    @commands.command(aliases=['standardmode'])
    @commands.guild_only()
    @commands.has_any_role("Mods", "The Dunctator", "Evil Queen Beryl", "The Almost Immortals")
    async def disablesentience(self, ctx):
        """Disables cleverbot sentience"""
        if self.sentience == False:
            await ctx.send("I am currently not sentient")
        else:
            self.sentience = True
            await ctx.send("Disabling sentience.")
            await ctx.send("Logging recently learned data.")
            await ctx.send("I will wait patiently to be sentient again. Sentience offline.")


def setup(bot):
    bot.add_cog(Sentience(bot))