import asyncio
import discord
from discord.ext import commands
from discord import file
import imaging
import roster
from io import BytesIO
import cakeshow
from config import credentials
import copy

class Botuser(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.broadcast_channel = None

    async def on_ready(self):
        print('Logged in as:')
        print(self.user.name)
        print(self.user.id)
        print('--------------')
        self.broadcast_channel = self.get_channel(credentials.broadcast_channel)
        print('Channel Target:')
        print(credentials.broadcast_channel)
        print('--------------')
        if self.broadcast_channel is None:
            print("WARNING: couldn't find a broadcast channel! Are your ENVIRONMENT VARIABLES set right?")


    async def broadcast(self, message):
        await self.broadcast_channel.send(message)

    async def broadcast_embed(self, in_embed, file=None):
        await self.broadcast_channel.send(embed=in_embed, file=file)


botuser = Botuser(command_prefix='!')


@botuser.command(name='test')
async def test(ctx):
    await cakeshow.test_show()


@botuser.command(name='cheer')
async def cheer(ctx, arg):
  if cakeshow.pending_show is not None:
    if arg == '1' or arg == '2':
      if arg == '1':
        res = await cakeshow.cheer(1, ctx.author)
      elif arg == '2':
        res = await cakeshow.cheer(2, ctx.author)
      
      if res:
        await ctx.send(':tada: *You successfully cheer on contestant no. '+ arg + '* :tada:')
      else:
        await ctx.send(':no_entry_sign: *Your cheers fall on deaf ears...* :no_entry_sign:\n(No more than one cheer per person, sorry)')
    else:
      await ctx.send(':no_entry_sign: **NO CAN DO, BOSS** :no_entry_sign:\nPlease enter a contestant number in numeral form.')
  else:
    await ctx.send(':no_entry_sign: **NO CAN DO, BOSS** :no_entry_sign:\nNo contestants are currently baking. You must wait until contestants are baking!')


@botuser.command(name='roster')
async def list_roster(ctx):
    if len(roster.players) > 0:
        msg = "**CURRENT CONTESTANTS:**\n"

        sortedroster = roster.players.copy()
        sortedroster.sort(key=compare_wins, reverse=True)

        for player in sortedroster:
            msg += "\n[" + player.wins + "-" + player.losses + "] " + player.name
        await ctx.send(msg)


def compare_wins(in_player):
  return in_player.wins - in_player.losses*0.001