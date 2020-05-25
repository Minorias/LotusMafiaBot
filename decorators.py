from functools import wraps

from globals import GlobalState
from utils import update_channel


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

    return decorated
