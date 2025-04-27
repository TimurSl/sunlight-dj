import discord
from discord.ext import commands
from discord import app_commands

class Loop247Cog(commands.Cog):
    def __init__(self, bot: commands.Bot, controller):
        self.bot = bot
        self.controller = controller

    @app_commands.command(name="247", description="Toggles 24/7 mode (continuous play & loop)")
    async def toggle_247(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await self.controller.toggle_247(interaction)