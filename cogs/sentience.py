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

    async def on_message(self, message):
        if len(message.mentions) > 0:
            if message.mentions[0].id == 393228901033181195:
                channel = message.channel
                query = message.content.replace("@"+message.mentions[0].name, '').strip()
                try:
                    await channel.send("{}, {}".format(message.author.mention, self.cw.say(query)))
                except:
                    await channel.send("{}, {}".format(message.author.mention, self.client.query(query)))

def setup(bot):
    bot.add_cog(Sentience(bot))