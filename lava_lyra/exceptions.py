__all__ = (
    "FilterInvalidArgument",
    "FilterTagAlreadyInUse",
    "FilterTagInvalid",
    "LavalinkVersionIncompatible",
    "LyraException",
    "NoNodesAvailable",
    "NodeConnectionFailure",
    "NodeCreationError",
    "NodeException",
    "NodeNotAvailable",
    "NodeRestException",
    "NodelinkExclusive",
    "QueueEmpty",
    "QueueException",
    "QueueFull",
    "TrackInvalidPosition",
    "TrackLoadError",
)


class LyraException(Exception):
    """Base of all Lyra exceptions."""


class NodeException(LyraException):
    """Base exception for nodes."""


class NodeCreationError(NodeException):
    """There was a problem while creating the node."""


class NodeConnectionFailure(NodeException):
    """There was a problem while connecting to the node."""


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

    Lyra requires Lavalink v4.2.0+ or NodeLink v3.2.0+. Lavalink v3.x is not supported.
    """


class NodelinkExclusive(LyraException):
    """Exception raised when using a Nodelink exclusive feature on a Lavalink instance."""
