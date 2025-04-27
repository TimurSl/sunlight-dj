import discord
from discord.ext import commands
from discord import app_commands

class Fav(commands.Cog):
    def __init__(self, bot: commands.Bot, controller):
        self.bot = bot
        self.controller = controller

    @app_commands.command(name="fav", description="Add current song to your favorites")
    async def fav(self, interaction: discord.Interaction):
        if not interaction.response.is_done():
            await interaction.response.defer(ephemeral=True)
        await self.controller.fav(interaction)

    @app_commands.command(name="favall", description="Add queue to your favorites")
    async def favall(self, interaction: discord.Interaction):
        if not interaction.response.is_done():
            await interaction.response.defer(ephemeral=True)
        await self.controller.favall(interaction)

    @app_commands.command(name="unfav", description="Remove current song from your favorites")
    async def unfav(self, interaction: discord.Interaction):
        if not interaction.response.is_done():
            await interaction.response.defer(ephemeral=True)
        await self.controller.unfav(interaction)
