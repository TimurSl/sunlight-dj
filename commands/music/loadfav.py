import discord
from discord.ext import commands
from discord import app_commands
from music.controller import TrackInfo, FavDropdown


class LoadFav(commands.Cog):
    def __init__(self, bot, controller):
        self.bot = bot
        self.controller = controller

    @app_commands.command(name="loadfav", description="Load your favorite songs")
    async def loadfav(self, interaction: discord.Interaction):
        if not interaction.response.is_done():
            await interaction.response.defer(ephemeral=True)

        favorites = self.controller.load_favorites()
        user_id = str(interaction.user.id)
        user_favs = favorites.get(user_id)

        if not user_favs:
            await interaction.followup.send("❌ You have no favorite songs.", ephemeral=True)
            return

        view = discord.ui.View()
        view.add_item(FavDropdown(user_favs, self.controller))

        await interaction.followup.send("🎵 Choose your favorite:", view=view, ephemeral=True)
