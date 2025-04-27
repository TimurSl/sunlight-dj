import discord
from discord.ext import commands
from discord import app_commands

class Search(commands.Cog):
    def __init__(self, bot: commands.Bot, controller):
        self.bot = bot
        self.controller = controller

    @app_commands.command(name="search", description="Search and play a song from YouTube")
    @app_commands.describe(query="Name of the song or keywords to search")
    async def search(self, interaction: discord.Interaction, query: str):
        await interaction.response.defer()

        await self.controller.search(interaction, query)
