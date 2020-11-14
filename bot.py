#!/usr/bin/env python
# -*- coding: UTF-8 -*-
from configparser import ConfigParser

import discord
from discord.ext import commands
import logging

logger = logging.getLogger('fenrir_bot')
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler('fenrir.log')
fh.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
logger.addHandler(fh)

config = ConfigParser()
config.read("configs/bot.ini")
API = config['API']
config_prefixes = config['Defaults']['prefix']

def get_prefix(bot, message):
    """A callable Prefix for our bot. This could be edited to allow per server prefixes."""
    prefixes = [config_prefixes]
    if not message.guild:
        return '?'
    return commands.when_mentioned_or(*prefixes)(bot, message)

initial_extensions = ['cogs.sfv_challonge.sfv_tournament']
bot = commands.Bot(command_prefix=get_prefix, description='Test bot')

if __name__ == '__main__':
    for extension in initial_extensions:
        bot.load_extension(extension)

@bot.event
async def on_ready():
    """http://discordpy.readthedocs.io/en/rewrite/api.html#discord.on_ready"""
    print(f'\n\nLogged in as: {bot.user.name} - {bot.user.id}\nVersion: {discord.__version__}\n')

    game = discord.Game("in the salt mines")
    await bot.change_presence(status=discord.Status.online, activity=game)
    await bot.user.edit(username="Fenrir")
    print(f'Successfully logged in and booted...!')

bot.run(API['key'], bot=True, reconnect=True)
