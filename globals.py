import json
import logging
from dataclasses import asdict, dataclass, field, fields
from datetime import datetime
from os import path

import discord
from dotmap import DotMap

from settings import NUM_OF_LAYERS, NUMBER_EMOJI_MAPPING, SAVE_FILENAME, ZONES

logger = logging.getLogger(__name__)


ABSOLUTE_CURRENT_SAVE_FP = path.join(path.dirname(path.abspath(__file__)), SAVE_FILENAME)


@dataclass
class LotusSpot:
    name: str
    number: int
    player: int

    def as_presentable(self):
        data = {
            k: v.title()
            if isinstance(v, str) else v
            for k, v in asdict(self).items()
        }
        return LotusSpot(**data)

    def disc_table_fmt(self):
        return (
            f"{NUMBER_EMOJI_MAPPING[self.number]} | "
            f"**__{self.name}__** - {self.player.mention if self.player else 'FREE'}"
        )

    def disc_message_fmt(self):
        return f"{NUMBER_EMOJI_MAPPING[self.number]} - **__{self.name}__**"


class SingletonMetaclass(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


@dataclass
class GlobalState(metaclass=SingletonMetaclass):
    """
    Class that holds all the global state variables used by the bot.
    Though there arent any explcit static methods/variables, the metaclass enforces the singleton pattern.
    Any instantiation of this class with return the same instance of this class.

    ! NOT THREAD SAFE !
    """

    """Attributes that will be serialized/saved to disk"""
    state: dict = field(default_factory=dict)

    """Attributes that shouldnt be serialized/saved"""
    # Set to True in the on_ready() callback once all messages/channels have been properly deserialized/inited
    initialized = False
    # Reference to the discord info channel for message deleting
    info_channel = None
    boot_time = None

    def fresh_init(self):
        """
        self.state
        {
            'Eastern-Plaguelands': {
                'layers': {
                    1: {
                        'channel': None,
                        'table_message': None,
                        'status_message': None,
                        'timer': None,
                        'spots': {
                            1: <__main__.LotusSpot at 0x7f165999c190>,
                            2: <__main__.LotusSpot at 0x7f165999c1c0>,
                        }
                    },
                    2: {
                        'channel': None,
                        'table_message': None,
                        'status_message': None,
                        'timer': None,
                        'spots': {
                            1: <__main__.LotusSpot at 0x7f165999c370>,
                            2: <__main__.LotusSpot at 0x7f165999c3a0>,
                        }
                    }
                }
            }
        }

        for zone_name, zone in GlobalState().state.items():
            for layer_number, layer in zone.layers.items():
                channel = layer.channel
                table_message = layer.table_message
                for spot_number, spot in layer.spots.items():
                    pass
        """
        state = DotMap(_dynamic=True)
        for ZONE, ZONE_INFO in ZONES.items():
            state[ZONE] = DotMap()
            state[ZONE].layers = DotMap()

            for layer in range(1, NUM_OF_LAYERS + 1):
                state[ZONE].layers[layer].channel = None
                state[ZONE].layers[layer].table_message = None
                state[ZONE].layers[layer].status_message = None
                state[ZONE].layers[layer].spots = DotMap()
                state[ZONE].layers[layer].channel_name = ZONE_INFO["channel_format"].format(layer)
                state[ZONE].layers[layer].timer = None
                for spot in ZONE_INFO["spots"]:
                    spot_number = spot["number"]
                    spot_name = spot["name"]
                    print(type(spot_number))
                    state[ZONE].layers[layer].spots[spot_number] = LotusSpot(
                        name=spot_name,
                        number=spot_number,
                        player=None
                    )
        new_state = DotMap(state, _dynamic=False)
        self.state = new_state

    def _load_state(self, global_state):
        state = DotMap(global_state["state"], _dynamic=False)
        for zone in state:
            for layer in state[zone].layers:
                for spot in state[zone].layers[layer].spots:
                    state[zone].layers[layer].spots[spot] = LotusSpot(**state[zone].layers[layer].spots[spot])

        return state

    def load_current_saved_state(self):
        try:
            with open(ABSOLUTE_CURRENT_SAVE_FP, "r") as f:
                saved_state = json_load(f)
                saved_state["state"] = self._load_state(saved_state)
            self.__init__(**saved_state)
        except FileNotFoundError:
            logger.info("No save file found")

    def save_current_state(self):
        with open(ABSOLUTE_CURRENT_SAVE_FP, "w") as f:
            json_dump(self, f)

    def get_state_for_channel(self, channel):
        """
        returns the appropriate layer dict
        {
            'channel': None,
            'table_message': None,
            'status_message': None,
            'timer': None,
            'spots': {
                1: <__main__.LotusSpot at 0x7f165999c190>,
                2: <__main__.LotusSpot at 0x7f165999c1c0>,
        }
        """
        if isinstance(channel, discord.TextChannel):
            channel_name = channel.name
        else:
            channel_name = channel
        for zone_name, zone in self.state.items():
            for layer_number, layer_state in zone.layers.items():
                if channel_name == layer_state.channel_name:
                    return zone_name, layer_number, layer_state
        raise ValueError(f"|{channel_name}| channel state not found")


"""
Json loading/dumping wrappers in order to take care of datetimes/dataclasses
"""


def json_load(fp):
    """
    Custom json.load that automatically converts isoformat strings to their corresponding datetime object
    """
    def json_custom_deserializer(pairs):
        res = {}
        for k, v in pairs:
            if isinstance(v, str):
                try:
                    res[k] = datetime.fromisoformat(v)
                except ValueError:
                    res[k] = v
            else:
                res[k] = v
        return res

    return json.load(fp, object_pairs_hook=json_custom_deserializer)


def json_dump(obj, fp):
    """
    Custom json.dump that automatically converts datetime objects to isoformat strings and converts
        dataclasses to their dictionary representations
    """
    def json_custom_serializer(obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, GlobalState):
            # We do this rather than using asdict() as that tries to deepcopy the values returned
            #   This fails spectacularly for the discord.Message object
            return {field.name: getattr(obj, field.name) for field in fields(obj)}
        if isinstance(obj, LotusSpot):
            return {field.name: getattr(obj, field.name) for field in fields(obj)}
        if isinstance(obj, discord.Message):
            return obj.id
        if isinstance(obj, discord.TextChannel):
            return obj.name
        if isinstance(obj, discord.Member):
            return obj.id
        if isinstance(obj, DotMap):
            return obj.toDict()

    return json.dump(obj, default=json_custom_serializer, fp=fp)
