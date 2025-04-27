import json
import os

import discord

from common.checks.permission_checks import is_music_user
from useful import get_pwd

MIXES_DIR = os.path.join(get_pwd(), "data", "music", "mixes")

import discord
from discord.ext import commands
from discord import app_commands

class SaveMix(commands.Cog):
    def __init__(self, bot: commands.Bot, controller):
        self.bot = bot
        self.controller = controller

    @commands.hybrid_command(name="savemix", description="Save the current queue as a mix for this server")
    @is_music_user()
    async def savemix(self, interaction: discord.Interaction):
        if not interaction.response.is_done():
            await interaction.response.defer()

        guild_music = self.controller.get_guild_music(interaction.guild.id)
        if not guild_music.queue:
            await interaction.followup.send("❌ No songs to save.")
            return

        os.makedirs(MIXES_DIR, exist_ok=True)
        mix_path = os.path.join(MIXES_DIR, f"{interaction.guild.id}.json")

        mix_data = []
        for track in guild_music.queue:
            mix_data.append({
                "url": track.url,
                "title": track.title,
                "stream_url": track.stream_url
            })

        with open(mix_path, "w", encoding="utf-8") as f:
            json.dump(mix_data, f, ensure_ascii=False, indent=2)

        await interaction.followup.send(f"✅ Saved {len(mix_data)} tracks to server mix.")
