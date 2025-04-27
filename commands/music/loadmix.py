import json
import os

import discord
from anyio import sleep_forever

from music.controller import TrackInfo
from useful import get_pwd

MIXES_DIR = os.path.join(get_pwd(), "data", "music", "mixes")

import discord
from discord.ext import commands
from discord import app_commands

class LoadMix(commands.Cog):
    def __init__(self, bot: commands.Bot, controller):
        self.bot = bot
        self.controller = controller

    @app_commands.command(name="loadmix", description="Load a mix for this server")
    async def loadmixcommand(self, interaction: discord.Interaction):
        if not interaction.response.is_done():
            await interaction.response.defer()

        await self.controller.loadmix(interaction)
