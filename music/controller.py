import asyncio
import json
import os
import random
from dataclasses import dataclass
from typing import List

import discord
from discord import ui
from discord.app_commands import guilds
from discord.ext import commands
import yt_dlp
from useful import get_pwd

FAV_FILE = os.path.join(get_pwd(), "data", "music", "favorites.json")
MIXES_DIR = os.path.join(get_pwd(), "data", "music", "mixes")

@dataclass
class TrackInfo:
    url: str
    title: str
    stream_url: str



class GuildMusic:
    def __init__(self):
        self.queue: List[TrackInfo] = []
        self.current_index = 0
        self.loop247 = False
        self.random_mode = False
        self.loop_queue = False
        self.vc = None
        self.skip_flag = False
        self.user_who_added_id = None # ID of the user who invited bot to voice


class MusicController:
    YTDL_OPTIONS = {
        'format': 'bestaudio/best',
        'noplaylist': False,
        'quiet': True,
        'extract_flat': 'in_playlist'
    }
    FFMPEG_OPTIONS = {
        'options': '-vn'
    }

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.ytdl = yt_dlp.YoutubeDL(self.YTDL_OPTIONS)
        self.guilds = {}
        self.skip_flag = False

    def get_guild_music(self, guild_id: int) -> GuildMusic:
        if guild_id not in self.guilds:
            self.guilds[guild_id] = GuildMusic()
        return self.guilds[guild_id]

    async def join(self, interaction: discord.Interaction, force: bool = False):
        if not interaction.user.voice or not interaction.user.voice.channel:
            await interaction.followup.send("You're not in a voice channel.")
            return
        await self.connect_if_not_connected(interaction, force=force)

    async def leave(self, interaction: discord.Interaction, force: bool = False):
        guild = interaction.guild or interaction.user.guild

        guild_music = self.get_guild_music(guild.id)
        if guild_music.user_who_added_id is not None and guild_music.user_who_added_id != interaction.user.id and not force:
            await interaction.followup.send("You can't leave the voice channel because you didn't add the bot.")
            return
        if guild_music.vc and guild_music.vc.is_connected():
            await guild_music.vc.disconnect()
            guild_music.vc = None
            guild_music.queue.clear()
            guild_music.current_index = 0
            await interaction.followup.send("Left the voice channel.")

    async def play(self, interaction: discord.Interaction, url: str):
        guild = interaction.guild or interaction.user.guild

        guild_music = self.get_guild_music(guild.id)
        queue = guild_music.queue

        await self.connect_if_not_connected(interaction)
        if not interaction.response.is_done():
            await interaction.response.defer()

        # Extract info
        loop = asyncio.get_event_loop()
        info = await loop.run_in_executor(None, lambda: self.ytdl.extract_info(url, download=False, process=True))
        print(info)

        queue = []

        if 'entries' in info:
            for entry in info['entries'][:5]:
                if entry.get('_type') == 'url':
                    full_entry = await loop.run_in_executor(None,
                                                            lambda: self.ytdl.extract_info(entry['url'], download=False, process=True))
                else:
                    full_entry = entry

                stream_url = self.get_any_audio_format(full_entry.get('formats', []))
                if stream_url:
                    queue.append(TrackInfo(
                        url=full_entry.get('webpage_url', full_entry.get('url')),
                        title=full_entry.get('title', full_entry.get('url')),
                        stream_url=stream_url
                    ))

            # Остальные треки кидаем в фон
            rest_entries = info['entries'][5:]
            if rest_entries:
                asyncio.create_task(self._process_background_tracks(rest_entries, interaction.guild.id))
        else:
            if guild_music.vc.is_playing():
                # in background
                soundtrack = asyncio.create_task(self._process_background_tracks([info], interaction.guild.id, interaction))
            else:
                # Один трек без плейлиста
                if info.get('_type') == 'url':
                    full_entry = await loop.run_in_executor(None,
                                                            lambda: self.ytdl.extract_info(info['url'], download=False,process=True))
                else:
                    full_entry = info

                stream_url = self.get_any_audio_format(full_entry.get('formats', []))
                if stream_url:
                    queue.append(TrackInfo(
                        url=full_entry.get('webpage_url', full_entry.get('url')),
                        title=full_entry.get('title', full_entry.get('url')),
                        stream_url=stream_url
                    ))

        if not queue:
            return

        # 🚀 Если всё ок, продолжаем
        guild_music.queue.extend(queue)

        await interaction.followup.send(f"Added {len(queue)} track(s) to the queue.")

        if not guild_music.vc.is_playing() and not guild_music.vc.is_paused():
            await self._play_current(interaction)

    async def toggle_loop_queue(self, interaction: discord.Interaction):
        guild = interaction.guild or interaction.user.guild

        guild_music = self.get_guild_music(guild.id)
        guild_music.loop_queue = not getattr(guild_music, 'loop_queue', False)
        state = "enabled" if guild_music.loop_queue else "disabled"
        await interaction.followup.send(f"Loop Queue {state}\n\n*(After the end of the queue, it will repeat all tracks.)*")

    async def _process_background_tracks(self, entries, guild_id, interaction=None):
        guild_music = self.get_guild_music(guild_id)

        loop = asyncio.get_event_loop()

        for entry in entries:
            if entry.get('_type') == 'url':
                full_entry = await loop.run_in_executor(None,
                                                        lambda: self.ytdl.extract_info(entry['url'], download=False, process=True))
            else:
                full_entry = entry

            stream_url = self.get_any_audio_format(full_entry.get('formats', []))
            if stream_url:
                guild_music.queue.append(TrackInfo(
                    url=full_entry.get('webpage_url', full_entry.get('url')),
                    title=full_entry.get('title', full_entry.get('url')),
                    stream_url=stream_url
                ))

            await asyncio.sleep(0.1)

        if interaction:
            await interaction.followup.send(f"Added {len(entries)} track(s) to the queue.")

    def get_any_audio_format(self, formats):
        for f in formats:
            if f.get('vcodec') == 'none' and f.get('acodec') != 'none':
                return f['url']  # Возвращаем первую нормальную аудиоссылку
        return None

    async def _play_current(self, interaction: discord.Interaction, ignore_stop=False):
        guild = interaction.guild or interaction.user.guild
        guild_music = self.get_guild_music(guild.id)

        if not interaction.user.voice or not interaction.user.voice.channel:
            if not guild_music.loop247: # if 24/7 disabled dont play
                await interaction.followup.send("You're not in a voice channel.")
                return

        # Прямо перед созданием ffmpeg player
        track = guild_music.queue[guild_music.current_index]

        if track.stream_url.endswith('.m3u8'):
            # Перезапрашиваем
            new_info = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.ytdl.extract_info(track.url, download=False, process=True)
            )
            new_url = self.get_any_audio_format(new_info.get('formats', []))
            if new_url:
                track.stream_url = new_url

        if guild_music.vc.is_playing() or guild_music.vc.is_paused():
            guild_music.vc.stop()
            await asyncio.sleep(0.5)

        source = discord.FFmpegPCMAudio(track.stream_url, **self.FFMPEG_OPTIONS)

        def after_play(e):
            if not ignore_stop:
                self.bot.loop.create_task(self._after_track(interaction))

        guild_music.vc.play(source, after=after_play)

        # load up track image link
        if track.url.startswith("https://www.youtube.com/watch?v="):
            video_id = track.url.split("v=")[-1]
            thumbnail_url = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
        else:
            thumbnail_url = None
        # send embed with thumbnail

        track_title_with_url = f"[{track.title}]({track.url})"
        embed = discord.Embed(title="Now Playing", description=track_title_with_url)
        if thumbnail_url:
            embed.set_image(url=thumbnail_url)
        view = PlayerView(self)

        # if user is not in voice just dont send the embed
        if interaction.user.voice is None:
            if not guild_music.loop247:
                await guild_music.vc.disconnect(force=True)
                return  # выходим из функции, чтобы дальше код не шёл
            # если 24/7 включен — просто пропускаем отправку embed
        else:
            await interaction.followup.send(embed=embed, view=view)

    async def _after_track(self, interaction: discord.Interaction):
        guild_music = self.get_guild_music(interaction.guild.id)
        if guild_music.skip_flag:
            guild_music.skip_flag = False
            return

        await self.advance_track(guild_music, interaction, direction=1, after_track_next=True)

    async def stop(self, interaction: discord.Interaction):
        guild = interaction.guild or interaction.user.guild

        guild_music = self.get_guild_music(guild.id)
        if guild_music.vc:
            guild_music.vc.stop()
            guild_music.queue.clear()
            guild_music.current_index = 0
            await interaction.followup.send("Stopped playback.")

    async def pause(self, interaction: discord.Interaction):
        guild = interaction.guild or interaction.user.guild

        guild_music = self.get_guild_music(guild.id)
        if guild_music.vc and guild_music.vc.is_playing():
            guild_music.vc.pause()
            await interaction.followup.send("Paused.")
        elif guild_music.vc and guild_music.vc.is_paused():
            guild_music.vc.resume()
            await interaction.followup.send("Resumed.")
        else:
            await interaction.followup.send("Nothing to pause or resume.")

    async def next(self, interaction: discord.Interaction):
        guild = interaction.guild or interaction.user.guild
        guild_music = self.get_guild_music(guild.id)
        await self.advance_track(guild_music, interaction, direction=1)

    async def previous(self, interaction: discord.Interaction):
        guild = interaction.guild or interaction.user.guild
        guild_music = self.get_guild_music(guild.id)
        await self.advance_track(guild_music, interaction, direction=-1)

    async def advance_track(self, guild_music, interaction, direction: int = 1, after_track_next=False):
        mode_used = ""
        if direction == 1:
            if guild_music.current_index + 1 >= len(guild_music.queue):
                if guild_music.loop247:
                    mode_used = "Loop 24/7 (Shuffle all track and start from 1)"
                    random.shuffle(guild_music.queue)
                    guild_music.current_index = 0
                elif guild_music.loop_queue:
                    mode_used = "Loop Queue (Repeat all tracks)"
                    guild_music.current_index = 0
                elif guild_music.random_mode:
                    mode_used = "Random"
                    guild_music.current_index = random.randint(0, len(guild_music.queue) - 1)
                else:
                    mode_used = "End of Queue (Stop playback)"
                    await interaction.followup.send("Queue ended.")
                    return
            else:
                guild_music.current_index = random.randint(0, len(guild_music.queue) - 1) if guild_music.random_mode else guild_music.current_index + 1
                mode_used = "Next Track" if not guild_music.random_mode else "Random Track"
        elif direction == -1:
            if guild_music.random_mode:
                mode_used = "Random Track"
                guild_music.current_index = random.randint(0, len(guild_music.queue) - 1)
            elif guild_music.loop_queue:
                mode_used = "Loop Queue (Repeat all tracks)"
                guild_music.current_index = len(guild_music.queue) - 1 if guild_music.current_index == 0 else guild_music.current_index - 1
            elif guild_music.loop247:
                mode_used = "Loop 24/7 (Shuffle all track and start from 1)"
                if guild_music.current_index == 0:
                    random.shuffle(guild_music.queue)
                guild_music.current_index = 0
            else:
                if guild_music.current_index > 0:
                    mode_used = "Previous Track"
                    guild_music.current_index -= 1
                else:
                    mode_used = "First Track"
                    guild_music.current_index = 0  # Stay at 0 if nothing else

        guild_music.skip_flag = not after_track_next
        guild_music.vc.stop()
        await asyncio.sleep(0.5)
        if interaction.user.voice is not None:
            await interaction.followup.send(f"⏩ {mode_used}: {guild_music.queue[guild_music.current_index].title}")
        await self._play_current(interaction)

    async def toggle_247(self, interaction: discord.Interaction):
        guild_music = self.get_guild_music(interaction.guild.id)
        guild_music.loop247 = not guild_music.loop247
        state = "enabled" if guild_music.loop247 else "disabled"
        await interaction.followup.send(f"24/7 mode {state}\n\n*(After the end of the queue, it will shuffle all tracks and start from the first one. (btw the bot wont leave voice after end of track if youre not in voice channel))*")

    # New: Shuffle the entire queue and restart playback
    async def shuffle(self, interaction: discord.Interaction):
        guild_music = self.get_guild_music(interaction.guild.id)
        guild_music.random_mode = not getattr(guild_music, 'random_mode', False)
        state = "enabled" if guild_music.random_mode else "disabled"
        await interaction.followup.send(f"Random mode {state}\n\n*(Every next track will be randomly selected from the queue.)*")

    # New: Show full queue list
    async def show_queue(self, interaction: discord.Interaction):
        guild_music = self.get_guild_music(interaction.guild.id)
        if not guild_music.queue:
            await interaction.followup.send("Queue is empty.")
            return


        lines = []
        for idx, track in enumerate(guild_music.queue):
            prefix = f'▶️ {idx + 1}.' if idx == guild_music.current_index else f'{idx + 1}.'
            lines.append(f"{prefix} {track.title}")

        msg = "\n".join(lines)

        if len(msg) > 1900:
            chunks = [msg[i:i + 1900] for i in range(0, len(msg), 1900)]

            await interaction.followup.send("**Current Queue:**")  # Заголовок один раз

            for chunk in chunks:
                await interaction.followup.send(chunk)  # Просто куски текста
        else:
            await interaction.followup.send(f"**Current Queue:**\n{msg}")

    async def search(self, interaction: discord.Interaction, query: str):
        guild_music = self.get_guild_music(interaction.guild.id)
        loop = asyncio.get_event_loop()

        await self.connect_if_not_connected(interaction)

        # ✅ Проверяем перед defer
        if not interaction.response.is_done():
            await interaction.response.defer()

        search_url = f"ytsearch:{query}"
        info = await loop.run_in_executor(None, lambda: self.ytdl.extract_info(search_url, download=False))

        if not info or 'entries' not in info or len(info['entries']) == 0:
            await interaction.followup.send("❌ No results found.")
            return

        entry = info['entries'][0]

        if entry.get('_type') == 'url':
            full_entry = await loop.run_in_executor(None, lambda: self.ytdl.extract_info(entry['url'], download=False,
                                                                                         process=True))
        else:
            full_entry = entry

        stream_url = self.get_any_audio_format(full_entry.get('formats', []))
        if not stream_url:
            await interaction.followup.send("❌ Couldn't extract audio stream.")
            return

        guild_music = self.get_guild_music(interaction.guild.id)

        guild_music.queue.append(TrackInfo(
            url=full_entry.get('webpage_url', full_entry.get('url')),
            title=full_entry.get('title', query),
            stream_url=stream_url
        ))

        await interaction.followup.send(f"🎵 Added to queue: **{full_entry.get('title', query)}**")

        if guild_music.vc and not guild_music.vc.is_playing() and not guild_music.vc.is_paused():
            await self._play_current(interaction)

    def load_favorites(self):
        if not os.path.exists(FAV_FILE):
            os.makedirs(os.path.dirname(FAV_FILE), exist_ok=True)
            with open(FAV_FILE, "w", encoding="utf-8-sig") as f:
                json.dump({}, f)
            return {}
        with open(FAV_FILE, "r", encoding="utf-8-sig") as f:
            content = f.read().strip()
            if not content:
                return {}
            return json.loads(content)

    def save_favorites(self, favorites):
        os.makedirs(os.path.dirname(FAV_FILE), exist_ok=True)
        with open(FAV_FILE, "w", encoding="utf-8-sig") as f:
            json.dump(favorites, f, indent=2)

    async def fav(self, interaction: discord.Interaction):
        if not interaction.response.is_done():
            await interaction.response.defer(ephemeral=True)

        guild_music = self.get_guild_music(interaction.guild.id)
        if not guild_music.queue:
            await interaction.followup.send("❌ No track to add to favorites.", ephemeral=True)
            return

        current_track = guild_music.queue[guild_music.current_index]

        favorites = self.load_favorites()
        user_id = str(interaction.user.id)

        if user_id not in favorites:
            favorites[user_id] = []

        # Проверка: не добавлять один и тот же трек дважды
        if any(fav.get('url') == current_track.url for fav in favorites[user_id]):
            await interaction.followup.send("⚠️ This track is already in your favorites.", ephemeral=True)
            return

        favorites[user_id].append({
            "title": current_track.title,
            "url": current_track.url,
            "stream_url": current_track.stream_url
        })

        self.save_favorites(favorites)
        await interaction.followup.send(f"✅ Added **{current_track.title}** to your favorites.", ephemeral=True)

    async def favall(self, interaction: discord.Interaction):
        if not interaction.response.is_done():
            await interaction.response.defer(ephemeral=True)

        guild_music = self.get_guild_music(interaction.guild.id)
        if not guild_music.queue:
            await interaction.followup.send("❌ No track to add to favorites.", ephemeral=True)
            return

        favorites = self.load_favorites()
        user_id = str(interaction.user.id)

        if user_id not in favorites:
            favorites[user_id] = []

        for track in guild_music.queue:
            # Проверка: не добавлять один и тот же трек дважды
            if any(fav.get('url') == track.url for fav in favorites[user_id]):
                continue

            favorites[user_id].append({
                "title": track.title,
                "url": track.url,
                "stream_url": track.stream_url
            })

        self.save_favorites(favorites)
        await interaction.followup.send(f"✅ Added all tracks to your favorites.", ephemeral=True)

    async def unfav(self, interaction: discord.Interaction):
        if not interaction.response.is_done():
            await interaction.response.defer(ephemeral=True)

        favorites = self.load_favorites()
        user_id = str(interaction.user.id)

        if user_id not in favorites:
            await interaction.followup.send("❌ You have no favorite songs.", ephemeral=True)
            return

        user_favs = favorites[user_id]

        if not user_favs:
            await interaction.followup.send("❌ You have no favorite songs.", ephemeral=True)
            return

        view = discord.ui.View()
        view.add_item(FavDropdown(user_favs, self, mode="remove"))

        await interaction.followup.send("🎵 Choose a favorite to remove:", view=view, ephemeral=True)

    async def connect_if_not_connected(self, interaction: discord.Interaction, force: bool = False):
        guild_music = self.get_guild_music(interaction.guild.id)
        if not interaction.user.voice or not interaction.user.voice.channel:
            await interaction.followup.send("You're not in a voice channel.")
            return
        channel = interaction.user.voice.channel
        if not guild_music.vc or not guild_music.vc.is_connected():
            guild_music.vc = await channel.connect()
            guild_music.user_who_added_id = interaction.user.id

            # 💥 Тут после подключения - проверка на наличие микса
            mix_path = os.path.join(MIXES_DIR, f"{interaction.guild.id}.json")
            if os.path.exists(mix_path):
                # ⚡ Отправляем кнопки
                view = LoadMixPromptView(self, interaction)
                await interaction.followup.send("🎵 Found a saved mix for this server. Load it?", view=view,
                                                ephemeral=True)
        else:
            if force:
                await guild_music.vc.move_to(channel)
                await interaction.followup.send(f"✅ Moved to {channel.name}.")
                guild_music.user_who_added_id = interaction.user.id
            elif guild_music.vc.channel == channel:
                print("Already connected to the same channel.")
            else:
                await interaction.followup.send("❌ Bot is already connected to another voice channel. Use /forcejoin (music user only) to reconnect it.", ephemeral=True)
                return

    async def nowplaying(self, interaction: discord.Interaction):
        guild_music = self.get_guild_music(interaction.guild.id)
        if not guild_music.queue:
            await interaction.followup.send("❌ No song is currently playing.", ephemeral=True)
            return

        track = guild_music.queue[guild_music.current_index]
        track_thumbnail = None
        if track.url.startswith("https://www.youtube.com/watch?v="):
            video_id = track.url.split("v=")[-1]
            track_thumbnail = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"

        embed = discord.Embed(title="Now Playing 🎶", description=f"[{track.title}]({track.url})",
                              color=discord.Color.blurple())
        if track_thumbnail:
            embed.set_image(url=track_thumbnail)

        await interaction.followup.send(embed=embed)

    async def skipto(self, interaction: discord.Interaction, track_number: int):
        if not interaction.response.is_done():
            await interaction.response.defer()

        guild_music = self.get_guild_music(interaction.guild.id)
        if not guild_music.queue:
            await interaction.followup.send("❌ No song is currently playing.")
            return

        if track_number < 1 or track_number > len(guild_music.queue):
            await interaction.followup.send(
                f"❌ Invalid track number. Please choose a number between 1 and {len(guild_music.queue)}.")
            return

        guild_music.current_index = track_number - 1
        print(f"Skipping to track {track_number}: {guild_music.queue[guild_music.current_index].title}")

        if guild_music.vc.is_playing() or guild_music.vc.is_paused():
            try:
                guild_music.skip_flag = True
                guild_music.vc.stop()
            except Exception:
                pass

        await asyncio.sleep(0.5)  # (на всякий случай дать остановиться)

        await self._play_current(interaction)
        await interaction.followup.send(
            f"⏩ Skipped to track {track_number}: {guild_music.queue[guild_music.current_index].title}")
        guild_music.skip_flag = False

    async def loadmix(self, interaction: discord.Interaction):
        if not interaction.response.is_done():
            await interaction.response.defer()

        guild_music = self.get_guild_music(interaction.guild.id)
        mix_path = os.path.join(MIXES_DIR, f"{interaction.guild.id}.json")

        if not os.path.exists(mix_path):
            await interaction.followup.send("❌ No saved mix found for this server.")
            return

        with open(mix_path, "r", encoding="utf-8") as f:
            mix_data = json.load(f)

        for track in mix_data:
            guild_music.queue.append(
                TrackInfo(
                    url=track["url"],
                    title=track["title"],
                    stream_url=track.get("stream_url", track["url"])
                )
            )

        await self.connect_if_not_connected(interaction)

        if not guild_music.vc.is_playing() and not guild_music.vc.is_paused():
            await self._play_current(interaction)

        await interaction.followup.send(f"✅ Loaded {len(mix_data)} tracks into queue!")

    async def removetrack(self, interaction: discord.Interaction, track_number: int):
        if not interaction.response.is_done():
            await interaction.response.defer()

        guild_music = self.get_guild_music(interaction.guild.id)

        if not guild_music.queue:
            await interaction.followup.send("❌ Queue is empty.")
            return

        if track_number < 1 or track_number > len(guild_music.queue):
            await interaction.followup.send(f"❌ Invalid track number. Choose between 1 and {len(guild_music.queue)}.")
            return

        removed_track = guild_music.queue.pop(track_number - 1)

        # ⚡ Корректировка current_index если надо
        if track_number - 1 < guild_music.current_index:
            guild_music.current_index -= 1
        elif track_number - 1 == guild_music.current_index:
            # Если удалили текущий трек:
            if guild_music.current_index >= len(guild_music.queue):
                guild_music.current_index = max(0, len(guild_music.queue) - 1)
            # Не трогаем playing — пусть доиграет

        await interaction.followup.send(f"🗑️ Removed **{removed_track.title} **from the queue.")

    async def playnext(self, interaction: discord.Interaction, track_number: int):
        if not interaction.response.is_done():
            await interaction.response.defer()

        guild_music = self.get_guild_music(interaction.guild.id)

        if not guild_music.queue:
            await interaction.followup.send("❌ Queue is empty.")
            return

        if track_number < 1 or track_number > len(guild_music.queue):
            await interaction.followup.send(
                f"❌ Invalid track number. Must be between 1 and {len(guild_music.queue)}.")
            return

        target_index = track_number - 1

        if target_index == guild_music.current_index:
            await interaction.followup.send("❌ This track is already playing.")
            return

        track = guild_music.queue.pop(target_index)

        # вставляем сразу после текущего трека
        insert_index = guild_music.current_index + 1
        guild_music.queue.insert(insert_index, track)

        await interaction.followup.send(
            f"✅ Moved **{track.title}** to play next (after current track)."
        )

        # View Buttons
class PlayerView(discord.ui.View):
    def __init__(self, controller: MusicController):
        super().__init__(timeout=None)
        self.controller = controller


    @discord.ui.button(label="⏮️ Previous", style=discord.ButtonStyle.primary)
    async def previous_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()

        await self.controller.previous(interaction)


    @discord.ui.button(label="⏯️ Pause/Resume", style=discord.ButtonStyle.secondary)
    async def pause_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()

        await self.controller.pause(interaction)

    @discord.ui.button(label="⏭️ Next", style=discord.ButtonStyle.primary)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()

        await self.controller.next(interaction)

    @discord.ui.button(label="⏹️ Clear Queue and Stop", style=discord.ButtonStyle.danger)
    async def stop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()

        await self.controller.stop(interaction)


class LoadMixPromptView(ui.View):
    def __init__(self, controller, interaction):
        super().__init__(timeout=30)
        self.controller = controller
        self.interaction = interaction

    @ui.button(label="✅ Load Mix", style=discord.ButtonStyle.success)
    async def load_mix(self, interaction: discord.Interaction, button: ui.Button):
        await self.controller.loadmix(self.interaction)
        self.stop()

    @ui.button(label="❌ No", style=discord.ButtonStyle.danger)
    async def no_mix(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.edit_message(view=None)  # Удаляем кнопки после ответа
        await interaction.response.send_message("❌ Mix load canceled.", ephemeral=True)
        self.stop()



class FavDropdown(discord.ui.Select):
    def __init__(self, user_favs, controller, mode="load"):
        self.controller = controller
        self.user_favs = user_favs
        self.mode = mode

        options = [discord.SelectOption(label=fav.get('title', 'Unknown Title'), description=fav.get('url', '')[:100]) for fav in user_favs]

        if mode == "load":
            options.append(discord.SelectOption(label="➕ Add All", description="Add all favorite songs"))
        elif mode == "remove":
            options.append(discord.SelectOption(label="➖ Remove All", description="Remove all favorite songs"))

        super().__init__(placeholder="Choose a favorite song to add..." if mode == "load" else "Choose favorite song to remove", options=options)



    async def callback(self, interaction_select: discord.Interaction):
        guild_music = self.controller.get_guild_music(interaction_select.guild.id)

        selected = self.values[0]
        if self.mode == "load":
            if selected == "➕ Add All":
                for fav in self.user_favs:
                    await self.self_add(fav, interaction_select)
                await interaction_select.response.send_message("✅ Added all favorite songs to the queue.", ephemeral=True)
            else:
                fav = next((f for f in self.user_favs if f.get('title', 'Unknown Title') == selected), None)
                if fav:
                    await self.self_add(fav, interaction_select)
                    await interaction_select.response.send_message(f"✅ Added {fav.get('title', 'Unknown')} to the queue.", ephemeral=True)
        elif self.mode == "remove":
            if selected == "➖ Remove All":
                favorites = self.controller.load_favorites()
                user_id = str(interaction_select.user.id)
                if user_id in favorites:
                    del favorites[user_id]
                    self.controller.save_favorites(favorites)
                    await interaction_select.response.send_message("✅ Removed all favorite songs.", ephemeral=True)
                else:
                    await interaction_select.response.send_message("❌ No favorite songs to remove.", ephemeral=True)
            else:
                fav = next((f for f in self.user_favs if f.get('title', 'Unknown Title') == selected), None)
                if fav:
                    favorites = self.controller.load_favorites()
                    user_id = str(interaction_select.user.id)
                    if user_id in favorites and fav in favorites[user_id]:
                        favorites[user_id].remove(fav)
                        self.controller.save_favorites(favorites)
                        await interaction_select.response.send_message(f"✅ Removed {fav.get('title', 'Unknown')} from favorites.", ephemeral=True)
                    else:
                        await interaction_select.response.send_message("❌ Favorite song not found.", ephemeral=True)

        if not guild_music.vc.is_playing() and not guild_music.vc.is_paused():
            self.controller.skip_flag = True
            self.controller.bot.loop.create_task(self.controller._play_current(interaction_select))

    async def self_add(self, fav, interaction_select):
        guild_music = self.controller.get_guild_music(interaction_select.guild.id)

        if not guild_music.vc or not guild_music.vc.is_connected():
            await self.controller.connect_if_not_connected(interaction_select)

        guild_music.queue.append(
            TrackInfo(
                url=fav.get('url'),
                title=fav.get('title', 'Unknown Title'),
                stream_url=fav.get('stream_url', fav.get('url'))  # если вдруг stream_url нет
            )
        )

