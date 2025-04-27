import discord
from discord.ext import commands
from discord import app_commands

class NowPlaying(commands.Cog):
    def __init__(self, bot: commands.Bot, controller):
        self.bot = bot
        self.controller = controller

    @app_commands.command(name="nowplaying", description="Show currently playing track")
    async def nowplaying(self, interaction: discord.Interaction):
        if not interaction.response.is_done():
            await interaction.response.defer(ephemeral=True)
        await self.controller.nowplaying(interaction)
