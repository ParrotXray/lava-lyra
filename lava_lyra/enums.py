from __future__ import annotations

import re
from enum import Enum
from typing import override

__all__ = (
    "LavaSearchType",
    "LoopMode",
    "MixEndReason",
    "NodeAlgorithm",
    "PlaylistType",
    "RouteIPType",
    "RouteStrategy",
    "SearchType",
    "TrackType",
    "URLRegex",
)


class SearchType(Enum):
    """
    The enum for the different search/recommendation prefixes Lavalink search plugins
    understand. Used as the `search_type` param on `Node.get_tracks()` / `Player.get_tracks()`
    / `Node.load_search()` for any source, not just Spotify.

    SearchType.ytsearch searches using regular Youtube,
    which is best for all scenarios.

    SearchType.ytmsearch searches using YouTube Music,
    which is best for getting audio-only results.

    SearchType.scsearch searches using SoundCloud,
    which is an alternative to YouTube or YouTube Music.

    SearchType.amsearch/spsearch/bilisearch search Apple Music, Spotify, and Bilibili
    respectively. SearchType.sprec/dzrec/tdrec/jsrec request recommendations from Spotify,
    Deezer, Tidal, and JioSaavn respectively — used internally by `get_recommendations()`.
    SearchType.other is a passthrough for plugin-defined prefixes not listed here.
    """

    ytsearch = "ytsearch"
    ytmsearch = "ytmsearch"
    scsearch = "scsearch"
    amsearch = "amsearch"
    spsearch = "spsearch"
    bilisearch = "bilisearch"
    sprec = "sprec"
    dzrec = "dzrec"
    tdrec = "tdrec"
    jsrec = "jsrec"
    other = "other"

    @classmethod
    @override
    def _missing_(cls, value: object) -> SearchType:
        return cls.other

    def __str__(self) -> str:
        return str(self.value)


class TrackType(Enum):
    """
    The enum for the different track types for Lyra.

    TrackType.YOUTUBE defines that the track is from YouTube

    TrackType.YOUTUBE_MUSIC defines that the track is from YouTube Music

    TrackType.SOUNDCLOUD defines that the track is from SoundCloud.

    TrackType.SPOTIFY defines that the track is from Spotify

    TrackType.APPLE_MUSIC defines that the track is from Apple Music.

    TrackType.DEEZER defines that the track is from Deezer.

    TrackType.BANDCAMP defines that the track is from Bandcamp.

    TrackType.BILIBILI defines that the track is from Bilibili.

    TrackType.FACEBOOK defines that the track is from Facebook.

    TrackType.INSTAGRAM defines that the track is from Instagram.

    TrackType.NEWGROUNDS defines that the track is from Newgrounds.

    TrackType.QOBUZ defines that the track is from Qobuz.

    TrackType.TIDAL defines that the track is from Tidal.

    TrackType.JIOSAAVN defines that the track is from JioSaavn.

    TrackType.YTDLP defines that the track is from yt-dlp.

    TrackType.HTTP defines that the track is from an HTTP source.

    TrackType.LOCAL defines that the track is from a local source.

    TrackType.OTHER defines that the track is from an unknown source (possible from 3rd-party plugins).
    """

    # We don't have to define anything special for these, since these just serve as flags
    YOUTUBE = "youtube"
    YOUTUBE_MUSIC = "ytmusic"
    SOUNDCLOUD = "soundcloud"
    SPOTIFY = "spotify"
    APPLE_MUSIC = "applemusic"
    DEEZER = "deezer"
    BANDCAMP = "bandcamp"
    BILIBILI = "bilibili"
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    NEWGROUNDS = "newgrounds"
    QOBUZ = "qobuz"
    TIDAL = "tidal"
    JIOSAAVN = "jiosaavn"
    YTDLP = "ytdlp"
    HTTP = "http"
    LOCAL = "local"
    OTHER = "other"

    @classmethod
    @override
    def _missing_(cls, value: object) -> TrackType:
        return cls.OTHER

    def __str__(self) -> str:
        return str(self.value)


class PlaylistType(Enum):
    """
    The enum for the different playlist types for Lyra.

    PlaylistType.YOUTUBE defines that the playlist is from YouTube

    PlaylistType.SOUNDCLOUD defines that the playlist is from SoundCloud.

    PlaylistType.SPOTIFY defines that the playlist is from Spotify

    PlaylistType.APPLE_MUSIC defines that the playlist is from Apple Music.

    PlaylistType.BILIBILI/FACEBOOK/INSTAGRAM/YTDLP define the playlist is from Bilibili,
    Facebook, Instagram, or yt-dlp respectively.

    PlaylistType.OTHER defines that the playlist is from an unknown source (possible from 3rd-party plugins).
    """

    # We don't have to define anything special for these, since these just serve as flags
    YOUTUBE = "youtube"
    SOUNDCLOUD = "soundcloud"
    SPOTIFY = "spotify"
    APPLE_MUSIC = "applemusic"
    BILIBILI = "bilibili"
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    YTDLP = "ytdlp"
    OTHER = "other"

    @classmethod
    @override
    def _missing_(cls, value: object) -> PlaylistType:
        return cls.OTHER

    def __str__(self) -> str:
        return str(self.value)


class NodeAlgorithm(Enum):
    """
    The enum for the different node algorithms in Lyra.

    The enums in this class are to only differentiate different
    methods, since the actual method is handled in the
    get_best_node() method.

    NodeAlgorithm.by_ping returns a node based on it's latency,
    preferring a node with the lowest response time

    NodeAlgorithm.by_total_players return a nodes based on how many total players it has.
    This algorithm prefers nodes with the least amount of total players.

    NodeAlgorithm.by_playing_players return a nodes based on how many players are currently playing.
    This algorithm prefers nodes with the least amount of actively playing players.
    This is more accurate than by_total_players as it only considers active players.

    NodeAlgorithm.by_health returns a node based on its health score,
    which considers latency, uptime, player load, and connection stability.
    This is the recommended algorithm for multi-node setups.
    """

    # We don't have to define anything special for these, since these just serve as flags
    by_ping = "BY_PING"
    by_total_players = "BY_TOTAL_PLAYERS"
    by_playing_players = "BY_PLAYING_PLAYERS"
    by_health = "BY_HEALTH"

    def __str__(self) -> str:
        return str(self.value)


class LoopMode(Enum):
    """
    The enum for the different loop modes.
    This feature is exclusively for the queue utility of lyra.
    If you are not using this feature, this class is not necessary.

    LoopMode.TRACK sets the queue loop to the current track.

    LoopMode.QUEUE sets the queue loop to the whole queue.

    """

    # We don't have to define anything special for these, since these just serve as flags
    TRACK = "track"
    QUEUE = "queue"

    def __str__(self) -> str:
        return str(self.value)


class RouteStrategy(Enum):
    """
    The enum for specifying the route planner strategy for Lavalink.
    This feature is exclusively for the RoutePlanner class.
    If you are not using this feature, this class is not necessary.

    RouteStrategy.ROTATE_ON_BAN specifies that the node is rotating IPs
    whenever they get banned by Youtube.

    RouteStrategy.LOAD_BALANCE specifies that the node is selecting
    random IPs to balance out requests between them.

    RouteStrategy.NANO_SWITCH specifies that the node is switching
    between IPs every CPU clock cycle.

    RouteStrategy.ROTATING_NANO_SWITCH specifies that the node is switching
    between IPs every CPU clock cycle and is rotating between IP blocks on
    ban.

    """

    ROTATE_ON_BAN = "RotatingIpRoutePlanner"
    LOAD_BALANCE = "BalancingIpRoutePlanner"
    NANO_SWITCH = "NanoIpRoutePlanner"
    ROTATING_NANO_SWITCH = "RotatingNanoIpRoutePlanner"


class RouteIPType(Enum):
    """
    The enum for specifying the route planner IP block type for Lavalink.
    This feature is exclusively for the RoutePlanner class.
    If you are not using this feature, this class is not necessary.

    RouteIPType.IPV4 specifies that the IP block type is IPV4

    RouteIPType.IPV6 specifies that the IP block type is IPV6
    """

    IPV4 = "Inet4Address"
    IPV6 = "Inet6Address"


class URLRegex:
    """
    A namespace class holding all the compiled URL regexes used by Lyra.

    URLRegex.BILIBILI_URL returns the Bilibili URL Regex.

    URLRegex.SPOTIFY_URL returns the Spotify URL Regex.

    URLRegex.DISCORD_MP3_URL returns the Discord MP3 URL Regex.

    URLRegex.YOUTUBE_URL returns the Youtube URL Regex.

    URLRegex.YOUTUBE_TIMESTAMP returns the Youtube Timestamp Regex.

    URLRegex.AM_URL returns the Apple Music URL Regex.

    URLRegex.SOUNDCLOUD_URL returns the SoundCloud URL Regex.

    URLRegex.BASE_URL returns the standard URL Regex.

    """

    BILIBILI_URL = re.compile(
        r"^https?://(?:(?:www|m)\.)?(?:bilibili\.com|b23\.tv)/(?P<type>video|audio)/(?P<id>(?:(?P<audioType>am|au|av)?(?P<audioId>[0-9]+))|[A-Za-z0-9]+)/?(?:\?.*)?$"
    )

    SPOTIFY_URL = re.compile(
        r"https?://open\.spotify\.com/(?:intl-[a-zA-Z-]+/)?(?P<type>album|playlist|track|artist)/(?P<id>[a-zA-Z0-9]+)(?:/)?(?:\?.*)?$",
    )

    DISCORD_MP3_URL = re.compile(
        r"https?://cdn.discordapp.com/attachments/(?P<channel_id>[0-9]+)/"
        r"(?P<message_id>[0-9]+)/(?P<file>[a-zA-Z0-9_.]+)+",
    )

    YOUTUBE_URL = re.compile(
        r"^((?:https?:)?\/\/)?((?:www|m|music)\.)?((?:youtube\.com|youtu.be))"
        r"(\/(?:[\w\-]+\?v=|embed\/|v\/)?)([\w\-]+)(\S+)?$",
    )

    YOUTUBE_TIMESTAMP = re.compile(
        r"(?P<video>^.*?)(\?t|&t|&start)=(?P<time>\d+)?.*",
    )

    AM_URL = re.compile(
        r"https?://music\.apple\.com/(?P<country>[a-zA-Z]{2})/"
        r"(?P<type>album|playlist|song|artist)/(?P<name>.+?)/(?P<id>[^/?]+?)(?:/)?(?:\?.*)?$",
    )

    SOUNDCLOUD_URL = re.compile(
        r"((?:https?:)?\/\/)?((?:www|m)\.)?soundcloud.com\/.*/.*",
    )

    BASE_URL = re.compile(r"https?://(?:www\.)?.+")


class LavaSearchType(Enum):
    """
    The enum for the different search types for LavaSearch plugin.

    LavaSearchType.TRACK searches for tracks only.

    LavaSearchType.ALBUM searches for albums only.

    LavaSearchType.ARTIST searches for artists only.

    LavaSearchType.PLAYLIST searches for playlists only.

    LavaSearchType.TEXT searches for text results only.
    """

    TRACK = "track"
    ALBUM = "album"
    ARTIST = "artist"
    PLAYLIST = "playlist"
    TEXT = "text"

    def __str__(self) -> str:
        return str(self.value)


class MixEndReason(Enum):
    """
    Mix end reasons (NodeLink specific)

    MixEndReason.FINISHED indicates that playback completed naturally.
    MixEndReason.REMOVED indicates that the mix was manually removed via API.
    MixEndReason.ERROR indicates that a stream error occurred.
    MixEndReason.MAIN_ENDED indicates that the main track ended, triggering auto-cleanup

    """

    FINISHED = "FINISHED"
    REMOVED = "REMOVED"
    ERROR = "ERROR"
    MAIN_ENDED = "MAIN_ENDED"

    @classmethod
    @override
    def _missing_(cls, value: object) -> MixEndReason:
        return cls.FINISHED

    def __str__(self) -> str:
        return str(self.value)
