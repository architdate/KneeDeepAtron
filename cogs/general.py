import discord
from discord.ext import commands

class General:
    """General commands"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="guide")
    @commands.guild_only()
    async def guide(self, ctx, *, console=""):
        """Links to Plailect's guide"""
        if console == "3ds" or console == "":
            embed = discord.Embed(title="Guide", color=discord.Color(0xCE181E))
            embed.set_author(name="Plailect", url="https://3ds.hacks.guide/")
            embed.set_thumbnail(url="https://3ds.hacks.guide/images/bio-photo.png")
            embed.url = "https://3ds.hacks.guide/"
            embed.description = "A complete guide to 3DS custom firmware, from stock to boot9strap."
            await ctx.send(embed=embed)
        elif console == "switch" or console == "nx":
            embed = discord.Embed(title="Guide", color=discord.Color(0xCB0004))
            embed.set_author(name="Plailect", url="https://switch.hacks.guide/")
            embed.set_thumbnail(url="https://3ds.hacks.guide/images/bio-photo.png")
            embed.url = "https://switch.hacks.guide/"
            embed.description = "Plailect's Switch 3.0.0 Homebrew guide"
            await self.bot.say(embed=embed)

    @commands.command(aliases=["a9lhtob9s","updatea9lh"])
    @commands.guild_only()
    async def atob(self, ctx):
        """Links to the guide for updating from a9lh to b9s"""
        embed = discord.Embed(title="Upgrading a9lh to b9s", color=discord.Color(0xCE181E))
        embed.set_author(name="Plailect", url="https://3ds.hacks.guide/a9lh-to-b9s")
        embed.set_thumbnail(url="https://3ds.hacks.guide/images/bio-photo.png")
        embed.url = "https://3ds.hacks.guide/a9lh-to-b9s"
        embed.description = "A guide for upgrading your device from arm9loaderhax to boot9strap."
        await ctx.send(embed=embed)

    @commands.command(aliases=["stock115","stock"])
    @commands.guild_only()
    async def stock114(self, ctx):
        """Advisory for consoles on stock 11.4+ firmware"""
        embed = discord.Embed(title="Running stock (unmodified) 11.4+ firmware?", color=discord.Color.dark_orange())
        embed.description = "You have 4 possible options for installing CFW:\n- [NTRBoot](https://3ds.hacks.guide/ntrboot) which requires a compatible NDS flashcart and maybe an additional DS(i) or hacked 3DS console depending on the flashcart\n- [DSiWare](https://3ds.hacks.guide/installing-boot9strap-\(dsiware\)) which involves system transferring from a hacked 3DS to an unhacked 3DS\n- [Seedminer](https://jisagi.github.io/SeedminerGuide/) which requires a compatible DSiWare game\n- [Hardmod](https://3ds.hacks.guide/installing-boot9strap-\(hardmod\)) which requires soldering **Not for beginners!**\n **Downgrading is impossible on 11.4+!**"
        await ctx.send(embed=embed)

    @commands.command()
    @commands.guild_only()
    async def updateb9s(self, ctx):
        """Links to the guide for updating b9s versions"""
        embed = discord.Embed(title="Updating B9S Guide", color=discord.Color(0xCE181E))
        embed.set_author(name="Plailect", url="https://3ds.hacks.guide/updating-b9s")
        embed.set_thumbnail(url="https://3ds.hacks.guide/images/bio-photo.png")
        embed.url = "https://3ds.hacks.guide/updating-b9s"
        embed.description = "A guide for updating to new B9S versions."
        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(General(bot))