import discord
from discord.ext import commands
from discord import app_commands

class PauseCog(commands.Cog):
    def __init__(self, bot: commands.Bot, controller):
        self.bot = bot
        self.controller = controller

    @app_commands.command(name="pause", description="Pauses or resumes playback")
    async def pause(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await self.controller.pause(interaction)