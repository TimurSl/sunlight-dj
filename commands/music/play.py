import discord
from discord.ext import commands
from discord import app_commands

class PlayCog(commands.Cog):
    def __init__(self, bot: commands.Bot, controller):
        self.bot = bot
        self.controller = controller

    @app_commands.command(name="play", description="Plays a YouTube URL or playlist")
    @app_commands.describe(url="The YouTube link to play")
    async def play(self, interaction: discord.Interaction, url: str):
        if not interaction.response.is_done():
            await interaction.response.defer()
        await self.controller.play(interaction, url)
