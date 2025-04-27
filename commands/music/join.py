import discord
from discord.ext import commands
from discord import app_commands

class JoinCog(commands.Cog):
    def __init__(self, bot: commands.Bot, controller):
        self.bot = bot
        self.controller = controller

    @app_commands.command(name="join", description="Bot joins your voice channel")
    async def join(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await self.controller.join(interaction)