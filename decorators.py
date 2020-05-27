from functools import wraps

from globals import GlobalState
from utils import update_channel, get_user_dm

def save_state(func):
    """
    Decorator to dump the state to disk after function is run
    """
    @wraps(func)
    async def decorated(*args, **kwargs):
        channel = await func(*args, **kwargs)
        state = GlobalState()
        state.save_current_state()
        if channel is not None:
            await update_channel(channel)
        return channel

    return decorated


def enforce_channels(*allowed_channels):
    """
    Decorator to enforce that we are in a zone channel
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            ctx = args[0]
            if ctx.message.channel.name not in allowed_channels:
                user_dm = await get_user_dm(ctx.message.author)
                await user_dm.send(
                    (
                        f"You sent `{ctx.message.content}` in {ctx.message.channel.mention}\n"
                        "That command is not allowed in that channel.\n"
                        f"You can retry in these channels: {allowed_channels}"
                    )
                )
                await ctx.message.delete()
                return
            return await func(*args, **kwargs)
        return wrapper
    return decorator
