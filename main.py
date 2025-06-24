import discord
from discord.ext import commands, tasks
from typing import Optional
from discord import app_commands
from discord.ui import Select, View
from itertools import cycle
import logging
from dotenv import load_dotenv
import asyncio
import os 

load_dotenv()
token = os.getenv('DISCORD_TOKEN')

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

bot_status = cycle (["/citlali", "watching aliens :p", "partying with the crew"])

@tasks.loop(seconds=2)
async def change_status():
    await bot.change_presence(status=discord.Status.online, activity=discord.Game(next(bot_status)))
@bot.event
async def on_ready():   
    change_status.start()
    print("Bot is now online.")
    try:
        synced_commands = await bot.tree.sync()
        print("Commands synced.")
    except Exception as e:
        print("An error with syncing application commands has occured: ", e)

@bot.tree.command(name="embed", description="create embed")
@app_commands.describe(
    author='author text',
    aicon='author icon',
    title='embed title',
    description='embed description',
    color='embed color',
    image='embed image url',
    thumbnail='embed thumbnail',
    footer='footer text',
    ficon='footer icon'
    )
async def embed(interaction: discord.Interaction, 
                author: Optional[str], aicon: Optional[discord.Attachment],
                title: Optional[str], description: str, color: str, image: Optional[discord.Attachment], 
                thumbnail: Optional[discord.Attachment], footer: Optional[str], ficon: Optional[discord.Attachment]
                ):
    embed = discord.Embed(
        title=title,
        description=description,
        color=discord.Color.from_str(color)
    )
    if author and aicon:
        embed.set_author(name=author, icon_url=aicon.url)
    if image:
        embed.set_image(url=image.url)
    if thumbnail:
        embed.set_thumbnail(url=thumbnail.url)
    if footer and ficon:
        embed.set_footer(text=footer, icon_url=ficon.url)
    await interaction.response.send_message("embed created successfully!", ephemeral=True)
    await interaction.channel.send(embed=embed)

@bot.tree.command(name="queue", description="add to queue")
async def queue(interaction: discord.Interaction, user: discord.Member, order: str, payment: str):
    channel = bot.get_channel(1386564664258727946)
    await interaction.response.send_message("ticket queued!")
    embed = discord.Embed(
        color=discord.Color.from_str("#bd9fe2"),
        description=(
            f"‎ ‎ ‎ ‎ ‎ ‎ ‎ ‎ ‎₊ ‎ ‎ ‎ ‎ ‎ ‎ ‎ ‎ ‎ ‎　꒰୨୧ ‎ ‎ ‎ ‎ ‎ ‎ ‎ ‎ ‎ ‎**{user.mention}’s offer *!*** ‎ ‎ ‎ ‎ ‎𓈒 ‎ ‎ ‎ ‎ ‎ ‎  ‎\n"
            f"‎ ‎ ‎ ‎ ‎ ‎ ‎ ‎ ‎ ୨୧ ‎ ‎ ‎ ‎ ‎ ‎ ‎ ‎‎ ‎ ‎ ‎__order__ : {order}‎ ‎ ‎ ‎ ‎\n"
            f"‎ ‎ ‎ ‎ ‎ ‎ ‎ ‎ ‎ ୨୧ ‎ ‎ ‎ ‎ ‎ ‎ ‎ ‎‎ ‎ ‎ ‎__payment__ : {payment}‎\n"
            f"‎ ‎ ‎ ‎ ‎ ‎ ‎ ‎ ‎ ୨୧ ‎ ‎ ‎ ‎ ‎ ‎ ‎ ‎‎ ‎ ‎ ‎__status__ : ‎ ‎ ‎ ‎"
        ),
    )

    await channel.send(embed=embed, view=MyView())

class MyView(discord.ui.View):
    @discord.ui.select(
        placeholder="status...",
        min_values=1,
        max_values=1,
        options = [
            discord.SelectOption(emoji="<a:1purplebow3:1386889594414301327>", 
                                 label="processing.."),
            discord.SelectOption(emoji="<a:06_purplepurse:1386889590199156747>", 
                                 label="slowly processing.."),
            discord.SelectOption(emoji="<:06_white_bows:1386889592409423893>", 
                                 label="finished!")
        ])
    async def select_callback(self, interaction: discord.Interaction, select: discord.ui.Select):
        try:
            print(f"DEBUG: select={select}, interaction={interaction}")
            print(f"DEBUG: select.values={getattr(select, 'values', None)}")
            print(f"DEBUG: interaction.message.embeds={interaction.message.embeds}")
            selected_value = select.values[0]
            embed = interaction.message.embeds[0] if interaction.message.embeds else None
            print(f"DEBUG: embed={embed}")
            if not embed or not embed.description:
                raise ValueError("Embed or description missing.")
            # Parse order, payment, and status from the description
            desc = embed.description
            print(f"DEBUG: embed.description={desc}")
            import re
            order_match = re.search(r'__order__ ?: ?(.+)', desc)
            payment_match = re.search(r'__payment__ ?: ?(.+)', desc)
            # status will be replaced, so we don't need to extract it
            order = order_match.group(1).strip() if order_match else ''
            payment = payment_match.group(1).strip() if payment_match else ''
            user = interaction.message.mentions[0] if interaction.message.mentions else None
            # Build new description with updated status
            new_desc = re.sub(r'(__status__ ?: ?).+', f"\\1{selected_value}", desc)
            embed.description = new_desc
            await interaction.response.edit_message(
                embed=embed,
                view=None if selected_value == "finished!" else MyView()
            )
        except Exception as e:
            print(f"Error editing message: {e}")
            await interaction.response.send_message(f"Failed to edit message: {e}", ephemeral=True)

@bot.tree.command(name="denied", description="order denied")
async def denied(interaction: discord.Interaction, order: str, payment: str, reason: str):
    await interaction.response.send_message("Order has been denied.", ephemeral=True)
    await interaction.channel.send(f"‎ ‎ ‎ ‎ ‎ ‎ ‎ ‎ ‎₊ ‎ ‎ ‎ ‎ ‎ ‎ ‎ ‎ ‎ ‎　꒰୨୧꒱ ‎ ‎ ‎ ‎ ‎ ‎ ‎ ‎ ‎ ‎**order __denied__**\n"
                                   f"‎ ‎ ‎ ‎ ‎ ‎ ‎ ‎ ‎ ୨୧ ‎ ‎ ‎ ‎ ‎ ‎ ‎ ‎‎ ‎ ‎ ‎__order__ : {order}‎ ‎ ‎ ‎ ‎\n"
                                   f"‎ ‎ ‎ ‎ ‎ ‎ ‎ ‎ ‎ ୨୧ ‎ ‎ ‎ ‎ ‎ ‎ ‎ ‎‎ ‎ ‎ ‎__payment__ : {payment}‎ ‎ ‎ ‎ ‎\n"
                                   f"‎ ‎ ‎ ‎ ‎ ‎ ‎ ‎ ‎ ୨୧ ‎ ‎ ‎ ‎ ‎ ‎ ‎ ‎‎ ‎ ‎ ‎__reason__ : {reason}‎ ‎ ‎ ‎ ‎"
    )

bot.run(token, log_handler=handler, log_level=logging.DEBUG)
