import discord
from discord.ext import commands
from discord import app_commands

class PreviousCog(commands.Cog):
    def __init__(self, bot: commands.Bot, controller):
        self.bot = bot
        self.controller = controller

    @app_commands.command(name="previous", description="Returns to the previous track")
    async def previous(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await self.controller.previous(interaction)