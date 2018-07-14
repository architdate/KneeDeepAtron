import discord


class MessageLogger:
    def __init__(self, bot):
        self.bot = bot

    async def on_message_delete(self, message):
        embed = discord.Embed(description=message.content)
        if message.embeds:
            data = message.embeds[0]
            if data.type == 'image':
                embed.set_image(url=data.url)

        if message.attachments:
            file = message.attachments[0]
            if file.url.lower().endswith(('png', 'jpeg', 'jpg', 'gif', 'webp')):
                embed.set_image(url=file.url)
            else:
                embed.add_field(name='Attachment', value='[{0}]({1})'.format(file.filename, file.url), inline=False)
        embed.set_author(name=message.author.display_name, icon_url=message.author.avatar_url_as(format='png'))
        embed.timestamp = message.created_at
        await self.bot.botlogsmod_channel.send("Deleted Message by: {}".format(message.author.name),embed=embed)

     
def setup(bot):
    bot.add_cog(MessageLogger(bot))
