import discord
from discord.ext import commands
from discord import app_commands

class CancelProcess(commands.Cog):
    def __init__(self, bot: commands.Bot, controller):
        self.bot = bot
        self.controller = controller

    @app_commands.command(name="cancel", description="Cancel the current processing tracks (useful when you dont wanna load playlist)")
    async def cancelprocess(self, interaction: discord.Interaction):
        if not interaction.response.is_done():
            await interaction.response.defer()
        await self.controller.cancelprocess(interaction)
