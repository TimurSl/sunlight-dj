import discord
from discord.ext import commands
from discord import app_commands

class QueueCog(commands.Cog):
    def __init__(self, bot: commands.Bot, controller):
        self.bot = bot
        self.controller = controller

    @app_commands.command(name="queue", description="Shows the full queue of songs")
    async def queue(self, interaction: discord.Interaction):
        print("Queue command triggered")
        await interaction.response.defer()
        await self.controller.show_queue(interaction)
