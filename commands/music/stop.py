import discord
from discord.ext import commands
from discord import app_commands

class StopCog(commands.Cog):
    def __init__(self, bot: commands.Bot, controller):
        self.bot = bot
        self.controller = controller

    @app_commands.command(name="clear", description="Stops playback and clears the queue")
    async def stop(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await self.controller.stop(interaction)