import discord
from discord.ext import commands
from discord import app_commands

class SkipTo(commands.Cog):
    def __init__(self, bot: commands.Bot, controller):
        self.bot = bot
        self.controller = controller

    @app_commands.command(name="skipto", description="Skips to a specific track in the queue")
    async def nowplaying(self, interaction: discord.Interaction, track_number: int = None):
        if not interaction.response.is_done():
            await interaction.response.defer()
        await self.controller.skipto(interaction, track_number)
