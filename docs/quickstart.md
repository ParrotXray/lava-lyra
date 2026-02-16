# Quick Jumpstart

If you want a quick example on how to get started with Lyra, look below:

## py-cord

```py
import lava_lyra
import discord


class MyBot(discord.Bot):
    def __init__(self) -> None:
        super().__init__(
            activity=discord.Activity(
                type=discord.ActivityType.listening, name="to music!"
            ),
        )

        self.add_cog(Music(self))

    async def on_ready(self) -> None:
        print("I'm online!")
        await self.cogs["Music"].start_nodes()


class Music(discord.Cog):
    def __init__(self, bot: discord.Bot) -> None:
        self.bot = bot

        self.pool = lava_lyra.NodePool()

    async def start_nodes(self) -> None:
        await self.pool.create_node(
            bot=self.bot,
            host="127.0.0.1",
            port=2333,
            password="youshallnotpass",
            identifier="MAIN",
        )
        print("Node is ready!")

    @discord.slash_command(name="join")
    async def join(
        self, ctx: discord.ApplicationContext, channel: discord.VoiceChannel = None
    ) -> None:
        if not channel:
            channel = getattr(ctx.author.voice, "channel", None)
            if not channel:
                return await ctx.respond(
                    "You must be in a voice channel to use this command "
                    "without specifying the channel argument."
                )

        await channel.connect(cls=lava_lyra.Player)
        await ctx.respond(f"Joined the voice channel `{channel}`")

    @discord.slash_command(name="play")
    async def play(self, ctx: discord.ApplicationContext, search: str) -> None:
        if not ctx.voice_client:
            await ctx.invoke(self.join)

        player = ctx.voice_client

        results = await player.get_tracks(query=search)

        if not results:
            return await ctx.respond("No results were found for that search term.")

        if isinstance(results, lava_lyra.Playlist):
            await player.play(track=results.tracks[0])
            await ctx.respond(f"Now playing: **{results.tracks[0].title}**")
        else:
            await player.play(track=results[0])
            await ctx.respond(f"Now playing: **{results[0].title}**")


bot = MyBot()
bot.run("token here")
```

## discord.py

```py
import lava_lyra
import discord
import re

from discord.ext import commands


class MyBot(commands.Bot):
    def __init__(self) -> None:
        super().__init__(
            command_prefix="!",
            activity=discord.Activity(
                type=discord.ActivityType.listening, name="to music!"
            ),
        )

        self.add_cog(Music(self))

    async def on_ready(self) -> None:
        print("I'm online!")
        await self.cogs["Music"].start_nodes()


class Music(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

        self.pool = lava_lyra.NodePool()

    async def start_nodes(self) -> None:
        await self.pool.create_node(
            bot=self.bot,
            host="127.0.0.1",
            port=2333,
            password="youshallnotpass",
            identifier="MAIN",
        )
        print("Node is ready!")

    @commands.command(name="join", aliases=["connect"])
    async def join(
        self, ctx: commands.Context, *, channel: discord.VoiceChannel = None
    ) -> None:
        if not channel:
            channel = getattr(ctx.author.voice, "channel", None)
            if not channel:
                raise commands.CheckFailure(
                    "You must be in a voice channel to use this command "
                    "without specifying the channel argument."
                )

        await ctx.author.voice.channel.connect(cls=lava_lyra.Player)
        await ctx.send(f"Joined the voice channel `{channel}`")

    @commands.command(name="play")
    async def play(self, ctx: commands.Context, *, search: str) -> None:
        if not ctx.voice_client:
            await ctx.invoke(self.join)

        player = ctx.voice_client

        results = await player.get_tracks(query=search)

        if not results:
            raise commands.CommandError("No results were found for that search term.")

        if isinstance(results, lava_lyra.Playlist):
            await player.play(track=results.tracks[0])
        else:
            await player.play(track=results[0])


bot = MyBot()
bot.run("token here")
```

:::{note}
Platform support (Spotify, Apple Music, etc.) is handled entirely by your Lavalink
server's plugins. No API credentials are needed in Lyra itself — configure them in
your `application.yml` instead.
:::