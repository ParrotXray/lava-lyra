__all__ = (
    "FilterInvalidArgument",
    "FilterTagAlreadyInUse",
    "FilterTagInvalid",
    "LavalinkVersionIncompatible",
    "LyraException",
    "NoNodesAvailable",
    "NodeConnectionClosed",
    "NodeConnectionFailure",
    "NodeCreationError",
    "NodeException",
    "NodeNotAvailable",
    "NodeRestException",
    "QueueEmpty",
    "QueueException",
    "QueueFull",
    "RequirementNotFound",
    "TrackInvalidPosition",
    "TrackLoadError",
    # Removed in v4: Platform-specific client exceptions
    # "InvalidSpotifyClientAuthorization",
    # "AppleMusicNotEnabled",
)


class LyraException(Exception):
    """Base of all Lyra exceptions."""


class NodeException(LyraException):
    """Base exception for nodes."""


class NodeCreationError(NodeException):
    """There was a problem while creating the node."""


class NodeConnectionFailure(NodeException):
    """There was a problem while connecting to the node."""


class NodeConnectionClosed(NodeException):
    """The node's connection is closed."""


class NodeRestException(NodeException):
    """A request made using the node's REST uri failed"""


class NodeNotAvailable(LyraException):
    """The node is currently unavailable."""


class NoNodesAvailable(LyraException):
    """There are no nodes currently available."""


class TrackInvalidPosition(LyraException):
    """An invalid position was chosen for a track."""


class TrackLoadError(LyraException):
    """There was an error while loading a track.

    In Lavalink v4, this could be due to:
    - Missing server-side plugins (LavaSrc, YouTube plugin, etc.)
    - Invalid API credentials configured on the Lavalink server
    - Platform-specific issues handled by plugins
    """


class FilterInvalidArgument(LyraException):
    """An invalid argument was passed to a filter."""


class FilterTagInvalid(LyraException):
    """An invalid tag was passed or Lyra was unable to find a filter tag"""


class FilterTagAlreadyInUse(LyraException):
    """A filter with a tag is already in use by another filter"""


class QueueException(LyraException):
    """Base Lyra queue exception."""


class QueueFull(QueueException):
    """Exception raised when attempting to add to a full Queue."""


class QueueEmpty(QueueException):
    """Exception raised when attempting to retrieve from an empty Queue."""


class LavalinkVersionIncompatible(LyraException):
    """Lavalink version is incompatible.

    Lyra v3.0+ requires Lavalink v4.0 or higher.
    For Lavalink v3.x support, use an older version of Lyra.
    """


class RequirementNotFound(LyraException):
    """Couldn't found any of discord packages.

    Neither discord.py nor py-cord could be found.
    Please install one of them before using.
    """


# Platform-specific exceptions have been removed in v4
# These are no longer needed as all platform support is handled
# by server-side plugins with their own configuration

# class InvalidSpotifyClientAuthorization(LyraException):
#     """No Spotify client authorization was provided for track searching."""
#     pass

# class AppleMusicNotEnabled(LyraException):
#     """An Apple Music Link was passed in when Apple Music functionality was not enabled."""
#     pass
