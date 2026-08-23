from __future__ import annotations

import random
from collections.abc import Iterable, Iterator
from copy import copy
from typing import Self, SupportsIndex, overload, override

from .enums import LoopMode
from .exceptions import QueueEmpty, QueueException, QueueFull
from .objects import Playlist, Track

__all__ = ("Queue",)


class Queue(Iterable[Track]):
    """Queue for Lyra. This queue takes lava_lyra.Track as an input and includes looping and shuffling."""

    __slots__ = (
        "_current_item",
        "_loop_mode",
        "_overflow",
        "_queue",
        "max_size",
    )

    def __init__(
        self,
        max_size: int | None = None,
        *,
        overflow: bool = True,
    ):
        self.max_size: int | None = max_size
        self._current_item: Track | None = None
        self._queue: list[Track] = []
        self._overflow: bool = overflow
        self._loop_mode: LoopMode | None = None

    def __str__(self) -> str:
        """String showing all Track objects appearing as a list."""
        return str([f"'{t}'" for t in self])

    def __repr__(self) -> str:
        """Official representation with max_size and member count."""
        return f"<{self.__class__.__name__} max_size={self.max_size} members={self.size}>"

    def __bool__(self) -> bool:
        """Treats the queue as a bool, with it evaluating True when it contains members."""
        return bool(self.size)

    def __call__(self, item: Track) -> None:
        """Allows the queue instance to be called directly in order to add a member."""
        self.put(item)

    def __len__(self) -> int:
        """Return the number of members in the queue."""
        return self.size

    @overload
    def __getitem__(self, index: SupportsIndex, /) -> Track: ...

    @overload
    def __getitem__(self, index: slice, /) -> list[Track]: ...

    def __getitem__(self, index: SupportsIndex | slice, /) -> Track | list[Track]:
        """Returns a member at the given position.
        Does not remove item from queue.
        """
        return self._queue[index]

    def __setitem__(self, index: SupportsIndex, item: Track, /) -> None:
        """Replaces the item at the given position."""
        self._check_track(item)
        self._queue[index] = item

    def __delitem__(self, index: int) -> None:
        """Delete item at given position."""
        self._queue.__delitem__(index)

    @override
    def __iter__(self) -> Iterator[Track]:
        """Iterate over members in the queue.
        Does not remove items when iterating.
        """
        return self._queue.__iter__()

    def __reversed__(self) -> Iterator[Track]:
        """Iterate over members in reverse order."""
        return self._queue.__reversed__()

    def __contains__(self, item: Track) -> bool:
        """Check if an item is a member of the queue."""
        return item in self._queue

    def __add__(self, other: Iterable[Track]) -> Queue:
        """Return a new queue containing all members.
        The new queue will have the same max_size as the original.
        """
        if not isinstance(other, Iterable):
            raise TypeError(
                f"Adding with the '{type(other)}' type is not supported.",
            )

        new_queue = self.copy()
        new_queue.extend(other)
        return new_queue

    def __iadd__(self, other: Iterable[Track] | Track) -> Self:
        """Add items to queue."""
        if isinstance(other, Track):
            self.put(other)
            return self

        if isinstance(other, Iterable):
            self.extend(other)
            return self

        raise TypeError(
            f"Adding '{type(other)}' type to the queue is not supported.",
        )

    def _get(self) -> Track:
        return self._queue.pop(0)

    def _drop(self) -> Track:
        return self._queue.pop()

    def _index(self, item: Track) -> int:
        return self._queue.index(item)

    def _insert(self, index: int, item: Track) -> None:
        self._queue.insert(index, item)

    def _remove(self, item: Track) -> None:
        self._queue.remove(item)

    @staticmethod
    def _check_track(item: Track) -> Track:
        if not isinstance(item, Track):
            raise TypeError("Only lava_lyra.Track objects are supported.")

        return item

    @classmethod
    def _check_track_container(cls, iterable: Iterable[Track]) -> list[Track]:
        iterable = list(iterable)
        for item in iterable:
            cls._check_track(item)

        return iterable

    @property
    def is_empty(self) -> bool:
        """Returns True if queue has no members."""
        return not bool(self.size)

    @property
    def is_full(self) -> bool:
        """Returns True if queue item count has reached max_size."""
        return False if self.max_size is None else self.size >= self.max_size

    @property
    def is_looping(self) -> bool:
        """Returns True if the queue is looping either a track or the queue"""
        return bool(self._loop_mode)

    @property
    def loop_mode(self) -> LoopMode | None:
        """Returns the LoopMode enum set in the queue object"""
        return self._loop_mode

    @property
    def size(self) -> int:
        """Returns the amount of items in the queue"""
        return len(self._queue)

    def get_queue(self) -> list[Track]:
        """Returns the queue as a List"""
        return self._queue

    def get(self) -> Track:
        """Return next immediately available item in queue if any.
        Raises QueueEmpty if no items in queue.
        """

        if self._loop_mode == LoopMode.TRACK:
            if self._current_item is not None:
                return self._current_item

        if self.is_empty:
            raise QueueEmpty("No items in the queue.")

        if self._loop_mode == LoopMode.QUEUE:
            if not self._current_item or self._current_item not in self._queue:
                if not self._queue:
                    raise QueueEmpty("No items in the queue.")
                item = self._queue[0]

            # we reached the end of the queue, go back to first track
            elif self._index(self._current_item) == len(self._queue) - 1:
                item = self._queue[0]

            # we are in the middle of the queue, go the next item
            else:
                index = self._index(self._current_item) + 1
                item = self._queue[index]
        else:
            item = self._get()

        self._current_item = item
        return item

    def set_current(self, item: Track | None) -> None:
        """
        Manually set the queue's notion of the currently playing item.

        Needed when a track is played outside the normal `get()` flow
        (e.g. replaying a track pulled from an external history stack),
        so that loop-mode aware lookups like `peek_next()` stay in sync
        with what's actually playing instead of pointing at a stale item.
        """
        if item is not None:
            self._check_track(item)
        self._current_item = item

    def peek_next(self) -> Track:
        """Return whatever `get()` would return next, WITHOUT mutating
        queue/loop state (does not pop, does not advance `_current_item`).

        This exists so callers can preload a gapless "next track" without
        also consuming/advancing the queue's position - which is what `get()`
        does. Calling `get()` for a preload and then calling it again once
        the track actually starts (to "sync" state) double-advances the
        queue under LoopMode.QUEUE, silently skipping tracks.

        Raises QueueEmpty if there is nothing to play next.
        """
        if self._loop_mode == LoopMode.TRACK:
            if self._current_item is not None:
                return self._current_item

        if self.is_empty:
            raise QueueEmpty("No items in the queue.")

        if self._loop_mode == LoopMode.QUEUE:
            if not self._current_item or self._current_item not in self._queue:
                if not self._queue:
                    raise QueueEmpty("No items in the queue.")
                return self._queue[0]

            # we reached the end of the queue, next up is the first track
            if self._index(self._current_item) == len(self._queue) - 1:
                return self._queue[0]

            # we are in the middle of the queue, next up is the next item
            index = self._index(self._current_item) + 1
            return self._queue[index]

        return self._queue[0]

    def pop(self, index: int = -1) -> Track:
        """Remove and return item at index (default last item).
        Raises QueueEmpty if no items in queue.
        Raises IndexError if index is out of range.
        """
        if self.is_empty:
            raise QueueEmpty("No items in the queue.")

        return self._queue.pop(index)

    def remove(self, item: Track) -> None:
        """
        Removes a item within the queue.
        Raises ValueError if item is not in queue.
        """
        return self._remove(self._check_track(item))

    def find_position(self, item: Track) -> int:
        """Find the position a given item within the queue.
        Raises ValueError if item is not in queue.
        """
        return self._index(self._check_track(item))

    def put(self, item: list[Track] | Track | Playlist, /) -> int:
        """Put the given item into the back of the queue."""
        added = 0

        if isinstance(item, Iterable):
            passing_items = self._check_track_container(item)
            if self.max_size is not None and self._overflow:
                while self._queue and self.size + len(passing_items) > self.max_size:
                    self._drop()
                if len(passing_items) > self.max_size:
                    passing_items = passing_items[: self.max_size]
            elif self.max_size is not None and not self._overflow:
                if self.size + len(passing_items) > self.max_size:
                    raise QueueFull(
                        f"Queue has {self.size}/{self.max_size} items, "
                        f"cannot add {len(passing_items)} more.",
                    )
            self._queue.extend(passing_items)
            added = len(passing_items)
        else:
            self._check_track(item)
            if self.is_full:
                if not self._overflow:
                    raise QueueFull(
                        f"Queue max_size of {self.max_size} has been reached.",
                    )
                if self._queue:
                    self._drop()
                elif self.max_size == 0:
                    return added
            self._queue.append(item)
            added = 1

        return added

    def put_at_index(self, index: int, item: Track) -> None:
        """Put the given item into the queue at the specified index."""
        self._check_track(item)
        if self.is_full:
            if not self._overflow:
                raise QueueFull(
                    f"Queue max_size of {self.max_size} has been reached.",
                )

            if self._queue:
                self._drop()
            elif self.max_size == 0:
                return

        return self._insert(index, item)

    def put_at_front(self, item: Track) -> None:
        """Put the given item into the front of the queue."""
        return self.put_at_index(0, item)

    def extend(self, iterable: Iterable[Track], *, atomic: bool = True) -> None:
        """
        Add the members of the given iterable to the end of the queue.
        If atomic is set to True, no tracks will be added upon any exceptions.
        If atomic is set to False, as many tracks will be added as possible.
        When overflow is enabled for the queue, `atomic=True` won't prevent dropped items.
        """
        if atomic:
            iterable = self._check_track_container(iterable)

            if not self._overflow and self.max_size is not None:
                new_len = len(iterable)

                if (new_len + self.size) > self.max_size:
                    raise QueueFull(
                        f"Queue has {self.size}/{self.max_size} items, cannot add {new_len} more.",
                    )

            if self._overflow and self.max_size is not None:
                self.put(list(iterable))
            else:
                for item in iterable:
                    self.put(item)
        else:
            for item in iterable:
                if not isinstance(item, Track):
                    continue
                if not self._overflow and self.max_size is not None and self.size >= self.max_size:
                    break
                self.put(item)

    def copy(self) -> Queue:
        """Create a copy of the current queue including its members."""
        new_queue = self.__class__(max_size=self.max_size)
        new_queue._queue = copy(self._queue)
        new_queue._overflow = self._overflow
        new_queue._loop_mode = self._loop_mode
        new_queue._current_item = self._current_item

        return new_queue

    def clear(self) -> None:
        """Remove all items from the queue."""
        self._queue.clear()

    def set_loop_mode(self, mode: LoopMode) -> None:
        """
        Sets the loop mode of the queue.
        Takes the LoopMode enum as an argument.

        Setting `LoopMode.QUEUE` re-inserts the current track into the queue if it
        isn't already a member, so it's included in the loop.
        """
        self._loop_mode = mode
        if self._loop_mode == LoopMode.QUEUE:
            if self._current_item is None:
                if not self._queue:
                    return
                self._current_item = self._queue[0]
                return
            try:
                index = self._index(self._current_item)
            except ValueError:
                index = 0
            if self._current_item not in self._queue:
                self._queue.insert(index, self._current_item)
            self._current_item = self._queue[index]

    def disable_loop(self) -> None:
        """
        Disables loop mode if set.
        Raises QueueException if loop mode is already None.
        """
        if not self._loop_mode:
            raise QueueException("Queue loop is already disabled.")

        if self._loop_mode == LoopMode.QUEUE:
            if self._current_item is None:
                self._loop_mode = None
                return
            try:
                index = self.find_position(self._current_item) + 1
            except (ValueError, TypeError):
                index = 0
            if index < len(self._queue):
                self._queue = self._queue[index:]

        self._loop_mode = None

    def shuffle(self) -> None:
        """Shuffles the queue."""
        return random.shuffle(self._queue)

    def clear_track_filters(self) -> None:
        """Clears all filters applied to tracks"""
        for track in self._queue:
            track.filters = None

    def jump(self, item: Track) -> None:
        """
        Jumps to the item specified in the queue.

        Raises QueueException if the loop mode is LoopMode.TRACK. If the loop
        mode is LoopMode.QUEUE, the current item is adjusted to the item
        before the specified track. Otherwise, the queue itself is mutated
        so that the next item retrieved is the track that is specified,
        effectively 'jumping' the queue.
        """

        if self._loop_mode == LoopMode.TRACK:
            raise QueueException("Jumping the queue whilst looping a track is not allowed.")

        try:
            index = self.find_position(item)
        except ValueError as e:
            raise QueueException(f"Cannot jump to '{item}': item is not in the queue.") from e
        if self._loop_mode == LoopMode.QUEUE:
            self._current_item = self._queue[index - 1]
        else:
            new_queue = self._queue[index : self.size]
            self._queue = new_queue
