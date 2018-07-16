import asyncio
import copy
import json
import logging
import re
import time
import traceback
from datetime import datetime, timedelta

import discord
from discord.ext import commands
from sqlalchemy.dialects.mysql import insert
from sqlalchemy import null

from .utils import checks

class MemberID(commands.Converter):
    async def convert(self, ctx, argument):
        try:
            m = await commands.MemberConverter().convert(ctx, argument)
        except commands.BadArgument:
            try:
                return int(argument, base=10)
            except ValueError:
                raise commands.BadArgument(str(argument) + " is not a valid member or member ID.") from None
        else:
            can_execute = ctx.author.id == ctx.bot.owner_id or \
                          ctx.author == ctx.guild.owner or \
                          ctx.author.top_role > m.top_role

            if not can_execute:
                raise commands.BadArgument('You cannot do this action on this user due to role hierarchy.')
            return m.id

class Mod:
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger("kneedeepatron.{}".format(__name__))

    async def add_restriction(self, member, rst, issuer):
        with open("data/warnings.json", "r") as f:
            rsts = json.load(f)
        if str(member.id) not in rsts:
            rsts[str(member.id)] = {"warns": []}
        rsts[str(member.id)]["name"] = str(member)
        timestamp = time.strftime("%Y-%m-%d %H%M%S", time.localtime())
        rsts[str(member.id)]["warns"].append({"issuer_id": issuer.id, "issuer_name":issuer.name, "reason":rst, "timestamp":timestamp})
        with open("data/warnings.json", "w") as f:
            json.dump(rsts, f)

    async def remove_restriction(self, member, count):
        with open("data/warnings.json", "r") as f:
            rsts = json.load(f)
        if str(member.id) not in rsts:
            return -1
        warn_count = len(rsts[str(member.id)]["warns"])
        if warn_count == 0:
            return -1
        if count > warn_count:
            return -2
        if count < 1:
            return -3
        warn = rsts[str(member.id)]["warns"][count-1]
        embed = discord.Embed(color=discord.Color.dark_red(), title="Deleted Warn: {} on {}".format(count, warn["timestamp"]),
                              description="Issuer: {0[issuer_name]}\nReason: {0[reason]}".format(warn))
        del rsts[str(member.id)]["warns"][count-1]
        with open("data/warnings.json", "w") as f:
            json.dump(rsts, f)
        return embed

    async def on_member_join(self, member):
        embed = discord.Embed(color=discord.Color.green())
        embed.title = "🆕 New member"
        embed.add_field(name="User", value="{}#{} ({})".format(member.name, member.discriminator, member.id))
        embed.add_field(name="Mention", value=member.mention, inline=False)
        embed.add_field(name="Joined at", value=member.joined_at.__format__('%A, %d. %B %Y @ %H:%M:%S'))
        embed.add_field(name="Created at", value=member.created_at.__format__('%A, %d. %B %Y @ %H:%M:%S'))
        await self.bot.botlogs_channel.send(embed=embed)

    async def on_member_remove(self, member):
        embed = discord.Embed(color=discord.Color.red(), timestamp=datetime.utcnow())
        embed.title = "🚪 Member left"
        embed.add_field(name="User", value="{}#{} ({})".format(member.name, member.discriminator, member.id))
        embed.add_field(name="Mention", value=member.mention, inline=False)
        await self.bot.botlogs_channel.send(embed=embed)
    
    @commands.command(name="purge")
    @commands.guild_only()
    @commands.has_any_role("Mods", "The Dunctator", "Evil Queen Beryl", "The Almost Immortals")
    async def purge(self, ctx, limit:int):
        """Clears a given number of messages. Staff only"""
        try:
            await ctx.message.channel.purge(limit=limit)
            await ctx.send("{} messages purged by: {}".format(str(limit), ctx.message.author.mention))
        except:
            await ctx.send("I do not have permissions to do this")

    @commands.command(name="listwarns")
    @commands.guild_only()
    async def listwarns(self, ctx, member:discord.Member):
        """Lists warnings for a user"""
        if member == None:
            member = ctx.message.author
        embed = discord.Embed(color=discord.Color.dark_red())
        embed.set_author(name="Warns for {}#{}".format(member.display_name, member.discriminator), icon_url=member.avatar_url)
        with open("data/warnings.json", "r") as f:
            warns = json.load(f)
        try:
            if len(warns[str(member.id)]["warns"]) == 0:
                embed.description = "There are none!"
                embed.color = discord.Color.green()
            else:
                for idx, warn in enumerate(warns[str(member.id)]["warns"]):
                    embed.add_field(name="{}: {}".format(idx + 1, warn["timestamp"]), value="Issuer: {}\nReason: {}".format(warn["issuer_name"], warn["reason"]))
        except KeyError:  # if the user is not in the file
            embed.description = "There are none!"
            embed.color = discord.Color.green()
        await ctx.send(embed=embed)


    @commands.command(name="warn")
    @commands.guild_only()
    @commands.has_any_role("Mods", "The Dunctator", "Evil Queen Beryl", "The Almost Immortals")
    async def warn(self, ctx, member:discord.Member, *, reason=""):
        """Warn a user. Staff only."""
        issuer = ctx.message.author
        for role in [self.bot.mods_role, self.bot.immortals_role, self.bot.duncan_role, self.bot.beryl_role]:
            if role in member.roles:
                await ctx.send("You cannot warn another staffer!")
                return
        await self.add_restriction(member, reason, issuer)
        with open("data/warnings.json", "r") as f:
            rsts = json.load(f)
            warn_count = len(rsts[str(member.id)]["warns"])
        msg = "You were warned on DKD Subs."
        if reason != "":
            msg += " The given reason is : " + reason 
        msg += "\n\nPlease read the rules of the server. This is warn #{}".format(warn_count)
        if warn_count == 2:
            msg += " __The next warn will automatically kick.__"
        if warn_count == 3:
            msg += "\n\nYou were kicked because of this warning. You can join again right away. Two more warnings will result in an automatic ban."
            try:
                await member.kick(reason="Three Warnings")
            except:
                await ctx.send("No permission to kick the warned member")
        if warn_count == 4:
            msg += "\n\nYou were kicked because of this warning. This is your final warning. You can join again, but **one more warn will result in a ban**."
            try:
                await member.kick(reason="Four Warnings")
            except:
                await ctx.send("No permission to kick the warned member")
        if warn_count == 5:
            msg += "\n\nYou were automatically banned due to five warnings."
            try:
                await member.ban()
            except:
                await ctx.send("No permission to ban the warned member")
        try:
            await member.send(msg)
        except discord.errors.Forbidden:
            pass # dont fail incase user has blocked the bot
        msg = "⚠️ **Warned**: {} warned {} (warn #{}) | {}".format(issuer.mention, member.mention, warn_count, str(member))
        if reason != "":
            msg += " The given reason is : " + reason
        await self.bot.botlogs_channel.send(msg)
    
    @commands.command(name="delwarn")
    @commands.guild_only()
    @commands.has_any_role("Mods", "The Dunctator", "Evil Queen Beryl", "The Almost Immortals")
    async def delwarn(self, ctx, member:discord.Member, idx:int):
        """Remove a specific warning from a user. Staff only."""
        returnvalue = await self.remove_restriction(member,idx)
        with open("data/warnings.json", "r") as f:
            rsts = json.load(f)
            warn_count = len(rsts[str(member.id)]["warns"])
        error = isinstance(returnvalue, int)
        if error:
            if returnvalue == -1:
                await ctx.send("{} has no warns!".format(member.mention))
            elif returnvalue == -2:
                await ctx.send("Warn index is higher than warn count ({})!".format(warn_count))
            elif returnvalue == -3:
                await ctx.send("Warn index below 1!")
            return
        else:
            msg = "🗑 **Deleted warn**: {} removed warn {} from {} | {}".format(ctx.message.author.mention, idx, member.mention, str(member))
            await self.bot.botlogs_channel.send(msg, embed=returnvalue)

    @commands.command(name="clearwarns")
    @commands.guild_only()
    @commands.has_any_role("Mods", "The Dunctator", "Evil Queen Beryl", "The Almost Immortals")
    async def clearwarns(self, ctx, member:discord.Member):
        """Clears warns of a specific member"""
        with open("data/warnings.json", "r") as f:
            warns = json.load(f)
        if str(member.id) not in warns:
            await ctx.send("{} has no warns!".format(member.mention))
            return
        warn_count = len(warns[str(member.id)]["warns"])
        if warn_count == 0:
            await ctx.send("{} has no warns!".format(member.mention))
            return
        warns[str(member.id)]["warns"] = []
        with open("data/warnings.json", "w") as f:
            json.dump(warns, f)
        await ctx.send("{} no longer has any warns!".format(member.mention))
        msg = "🗑 **Cleared warns**: {} cleared {} warns from {} | {}".format(ctx.message.author.mention, warn_count, member.mention, str(member))
        await self.bot.botlogs_channel.send(msg)

    @commands.command(name="lockdown")
    @commands.guild_only()
    @commands.has_any_role("Mods", "The Dunctator", "Evil Queen Beryl", "The Almost Immortals")
    async def lock(self, ctx):
        """Lock message sending in the channel. Staff only."""
        try:
            overwrites_subs = ctx.message.channel.overwrites_for(self.bot.subs_role)
            overwrites_frens = ctx.message.channel.overwrites_for(self.bot.frens_role)
            overwrites_mods = ctx.message.channel.overwrites_for(self.bot.mods_role)
            overwrites_immortals = ctx.message.channel.overwrites_for(self.bot.immortals_role)
            overwrites_trusted = ctx.message.channel.overwrites_for(self.bot.trusted_role)
            if overwrites_subs.send_messages is False or overwrites_frens.send_messages is False:
                await ctx.send("🔒 Channel is already locked down. Use `unlock` command to unlock.")
                return
            overwrites_subs.send_messages = False
            overwrites_frens.send_messages = False
            overwrites_mods.send_messages = True
            overwrites_immortals.send_messages = True
            overwrites_trusted.send_messages = True
            await ctx.message.channel.set_permissions(self.bot.subs_role, overwrite=overwrites_subs)
            await ctx.message.channel.set_permissions(self.bot.frens_role, overwrite=overwrites_frens)
            await ctx.message.channel.set_permissions(self.bot.mods_role, overwrite=overwrites_mods)
            await ctx.message.channel.set_permissions(self.bot.immortals_role, overwrite=overwrites_immortals)
            await ctx.message.channel.set_permissions(self.bot.trusted_role, overwrite=overwrites_trusted)
            await ctx.send("🔒 Channel locked down. Only staff members may speak. Do not bring the topic to other channels or risk disciplinary actions.")
            msg = "🔒 **Lockdown**: {0} by {1} | {2}#{3}".format(ctx.message.channel.mention, ctx.message.author.mention, ctx.message.author.name, ctx.message.author.discriminator)
            await self.bot.botlogs_channel.send(msg)
        except Exception as e:
            print(e)
            traceback.print_exc()
            await ctx.send("💢 I don't have permission to do this.")

    @commands.command(name="unlock")
    @commands.guild_only()
    @commands.has_any_role("Mods", "The Dunctator", "Evil Queen Beryl", "The Almost Immortals")
    async def unlock(self, ctx):
        """Unock message sending in the channel. Staff only."""
        try:
            overwrites_subs = ctx.message.channel.overwrites_for(self.bot.subs_role)
            overwrites_frens = ctx.message.channel.overwrites_for(self.bot.frens_role)
            overwrites_trusted = ctx.message.channel.overwrites_for(self.bot.trusted_role)
            if overwrites_subs.send_messages is True and overwrites_frens.send_messages is True:
                await ctx.send("🔓 Channel is already unlocked.")
                return
            overwrites_subs.send_messages = None
            overwrites_frens.send_messages = None
            overwrites_trusted.send_messages = None
            await ctx.message.channel.set_permissions(self.bot.subs_role, overwrite=overwrites_subs)
            await ctx.message.channel.set_permissions(self.bot.frens_role, overwrite=overwrites_frens)
            await ctx.message.channel.set_permissions(self.bot.trusted_role, overwrite=overwrites_trusted)
            await ctx.send("🔓 Channel unlocked.")
            msg = "🔓 **Unlock**: {0} by {1} | {2}#{3}".format(ctx.message.channel.mention, ctx.message.author.mention, ctx.message.author.name, ctx.message.author.discriminator)
            await self.bot.botlogs_channel.send(msg)
        except Exception as e:
            print(e)
            traceback.print_exc()
            await ctx.send("💢 I don't have permission to do this.")

    @commands.command()
    @checks.check_permissions_or_owner(kick_members=True)
    @commands.bot_has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason: str = None):
        """Kicks a member."""
        author = ctx.message.author
        embed = discord.Embed(color=discord.Color.red(), timestamp=ctx.message.created_at)
        embed.title = "👢 Kicked member"
        embed.add_field(name="User", value=member.mention)
        embed.add_field(name="Action taken by", value=ctx.author.name)
        if member:
            if author.top_role.position < member.top_role.position + 1:
                return await ctx.send("⚠ Operation failed!\nThis cannot be allowed as you are not above the member in role hierarchy.")
            else:
                await member.kick(reason=reason)
                return_msg = "Kicked user: {}".format(member.mention)
                if reason:
                    return_msg += " for reason `{}`".format(reason)
                return_msg += "."
                await ctx.send(return_msg)
                await self.bot.botlogs_channel.send(embed=embed)

    @commands.command()
    @checks.check_permissions_or_owner(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason: str = None):
        """Bans a member."""
        author = ctx.message.author
        embed = discord.Embed(color=discord.Color.red(), timestamp=ctx.message.created_at)
        embed.title = "🔨 Banned member"
        embed.add_field(name="User", value=member.mention)
        embed.add_field(name="Action taken by", value=ctx.author.name)
        if member:
            if author.top_role.position < member.top_role.position + 1:
                return await ctx.send("⚠ Operation failed!\nThis cannot be allowed as you are not above the member in role hierarchy.")
            else:
                await member.ban(reason=reason)
                return_msg = "Banned user: {}".format(member.mention)
                if reason:
                    return_msg += " for reason `{}`".format(reason)
                return_msg += "."
                await ctx.send(return_msg)
                await self.bot.botlogs_channel.send(embed=embed)

    @commands.command()
    @checks.check_permissions_or_owner(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def hackban(self, ctx, identity: MemberID, *, reason: str = None):
        """Bans a member based on ID"""
        author = ctx.message.author
        embed = discord.Embed(color=discord.Color.red(), timestamp=ctx.message.created_at)
        embed.title = "Hackban via ID"
        embed.add_field(name="User ID", value=str(identity))
        embed.add_field(name="Action taken by", value=ctx.author.name)
        await ctx.guild.ban(discord.Object(id=identity), reason=reason)
        return_msg = "Banned user ID: {}".format(str(identity))
        if reason:
            return_msg += " for reason `{}`".format(reason)
        return_msg += "."
        await ctx.send(return_msg)
        await self.bot.botlogs_channel.send(embed=embed)

    @commands.command()
    @commands.has_any_role("Mods", "The Dunctator", "Evil Queen Beryl", "The Almost Immortals")
    async def mute(self, ctx, user:discord.Member, *, reason="Reason Unspecified"):
        """Mute a specific user, staff and trusted users only"""
        for role in [self.bot.mods_role, self.bot.immortals_role, self.bot.duncan_role, self.bot.beryl_role]:
            if role in user.roles:
                await ctx.send("You cannot mute a staffer!")
                return
        await user.add_roles(self.bot.muted_role)
        msg = "**Muted**: {} has muted {}! The command was used for the following reason: {}".format(ctx.message.author.mention, user.mention, reason)
        await ctx.send(msg)
        await self.bot.botlogsmod_channel.send(msg)

    @commands.command()
    @commands.has_any_role("Mods", "The Dunctator", "Evil Queen Beryl", "The Almost Immortals")
    async def unmute(self, ctx, user:discord.Member, *, reason="Reason Unspecified"):
        """Mute a specific user, staff and trusted users only"""
        await user.remove_roles(self.bot.muted_role)
        msg = "**Unmuted**: {} has unmuted {}! The command was used for the following reason: {}".format(ctx.message.author.mention, user.mention, reason)
        await ctx.send(msg)
        await self.bot.botlogsmod_channel.send(msg)

    @commands.command()
    @checks.check_permissions_or_owner(kick_members=True)
    @commands.bot_has_permissions(manage_roles=True)
    async def approve(self, ctx, user: discord.Member):
        """Approve a user, giving them the trusted role."""
        await user.add_roles(self.bot.trusted_role)
        msg = "✅ **Approved**: {} approved {}".format(ctx.message.author.mention, user.mention)
        await ctx.send(msg)
        await self.bot.botlogsmod_channel.send(msg)

    @commands.command()
    @checks.check_permissions_or_owner(kick_members=True)
    @commands.bot_has_permissions(manage_roles=True)
    async def revoke(self, ctx, user:discord.Member):
        """Removes trusted role"""
        await user.remove_roles(self.bot.trusted_role)
        msg = "✅ **Revoked**: {} removed trusted from {}".format(ctx.message.author.mention, user.mention)
        await ctx.send(msg)
        await self.bot.botlogsmod_channel.send(msg)

    @commands.command(aliases=['sr'])
    @commands.has_any_role("Mods", "Trusted")
    async def staffrequest(self, ctx, *, reason="Reason Unspecified"):
        """Summons staff, trusted only"""
        await self.bot.botlogsmod_channel.send("@everyone {} has requested staff assistance for the reason: {}".format(ctx.message.author, reason))
        await ctx.send("Staff request sent! This channel will locked down till staff takes action")
        try:
            overwrites_subs = ctx.message.channel.overwrites_for(self.bot.subs_role)
            overwrites_frens = ctx.message.channel.overwrites_for(self.bot.frens_role)
            overwrites_mods = ctx.message.channel.overwrites_for(self.bot.mods_role)
            overwrites_immortals = ctx.message.channel.overwrites_for(self.bot.immortals_role)
            overwrites_trusted = ctx.message.channel.overwrites_for(self.bot.trusted_role)
            if overwrites_subs.send_messages is False or overwrites_frens.send_messages is False:
                await ctx.send("🔒 Channel is already locked down. Use `unlock` command to unlock.")
                return
            overwrites_subs.send_messages = False
            overwrites_frens.send_messages = False
            overwrites_mods.send_messages = True
            overwrites_immortals.send_messages = True
            overwrites_trusted.send_messages = True
            await ctx.message.channel.set_permissions(self.bot.subs_role, overwrite=overwrites_subs)
            await ctx.message.channel.set_permissions(self.bot.frens_role, overwrite=overwrites_frens)
            await ctx.message.channel.set_permissions(self.bot.mods_role, overwrite=overwrites_mods)
            await ctx.message.channel.set_permissions(self.bot.immortals_role, overwrite=overwrites_immortals)
            await ctx.message.channel.set_permissions(self.bot.trusted_role, overwrite=overwrites_trusted)
            await ctx.send("🔒 Channel locked down. Only staff members may speak. Do not bring the topic to other channels or risk disciplinary actions.")
            msg = "🔒 **Lockdown**: {0} by {1} | {2}#{3}".format(ctx.message.channel.mention, ctx.message.author.mention, ctx.message.author.name, ctx.message.author.discriminator)
            await self.bot.botlogs_channel.send(msg)
        except Exception as e:
            print(e)
            traceback.print_exc()
            await ctx.send("💢 I don't have permission to do this.")

def setup(bot):
    bot.add_cog(Mod(bot))
