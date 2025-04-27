import discord
from discord.ext import commands
from discord import app_commands

class NextCog(commands.Cog):
    def __init__(self, bot: commands.Bot, controller):
        self.bot = bot
        self.controller = controller

    @app_commands.command(name="next", description="Skips to the next track")
    async def next(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await self.controller.next(interaction)