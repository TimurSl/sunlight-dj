import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
import os
load_dotenv()

MODERATOR_ROLE_ID = int(os.getenv("MODERATOR_ROLE_ID"))

def is_moderator():
    async def predicate(ctx):
        if ctx.author.guild_permissions.administrator:
            return True
        return MODERATOR_ROLE_ID in [r.id for r in ctx.author.roles]
    return commands.check(predicate)

MUSIC_USER_ROLE_ID = int(os.getenv("DISCORD_MUSIC_ROLE_ID"))

def is_music_user():
    async def predicate(ctx):
        if ctx.author.guild_permissions.administrator:
            return True
        return MUSIC_USER_ROLE_ID in [r.id for r in ctx.author.roles]
    return commands.check(predicate)

def is_app_moderator():
    async def predicate(interaction: discord.Interaction):
        if interaction.user.guild_permissions.administrator:
            return True
        return MODERATOR_ROLE_ID in [r.id for r in interaction.user.roles]
    return app_commands.check(predicate)

def is_app_music_user():
    async def predicate(interaction: discord.Interaction):
        if interaction.user.guild_permissions.administrator:
            return True
        return MUSIC_USER_ROLE_ID in [r.id for r in interaction.user.roles]
    return app_commands.check(predicate)