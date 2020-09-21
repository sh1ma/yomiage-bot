from __future__ import annotations

import os
from typing import Optional

import discord
from aiohttp import BasicAuth, ClientSession, StreamReader
from discord import AudioSource, Message, PCMAudio, TextChannel, VoiceClient
from discord.ext.commands import Bot, Cog, Context, command


class VoiceTextApiClient:
    def __init__(
        self, api_token: str, host: str = "https://api.voicetext.jp/v1"
    ) -> None:
        self.host = host
        self.session = ClientSession(raise_for_status=True, auth=BasicAuth(api_token))

    async def save_voice(self, text: str) -> None:
        resp = await self.session.post(
            self.host + "/tts",
            params={"text": text, "speaker": "hikari"},
        )
        async with resp:
            with open("a.wav", "wb") as f:
                f.write(await resp.read())


class Hello(Cog):
    def __init__(self, bot: Bot) -> None:
        self.bot: Bot = bot
        self.voice_joined: bool = False
        self.voice_client: Optional[VoiceClient] = None
        self.yomiage_channel: Optional[TextChannel] = None
        self.voicetext_api_client = VoiceTextApiClient(
            os.environ["VOICE_TEXT_API_TOKEN"]
        )

    @Cog.listener()
    async def on_message(self, message: Message) -> None:
        if not self.voice_joined:
            return
        if message.author.id == self.bot.user.id:
            return
        if message.channel == self.yomiage_channel:
            text = message.content
            if text and self.voice_client:
                await self.voicetext_api_client.save_voice(text)
                self.voice_client.play(discord.FFmpegPCMAudio("a.wav"))

    @command()
    async def join(self, ctx: Context) -> None:
        if self.voice_joined:
            await ctx.send("すでにボイスチャンネルに参加しています")
            return
        voice_ch = ctx.author.voice if ctx.author.voice else None
        if not voice_ch:
            await ctx.send("ボイスチャンネルに参加後、お試しください")
            return
        self.voice_joined = True
        self.voice_client = await voice_ch.channel.connect()
        self.yomiage_channel = ctx.channel
        await ctx.send("ボイスチャンネルに参加しました")

    @command()
    async def leave(self, ctx: Context) -> None:
        if not self.voice_joined:
            await ctx.send("ボイスチャンネルに参加していません")
            return
        if not self.voice_client:
            return
        await self.voice_client.disconnect()
        await ctx.send("ボイスチャンネルを退出しました")


def setup(bot: Bot) -> None:
    bot.add_cog(Hello(bot))
