import discord
import asyncio
from discord.ext import commands
from discord.opus import OpusNotLoaded

class Radio:
    """Assignables"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='startradio', aliases=['weeb'])
    async def weeb(self, ctx):
        """Listen.moe player"""
        try:
            channel = ctx.author.voice.channel
            if channel != None:
                voice_client = await channel.connect()
                player = discord.FFmpegPCMAudio("http://listen.moe/stream")
                voice_client.play(player, after=lambda e: print('done', e))
                voice_client.source = discord.PCMVolumeTransformer(voice_client.source)
                voice_client.source.volume = 1.0
            else:
                await self.bot.say("Join a voice channel before attempting this command")
        except asyncio.TimeoutError:
            await self.bot.say("Timeout while joining")
        except discord.opus.OpusNotLoaded:
            await self.bot.say("Opus Lib not found")


def setup(bot):
    bot.add_cog(Radio(bot))