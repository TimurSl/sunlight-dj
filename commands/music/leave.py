import discord
from discord.ext import commands
from discord import app_commands

class LeaveCog(commands.Cog):
    def __init__(self, bot: commands.Bot, controller):
        self.bot = bot
        self.controller = controller

    @app_commands.command(name="leave", description="Bot leaves the voice channel")
    async def leave(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await self.controller.leave(interaction)
