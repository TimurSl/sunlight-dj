import os
from dotenv import load_dotenv
import discord
from discord.ext import commands


from commands.music.join import JoinCog
from commands.music.leave import LeaveCog
from commands.music.play import PlayCog
from commands.music.loop import Loop247Cog
from commands.music.next import NextCog
from commands.music.stop import StopCog
from commands.music.previous import PreviousCog
from commands.music.pause import PauseCog
from commands.music.queue import QueueCog
from commands.music.random import RandomCog
from commands.music.loopqueue import LoopQueueCog
from commands.music.search import Search
from commands.music.fav import Fav
from commands.music.nowplaying import NowPlaying
from commands.music.skipto import SkipTo
from commands.music.loadfav import LoadFav
from commands.music.loadmix import LoadMix
from commands.music.savemix import SaveMix
from commands.music.removetrack import RemoveTrack
from commands.music.forcejoin import ForceJoinCog
from commands.music.forceleave import ForceLeaveCog

from music.controller import MusicController


load_dotenv()
TOKEN = str(os.getenv("BOT_TOKEN"))

intents = discord.Intents.default()
intents.members = True
intents.message_content = True




class CustomBot(commands.Bot):
    async def setup_hook(self):
        controller = MusicController(bot)

        await bot.add_cog(JoinCog(bot, controller))
        await bot.add_cog(PlayCog(bot, controller))
        await bot.add_cog(StopCog(bot, controller))
        await bot.add_cog(PauseCog(bot, controller))
        await bot.add_cog(NextCog(bot, controller))
        await bot.add_cog(PreviousCog(bot, controller))
        await bot.add_cog(Loop247Cog(bot, controller))
        await bot.add_cog(LeaveCog(bot, controller))
        await bot.add_cog(QueueCog(bot, controller))
        await bot.add_cog(RandomCog(bot, controller))
        await bot.add_cog(LoopQueueCog(bot, controller))
        await bot.add_cog(Search(bot, controller))
        await bot.add_cog(Fav(bot, controller))
        await bot.add_cog(NowPlaying(bot, controller))
        await bot.add_cog(SkipTo(bot, controller))
        await bot.add_cog(LoadFav(bot, controller))
        await bot.add_cog(LoadMix(bot, controller))
        await bot.add_cog(SaveMix(bot, controller))
        await bot.add_cog(RemoveTrack(bot, controller))
        await bot.add_cog(ForceJoinCog(bot, controller))
        await bot.add_cog(ForceLeaveCog(bot, controller))


        print("Reloaded all modules & synced commands.")

bot = CustomBot(command_prefix="/", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Error syncing commands: {e}")

bot.run(TOKEN)
