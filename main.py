import asyncio
import logging
import sys
from datetime import datetime

import discord
from discord.ext.commands import Bot, CommandNotFound, MissingRole, has_role

from decorators import save_state
from globals import GlobalState
from settings import ADMIN_ROLE_ID, AUTHORIZED_CHANNELS, DISCORD_TOKEN, PREFIX
from utils import get_user_dm, update_channel

logger = logging.getLogger(__name__)

bot = Bot(command_prefix=PREFIX)
bot.remove_command("help")


@bot.event
async def on_ready():
    logger.info(f"Successfully logged in as {bot.user.name}")
    global_state = GlobalState()

    servers = bot.guilds
    logger.info("Our servers are: {}".format([server.name for server in servers]))
    assert len(servers) == 1
    server = servers[0]
    logger.info(f"{server.name} is bae")

    # Populate channels with discord objects
    discord_channels = {channel.name: channel for channel in server.channels}
    for zone_name, zone in global_state.state.items():
        for layer_number, layer in zone.layers.items():
            channel = discord_channels.get(layer.channel_name, None)
            if channel is None:
                logger.error(f"Couldn't find |{layer.channel_name}| channel. Choices were: |{discord_channels}|")
                exit()
            layer.channel = channel

    # Populate messages with discord objects
    table_messages = [
            layer.table_message
            for zone in global_state.state.values()
            for layer in zone.layers.values()
    ]
    status_messages = [
            layer.status_message
            for zone in global_state.state.values()
            for layer in zone.layers.values()
    ]
    if not all(table_messages) or not all(status_messages):
        # One or more messages have not been initialised
        logger.warning("Messages werent initialised - Doing that now")
        # We assume that channels have been loaded above
        for zone_name, zone in GlobalState().state.items():
            for layer_number, layer in zone.layers.items():
                channel = layer.channel
                # Wipe channel
                await channel.purge(limit=None)
                layer.status_message = await channel.send("I'm bootin' baby!")
                layer.table_message = await channel.send("I'm bootin' baby!")
    else:
        # We assume that channels have been loaded above
        for zone_name, zone in GlobalState().state.items():
            for layer_number, layer in zone.layers.items():
                try:
                    layer.table_message = await layer.channel.fetch_message(layer.table_message)
                    layer.status_message = await layer.channel.fetch_message(layer.status_message)
                except discord.NotFound:
                    logger.error(f"Could not find message {layer.table_message}")
                    await layer.channel.send("Couldn't find my info message in here - Let Malzo know!")
                    exit()

    # Populate all the users
    for zone_name, zone in GlobalState().state.items():
        for layer_number, layer in zone.layers.items():
            for spot_number, spot in layer.spots.items():
                if spot.player is not None:
                    discord_member = server.get_member(spot.player)
                    if discord_member is None:
                        logger.warning(f"Failed to find user with id |{spot.player}|")
                    spot.player = discord_member

    for zone_name, zone in GlobalState().state.items():
        for layer_number, layer in zone.layers.items():
            await update_channel(layer.channel)
    global_state.initialized = True
    global_state.save_current_state()

    # chan = discord_channels["ony-calendar"]
    # msg = await chan.fetch_message(714483211119493121)
    # print(msg)
    # print(msg.embeds)
    # embed = msg.embeds[0]
    # print(embed.title)
    # print(embed.description)
    # for f in embed.fields:
    #     print("name", "|{}|".format(f.name), f.name.encode())
    #     print("value", f.value.encode())
    #     print(f.inline)
    #     print()


@bot.event
async def on_message(message):
    # Ignore messages that we sent
    if message.author.id == bot.user.id:
        return

    state = GlobalState()
    while not state.initialized:
        await asyncio.sleep(1)

    channel = message.channel
    # We only care for our 3 channels, rest can be ignored
    if channel.name in AUTHORIZED_CHANNELS:
        await bot.process_commands(message)
    else:
        logger.warning(f"Got message from unallowed channel {message}")


@bot.event
async def on_command_error(context, exception):
    if isinstance(exception, CommandNotFound):
        logger.warning(f"Unrecognized command: |{context.message.content}|")
        await context.channel.send("I do not recognize that command. Learn to type. Or read. Or both.")
    elif isinstance(exception, MissingRole):
        logger.warning(f"Missing role for user: |{context.message.author}| for message: |{context.message.content}")
        await context.channel.send("You do not have the permissions to use that command. Newb.")
    else:
        logger.error(
            f"Exception in command |{context.command}|. On message |{context.message.content}|. From user |{context.message.author.display_name}|",
            exc_info=(type(exception), exception, exception.__traceback__)
        )


@bot.command()
@save_state
async def signin(ctx, *spot_nums):
    # Remove duplicates
    spot_nums = list(set(spot_nums))

    user = ctx.message.author
    channel = ctx.message.channel
    user_dm = await get_user_dm(user)
    zone_name, layer_num, state = GlobalState().get_state_for_channel(channel)

    if len(spot_nums) == 0:
        await user_dm.send(
            (
                f"You sent `{ctx.message.content}` in {channel.mention}\n"
                "You need to give me atleast one lotus spot number\n"
                f"You can choose from the following: {[spot.number for spot in state.spots.values() if spot.player is None]}"
            )
        )
        await ctx.message.delete()
        return

    for spot_num in spot_nums:
        try:
            int(spot_num)
        except ValueError:
            await user_dm.send(
                (
                    f"You sent `{ctx.message.content}` in {channel.mention}\n"
                    "Pretty sure at least one of those aint a valid number\n"
                    f"You can choose from the following: {[spot.number for spot in state.spots.values() if spot.player is None]}"
                )
            )
            await ctx.message.delete()
            return

        if spot_num not in state.spots:
            await user_dm.send(
                (
                    f"You sent `{ctx.message.content}` in {channel.mention}\n"
                    "Pretty sure atleast one of those aint a valid spot number\n"
                    f"You can choose from the following: {[spot.number for spot in state.spots.values() if spot.player is None]}"
                )
            )
            await ctx.message.delete()
            return

        spot = state.spots[spot_num]
        if spot.player is not None:
            await user_dm.send(
                (
                    f"You sent `{ctx.message.content}` in {channel.mention}\n"
                    "At least one of those spots is already taken\n"
                    f"You can choose from the following: {[spot.number for spot in state.spots.values() if spot.player is None]}"
                )
            )
            await ctx.message.delete()
            return

    for spot_num in spot_nums:
        spot = state.spots[spot_num]
        spot.player = user

    lotus_spots = "\n".join([state.spots[spot_num].disc_message_fmt() for spot_num in spot_nums])
    await user_dm.send(
        (
            "Sign in confirmed.\n"
            f"Zone: {zone_name} | Layer: {layer_num}\n"
            f"{lotus_spots}"
        )
    )
    await ctx.message.delete()
    return ctx.channel



if __name__ == "__main__":
    logging.basicConfig(
        # filename=f"{path.dirname(path.abspath(__file__))}/lootbot.log",
        stream=sys.stdout,
        level=logging.INFO,
        filemode='a',
        format="%(levelname)s:%(name)s:[%(asctime)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    logging.getLogger("discord.gateway").setLevel(logging.WARNING)

    logging.info(" ")
    logging.info("-" * 50)
    logging.info(" ")

    GlobalState().load_current_saved_state()
    GlobalState().boot_time = datetime.now()

    try:
        logger.info("Starting the endless loop")
        boot_count = 0
        while True:
            boot_count += 1
            logger.info(f"!!! Running the bot - {boot_count} !!!")
            bot.run(DISCORD_TOKEN)
            logger.info("Bot returned - rerunning in loop")
    except RuntimeError:
        logger.exception(f"Exiting messily. Boot count: {boot_count}")
    except Exception:
        logger.exception(f"Lets see what hides here! Boot count: {boot_count}")
