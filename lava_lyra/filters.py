from __future__ import annotations

import collections
import inspect
from typing import Any, Self, override

from .exceptions import FilterInvalidArgument

__all__ = (
    "ChannelMix",
    "Distortion",
    "Equalizer",
    "Filter",
    "Karaoke",
    "LowPass",
    "Rotation",
    "Timescale",
    "Tremolo",
    "Vibrato",
)


class Filter:
    """
    The base class for all filters.
    You can use these filters if you have the latest Lavalink version
    installed. If you do not have the latest Lavalink version,
    these filters will not work.

    You must specify a tag for each filter you put on.
    This is necessary for the removal of filters.
    """

    __slots__ = ("payload", "preload", "tag")

    def __init__(self, *, tag: str):
        self.payload: dict[str, Any] | None = None
        self.tag: str = tag
        self.preload: bool = False

    def set_preload(self, status: bool = True) -> Self:
        """
        Internal method to set whether or not the filter was preloaded.
        Returns self to allow method chaining.
        """
        self.preload = status
        return self

    def _get_init_kwargs(self) -> dict[str, Any]:
        keys: set[str] = set()
        for klass in type(self).__mro__:
            keys.update(getattr(klass, "__slots__", ()))
        keys -= {"payload", "preload", "tag"}

        return {key: getattr(self, key) for key in keys}

    def update(self, **kwargs: Any) -> Self:
        current = self._get_init_kwargs()
        unknown = set(kwargs) - set(current)
        if unknown:
            raise FilterInvalidArgument(
                f"Unknown filter parameter(s): {', '.join(sorted(unknown))}",
            )
        current.update(kwargs)

        preload = self.preload
        type(self).__init__(self, tag=self.tag, **current)
        self.preload = preload

        return self

    def reset(self) -> Self:
        defaults = {
            key: value.default
            for key, value in inspect.signature(type(self).__init__).parameters.items()
            if key not in ("self", "tag") and value.default is not inspect.Parameter.empty
        }
        current = self._get_init_kwargs()
        current.update(defaults)
        type(self).__init__(self, tag=self.tag, **current)
        return self

    def __eq__(self, other: object) -> bool:
        """
        Checks if two filters are identical based on their type, tag, and payload.
        """
        if not isinstance(other, Filter):
            return NotImplemented

        return type(self) is type(other) and self.tag == other.tag and self.payload == other.payload


class Equalizer(Filter):
    """
    Filter which represents a 15 band equalizer.
    You can adjust the dynamic of the sound using this filter.
    i.e: Applying a bass boost filter to emphasize the bass in a song.
    The format for the levels is: List[Tuple[int, float]]
    """

    __slots__ = (
        "eq",
        "raw",
    )

    def __init__(self, *, tag: str, levels: list[tuple[int, float]]):
        super().__init__(tag=tag)

        self.eq = self._factory(levels)
        self.raw = levels

        self.payload = {"equalizer": self.eq}

    def _factory(self, levels: list[tuple[int, float]]) -> list[dict[str, int | float]]:
        _dict: dict[int, float] = collections.defaultdict(float)

        _dict.update(levels)
        data = [{"band": i, "gain": _dict[i]} for i in range(15)]

        return data

    @override
    def _get_init_kwargs(self) -> dict[str, Any]:
        return {"levels": self.raw}

    def __repr__(self) -> str:
        return f"<Lyra.EqualizerFilter tag={self.tag} eq={self.eq} raw={self.raw}>"

    @override
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Equalizer):
            return NotImplemented

        return self.raw == other.raw and self.tag == other.tag

    @classmethod
    def flat(cls) -> Equalizer:
        """Equalizer preset which represents a flat EQ board,
        with all levels set to their default values.
        """

        levels = [
            (0, 0.0),
            (1, 0.0),
            (2, 0.0),
            (3, 0.0),
            (4, 0.0),
            (5, 0.0),
            (6, 0.0),
            (7, 0.0),
            (8, 0.0),
            (9, 0.0),
            (10, 0.0),
            (11, 0.0),
            (12, 0.0),
            (13, 0.0),
            (14, 0.0),
        ]
        return cls(tag="flat", levels=levels)

    @classmethod
    def boost(cls) -> Equalizer:
        """Equalizer preset which boosts the sound of a track,
        making it sound fun and energetic by increasing the bass
        and the highs.
        """

        levels = [
            (0, -0.075),
            (1, 0.125),
            (2, 0.125),
            (3, 0.1),
            (4, 0.1),
            (5, 0.05),
            (6, 0.075),
            (7, 0.0),
            (8, 0.0),
            (9, 0.0),
            (10, 0.0),
            (11, 0.0),
            (12, 0.125),
            (13, 0.15),
            (14, 0.05),
        ]
        return cls(tag="boost", levels=levels)

    @classmethod
    def metal(cls) -> Equalizer:
        """Equalizer preset which increases the mids of a track,
        preferably one of the metal genre, to make it sound
        more full and concert-like.
        """

        levels = [
            (0, 0.0),
            (1, 0.1),
            (2, 0.1),
            (3, 0.15),
            (4, 0.13),
            (5, 0.1),
            (6, 0.0),
            (7, 0.125),
            (8, 0.175),
            (9, 0.175),
            (10, 0.125),
            (11, 0.125),
            (12, 0.1),
            (13, 0.075),
            (14, 0.0),
        ]

        return cls(tag="metal", levels=levels)

    @classmethod
    def piano(cls) -> Equalizer:
        """Equalizer preset which increases the mids and highs
        of a track, preferably a piano based one, to make it
        stand out.
        """

        levels = [
            (0, -0.25),
            (1, -0.25),
            (2, -0.125),
            (3, 0.0),
            (4, 0.25),
            (5, 0.25),
            (6, 0.0),
            (7, -0.25),
            (8, -0.25),
            (9, 0.0),
            (10, 0.0),
            (11, 0.5),
            (12, 0.25),
            (13, -0.025),
            (14, 0.0),
        ]
        return cls(tag="piano", levels=levels)


class Timescale(Filter):
    """Filter which changes the speed and pitch of a track.
    You can make some very nice effects with this filter,
    i.e: a vaporwave-esque filter which slows the track down
    a certain amount to produce said effect.
    """

    __slots__ = ("pitch", "rate", "speed")

    def __init__(self, *, tag: str, speed: float = 1.0, pitch: float = 1.0, rate: float = 1.0):
        super().__init__(tag=tag)

        if speed <= 0:
            raise FilterInvalidArgument("Timescale speed must be more than 0.")
        if pitch <= 0:
            raise FilterInvalidArgument("Timescale pitch must be more than 0.")
        if rate <= 0:
            raise FilterInvalidArgument("Timescale rate must be more than 0.")

        self.speed: float = speed
        self.pitch: float = pitch
        self.rate: float = rate

        self.payload = {
            "timescale": {"speed": self.speed, "pitch": self.pitch, "rate": self.rate},
        }

    @classmethod
    def vaporwave(cls) -> Timescale:
        """Timescale preset which slows down the currently playing track,
        giving it the effect of a half-speed record/casette playing.

        This preset will assign the tag 'vaporwave'.
        """

        return cls(tag="vaporwave", speed=0.8, pitch=0.8)

    @classmethod
    def nightcore(cls) -> Timescale:
        """Timescale preset which speeds up the currently playing track,
        which matches up to nightcore, a genre of sped-up music

        This preset will assign the tag 'nightcore'.
        """

        return cls(tag="nightcore", speed=1.25, pitch=1.3)

    def __repr__(self) -> str:
        return f"<Lyra.TimescaleFilter tag={self.tag} speed={self.speed} pitch={self.pitch} rate={self.rate}>"

    @override
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Timescale):
            return False

        return self.speed == other.speed and self.pitch == other.pitch and self.rate == other.rate


class Karaoke(Filter):
    """Filter which filters the vocal track from any song and leaves the instrumental.
    Best for karaoke as the filter implies.
    """

    __slots__ = ("filter_band", "filter_width", "level", "mono_level")

    def __init__(
        self,
        *,
        tag: str,
        level: float = 1.0,
        mono_level: float = 1.0,
        filter_band: float = 220.0,
        filter_width: float = 100.0,
    ):
        super().__init__(tag=tag)

        self.level: float = level
        self.mono_level: float = mono_level
        self.filter_band: float = filter_band
        self.filter_width: float = filter_width

        self.payload = {
            "karaoke": {
                "level": self.level,
                "monoLevel": self.mono_level,
                "filterBand": self.filter_band,
                "filterWidth": self.filter_width,
            },
        }

    def __repr__(self) -> str:
        return (
            f"<Lyra.KaraokeFilter tag={self.tag} level={self.level} mono_level={self.mono_level} "
            f"filter_band={self.filter_band} filter_width={self.filter_width}>"
        )

    @override
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Karaoke):
            return False

        return (
            self.level == other.level
            and self.mono_level == other.mono_level
            and self.filter_band == other.filter_band
            and self.filter_width == other.filter_width
        )


class Tremolo(Filter):
    """Filter which produces a wavering tone in the music,
    causing it to sound like the music is changing in volume rapidly.
    """

    __slots__ = ("depth", "frequency")

    def __init__(self, *, tag: str, frequency: float = 2.0, depth: float = 0.5):
        super().__init__(tag=tag)

        if frequency <= 0:
            raise FilterInvalidArgument(
                "Tremolo frequency must be greater than 0.",
            )
        if depth < 0 or depth > 1:
            raise FilterInvalidArgument(
                "Tremolo depth must be between 0 and 1.",
            )

        self.frequency: float = frequency
        self.depth: float = depth

        self.payload = {
            "tremolo": {
                "frequency": self.frequency,
                "depth": self.depth,
            },
        }

    def __repr__(self) -> str:
        return f"<Lyra.TremoloFilter tag={self.tag} frequency={self.frequency} depth={self.depth}>"

    @override
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Tremolo):
            return False

        return self.frequency == other.frequency and self.depth == other.depth


class Vibrato(Filter):
    """Filter which produces a wavering tone in the music, similar to the Tremolo filter,
    but changes in pitch rather than volume.
    """

    __slots__ = ("depth", "frequency")

    def __init__(self, *, tag: str, frequency: float = 2.0, depth: float = 0.5):
        super().__init__(tag=tag)

        if frequency <= 0 or frequency > 14:
            raise FilterInvalidArgument(
                "Vibrato frequency must be greater than 0 and at most 14.",
            )
        if depth < 0 or depth > 1:
            raise FilterInvalidArgument(
                "Vibrato depth must be between 0 and 1.",
            )

        self.frequency: float = frequency
        self.depth: float = depth

        self.payload = {
            "vibrato": {
                "frequency": self.frequency,
                "depth": self.depth,
            },
        }

    def __repr__(self) -> str:
        return f"<Lyra.VibratoFilter tag={self.tag} frequency={self.frequency} depth={self.depth}>"

    @override
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Vibrato):
            return False

        return self.frequency == other.frequency and self.depth == other.depth


class Rotation(Filter):
    """Filter which produces a stereo-like panning effect, which sounds like
    the audio is being rotated around the listener's head
    """

    __slots__ = ("rotation_hertz",)

    def __init__(self, *, tag: str, rotation_hertz: float = 5):
        super().__init__(tag=tag)

        self.rotation_hertz: float = rotation_hertz
        self.payload = {"rotation": {"rotationHz": self.rotation_hertz}}

    def __repr__(self) -> str:
        return f"<Lyra.RotationFilter tag={self.tag} rotation_hertz={self.rotation_hertz}>"

    @override
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Rotation):
            return False

        return self.rotation_hertz == other.rotation_hertz


class ChannelMix(Filter):
    """Filter which manually adjusts the panning of the audio, which can make
    for some cool effects when done correctly.
    """

    __slots__ = (
        "left_to_left",
        "left_to_right",
        "right_to_left",
        "right_to_right",
    )

    def __init__(
        self,
        *,
        tag: str,
        left_to_left: float = 1,
        right_to_right: float = 1,
        left_to_right: float = 0,
        right_to_left: float = 0,
    ):
        super().__init__(tag=tag)

        if left_to_left < 0 or left_to_left > 1:
            raise FilterInvalidArgument(
                "'left_to_left' must be between 0 and 1 (inclusive).",
            )
        if right_to_right < 0 or right_to_right > 1:
            raise FilterInvalidArgument(
                "'right_to_right' must be between 0 and 1 (inclusive).",
            )
        if left_to_right < 0 or left_to_right > 1:
            raise FilterInvalidArgument(
                "'left_to_right' must be between 0 and 1 (inclusive).",
            )
        if right_to_left < 0 or right_to_left > 1:
            raise FilterInvalidArgument(
                "'right_to_left' must be between 0 and 1 (inclusive).",
            )

        self.left_to_left: float = left_to_left
        self.left_to_right: float = left_to_right
        self.right_to_left: float = right_to_left
        self.right_to_right: float = right_to_right

        self.payload = {
            "channelMix": {
                "leftToLeft": self.left_to_left,
                "leftToRight": self.left_to_right,
                "rightToLeft": self.right_to_left,
                "rightToRight": self.right_to_right,
            },
        }

    def __repr__(self) -> str:
        return (
            f"<Lyra.ChannelMix tag={self.tag} left_to_left={self.left_to_left} left_to_right={self.left_to_right} "
            f"right_to_left={self.right_to_left} right_to_right={self.right_to_right}>"
        )

    @override
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ChannelMix):
            return False

        return (
            self.left_to_left == other.left_to_left
            and self.left_to_right == other.left_to_right
            and self.right_to_left == other.right_to_left
            and self.right_to_right == other.right_to_right
        )


class Distortion(Filter):
    """Filter which generates a distortion effect. Useful for certain filter implementations where
    distortion is needed.
    """

    __slots__ = (
        "cos_offset",
        "cos_scale",
        "offset",
        "scale",
        "sin_offset",
        "sin_scale",
        "tan_offset",
        "tan_scale",
    )

    def __init__(
        self,
        *,
        tag: str,
        sin_offset: float = 0,
        sin_scale: float = 1,
        cos_offset: float = 0,
        cos_scale: float = 1,
        tan_offset: float = 0,
        tan_scale: float = 1,
        offset: float = 0,
        scale: float = 1,
    ):
        super().__init__(tag=tag)

        self.sin_offset: float = sin_offset
        self.sin_scale: float = sin_scale
        self.cos_offset: float = cos_offset
        self.cos_scale: float = cos_scale
        self.tan_offset: float = tan_offset
        self.tan_scale: float = tan_scale
        self.offset: float = offset
        self.scale: float = scale

        self.payload = {
            "distortion": {
                "sinOffset": self.sin_offset,
                "sinScale": self.sin_scale,
                "cosOffset": self.cos_offset,
                "cosScale": self.cos_scale,
                "tanOffset": self.tan_offset,
                "tanScale": self.tan_scale,
                "offset": self.offset,
                "scale": self.scale,
            },
        }

    def __repr__(self) -> str:
        return (
            f"<Lyra.Distortion tag={self.tag} sin_offset={self.sin_offset} sin_scale={self.sin_scale}> "
            f"cos_offset={self.cos_offset} cos_scale={self.cos_scale} tan_offset={self.tan_offset} "
            f"tan_scale={self.tan_scale} offset={self.offset} scale={self.scale}"
        )

    @override
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Distortion):
            return False

        return (
            self.sin_offset == other.sin_offset
            and self.sin_scale == other.sin_scale
            and self.cos_offset == other.cos_offset
            and self.cos_scale == other.cos_scale
            and self.tan_offset == other.tan_offset
            and self.tan_scale == other.tan_scale
            and self.offset == other.offset
            and self.scale == other.scale
        )


class LowPass(Filter):
    """Filter which supresses higher frequencies and allows lower frequencies to pass.
    You can also do this with the Equalizer filter, but this is an easier way to do it.
    """

    __slots__ = ("smoothing",)

    def __init__(self, *, tag: str, smoothing: float = 20):
        super().__init__(tag=tag)

        self.smoothing: float = smoothing
        self.payload = {"lowPass": {"smoothing": self.smoothing}}

    def __repr__(self) -> str:
        return f"<Lyra.LowPass tag={self.tag} smoothing={self.smoothing}>"

    @override
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, LowPass):
            return False

        return self.smoothing == other.smoothing
