import discord
from discord.ext import commands
from discord import app_commands

class LoopQueueCog(commands.Cog):
    def __init__(self, bot: commands.Bot, controller):
        self.bot = bot
        self.controller = controller

    @app_commands.command(name="loopqueue", description="Toggle looping the entire queue")
    async def loopqueue(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await self.controller.toggle_loop_queue(interaction)