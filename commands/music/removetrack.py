import discord
from discord.ext import commands
from discord import app_commands

class RemoveTrack(commands.Cog):
    def __init__(self, bot: commands.Bot, controller):
        self.bot = bot
        self.controller = controller

    @app_commands.command(name="removetrack", description="Remove a track from the queue")
    async def search(self, interaction: discord.Interaction, track_number: int):
        if not interaction.response.is_done():
            await interaction.response.defer()

        await self.controller.removetrack(interaction, track_number)
