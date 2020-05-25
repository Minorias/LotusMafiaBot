import discord

from globals import GlobalState
from settings import LOTUS_WINDOW_END_DELTA, LOTUS_WINDOW_START_DELTA

# trick yoinked from raid-helper bot to get blank name/value in fields
BLANK = b'\xe2\x80\x8e'.decode()
DATE_FMT = "%d/%m/%Y at %H:%M"


async def update_channel(channel):
    await _update_status_message(channel)
    await _update_table_message(channel)


async def _update_status_message(channel):
    zone_name, layer_num, state = GlobalState().get_state_for_channel(channel)

    status_embed = discord.Embed(
        title=f"{zone_name} | Layer {layer_num}",
    )
    if state.timer is not None:
        status_embed.add_field(
            name=BLANK,
            value=(
                f"**Lotus was last picked:**\n"
                f"**{state.timer.strftime(DATE_FMT)}**"
            ),
        )
        status_embed.add_field(
            name=BLANK,
            value=BLANK,
        )
        status_embed.add_field(
            name=BLANK,
            value=(
                "**Free spots:**\n"
                f"{len([spot for spot in state.spots.values() if spot.player is None])}"
            )
        )
        window_open = state.timer + LOTUS_WINDOW_START_DELTA
        status_embed.add_field(
            name=BLANK,
            value=(
                "```diff\n"
                f"+ Next lotus window opens:\n"
                f"+ {window_open.strftime(DATE_FMT)}"
                "```"
            ),
        )
        window_close = state.timer + LOTUS_WINDOW_END_DELTA
        status_embed.add_field(
            name=BLANK,
            value=(
                "```diff\n"
                f"- Next lotus window closes:\n"
                f"- {window_close.strftime(DATE_FMT)}"
                "```"
            ),
        )
    else:
        status_embed.add_field(
            name=BLANK,
            value=(
                "**Lotus was last picked:**\n"
                "**¯\\_(ツ)_/¯**"
            ),
        )
        status_embed.add_field(
            name=BLANK,
            value=BLANK,
        )
        status_embed.add_field(
            name=BLANK,
            value=(
                "**Free spots:**\n"
                f"{len([spot for spot in state.spots.values() if spot.player is None])}"
            )
        )
        status_embed.add_field(
            name=BLANK,
            value=(
                "```diff\n"
                "+ Next lotus window opens:\n"
                "¯\\_(ツ)_/¯"
                "```"
            ),
        )
        status_embed.add_field(
            name=BLANK,
            value=(
                "```diff\n"
                "- Next lotus window closes:\n"
                "¯\\_(ツ)_/¯"
                "```"
            ),
        )

    await state.status_message.edit(embed=status_embed, content="")


async def _update_table_message(channel):
    zone_name, layer_num, state = GlobalState().get_state_for_channel(channel)

    table_embed = discord.Embed(
        title="Lotus Spots",
    )
    for spot in state.spots.values():
        table_embed.add_field(
            name=BLANK,
            value=spot.disc_table_fmt(),
            inline=False
        )
    await state.table_message.edit(embed=table_embed, content="")


async def get_user_dm(user):
    if user.dm_channel is None:
        await user.create_dm()
    return user.dm_channel
