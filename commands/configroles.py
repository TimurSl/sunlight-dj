import discord
from discord.ext import commands
from common.config import set_moderator_roles, set_music_roles, get_moderator_roles, get_music_roles

class ConfigRoles(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name='set_moderator_roles')
    @commands.has_guild_permissions(administrator=True)
    async def set_moderator_roles_cmd(self, ctx: commands.Context, *roles: discord.Role):
        if ctx.guild is None:
            return
        role_ids = [r.id for r in roles]
        set_moderator_roles(ctx.guild.id, role_ids)
        names = ', '.join([r.name for r in roles]) if roles else '(none)'
        await ctx.reply(f"Moderator roles updated: {names}")

    @commands.command(name='set_music_roles')
    @commands.has_guild_permissions(administrator=True)
    async def set_music_roles_cmd(self, ctx: commands.Context, *roles: discord.Role):
        if ctx.guild is None:
            return
        role_ids = [r.id for r in roles]
        set_music_roles(ctx.guild.id, role_ids)
        names = ', '.join([r.name for r in roles]) if roles else '(none)'
        await ctx.reply(f"Music roles updated: {names}")

    @commands.command(name='show_roles_config')
    @commands.has_guild_permissions(manage_guild=True)
    async def show_roles_config_cmd(self, ctx: commands.Context):
        if ctx.guild is None:
            return
        mods = get_moderator_roles(ctx.guild.id)
        mus = get_music_roles(ctx.guild.id)
        def fmt(ids):
            if not ids:
                return '(none)'
            names = []
            for rid in ids:
                role = ctx.guild.get_role(int(rid))
                names.append(role.name if role else f"<deleted:{rid}>")
            return ', '.join(names)
        await ctx.reply(f"Configured roles:\n- Moderators: {fmt(mods)}\n- Music users: {fmt(mus)}")

async def setup(bot: commands.Bot):
    await bot.add_cog(ConfigRoles(bot))
