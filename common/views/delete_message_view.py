import discord
from common.checks.permission_checks import is_moderator

class DeleteMessageView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=30)

    @discord.ui.button(label="❌ Delete Message", style=discord.ButtonStyle.danger)
    @is_moderator()
    async def delete_message(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.message.delete()