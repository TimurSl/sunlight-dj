import discord
from discord import app_commands
from discord.ext import commands
from typing import Iterable
from common.config import get_moderator_roles, get_music_roles


def _has_any_role_id(user_roles: Iterable[discord.Role], allowed_ids: Iterable[int]) -> bool:
    role_ids = {r.id for r in user_roles}
    for rid in allowed_ids:
        if rid in role_ids:
            return True
    return False


def is_moderator():
    async def predicate(ctx):
        if ctx.guild is None:
            return False
        if ctx.author.guild_permissions.administrator:
            return True
        allowed = get_moderator_roles(ctx.guild.id)
        return _has_any_role_id(ctx.author.roles, allowed)
    return commands.check(predicate)


essentially_music_role_ids = None


def is_music_user():
    async def predicate(ctx):
        if ctx.guild is None:
            return False
        if ctx.author.guild_permissions.administrator:
            return True
        allowed = get_music_roles(ctx.guild.id)
        return _has_any_role_id(ctx.author.roles, allowed)
    return commands.check(predicate)


def is_app_moderator():
    async def predicate(interaction: discord.Interaction):
        if interaction.guild is None:
            return False
        if interaction.user.guild_permissions.administrator:
            return True
        allowed = get_moderator_roles(interaction.guild.id)
        return _has_any_role_id(interaction.user.roles, allowed)
    return app_commands.check(predicate)


def is_app_music_user():
    async def predicate(interaction: discord.Interaction):
        if interaction.guild is None:
            return False
        if interaction.user.guild_permissions.administrator:
            return True
        allowed = get_music_roles(interaction.guild.id)
        return _has_any_role_id(interaction.user.roles, allowed)
    return app_commands.check(predicate)