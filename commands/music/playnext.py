import discord
from discord.ext import commands
from discord import app_commands

class PlayNext(commands.Cog):
    def __init__(self, bot: commands.Bot, controller):
        self.bot = bot
        self.controller = controller

    @app_commands.command(name="playnext", description="Play a track next in the queue")
    async def playnext(self, interaction: discord.Interaction, track_number: int):
        if not interaction.response.is_done():
            await interaction.response.defer()

        await self.controller.playnext(interaction, track_number)
