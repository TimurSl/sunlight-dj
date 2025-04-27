import discord
from discord.ext import commands
from discord import app_commands
from discord.ext.commands import has_permissions

from common.checks.permission_checks import is_moderator, is_music_user


class ForceJoinCog(commands.Cog):
    def __init__(self, bot: commands.Bot, controller):
        self.bot = bot
        self.controller = controller

    @commands.hybrid_command(name="forcejoin", description="Bot joins your voice channel (forcefully)")
    @commands.check_any(is_moderator(), is_music_user())
    async def forcejoin(self, interaction: discord.Interaction):
        if not interaction.response.is_done():
            await interaction.response.defer(ephemeral=True)

        await self.controller.join(interaction, force=True)

    @forcejoin.error
    async def forcejoin_error(self, interaction: discord.Interaction, error):
        if isinstance(error, commands.CommandInvokeError):
            await interaction.followup.send(
                "An error occurred while trying to force join the voice channel. Please try again later.",
                ephemeral=True
            )
        else:
            raise error
