import discord
from discord.ext import commands
from discord import app_commands

class RandomCog(commands.Cog):
    def __init__(self, bot: commands.Bot, controller):
        self.bot = bot
        self.controller = controller

    @app_commands.command(name="random", description="Shuffle the queue and restart playback")
    async def random(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await self.controller.shuffle(interaction)