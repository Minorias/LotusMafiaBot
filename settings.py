from datetime import timedelta

DISCORD_TOKEN = "lotus? what lotus?"

PREFIX = ">"
ADMIN_ROLE_ID = 713873303064019025
VIP_ROLE_ID = 713874692129423361
PLEB_ROLE_ID = 713874693224005733

NUM_OF_LAYERS = 2

EPL_SPOTS = [
    {
        "name": "Cauldron 1",
        "number": 1,
    },
    {
        "name": "Cauldron 2",
        "number": 2,
    },
    {
        "name": "Naxx",
        "number": 3,
    },
    {
        "name": "Northdale",
        "number": 4,
    },
    {
        "name": "Mill",
        "number": 5,
    },
    {
        "name": "Noxious Glade",
        "number": 6,
    },
    {
        "name": "Tyr's Hand",
        "number": 7,
    },
    {
        "name": "Corin's Crossing",
        "number": 8,
    },
    {
        "name": "Fungal Vale",
        "number": 9,
    },
    {
        "name": "Undercroft",
        "number": 10,
    },
]

ZONES = {
    "Eastern-Plaguelands": {
        "channel_format": "epl-layer-{}",
        "spots": EPL_SPOTS
    },
}

LOTUS_TIMER_CHANNEL_NAME = "lotus-timer-callouts"

AUTHORIZED_CHANNELS = [
    zone["channel_format"].format(layer) for zone in ZONES.values() for layer in range(1, NUM_OF_LAYERS+1)
] + [LOTUS_TIMER_CHANNEL_NAME]

SAVE_FILENAME = "lotus_yoink.exe"

NUMBER_EMOJI_MAPPING = {
    1: ":one:",
    2: ":two:",
    3: ":three:",
    4: ":four:",
    5: ":five:",
    6: ":six:",
    7: ":seven:",
    8: ":eight:",
    9: ":nine:",
    10: ":keycap_ten:",

}

LOTUS_WINDOW_START_DELTA = timedelta(minutes=45)
LOTUS_WINDOW_END_DELTA = timedelta(minutes=75)
try:
    from local_settings import *  # NOQA
except ImportError:
    print("No local_settings.py file")

try:
    from local_settings import DISCORD_TOKEN  # NOQA
except ImportError:
    print("Get your own token!")
    exit()
