# Use the Queue class

Lyra has an optional queue system that works seamlessly with the library. This queue system introduce quality-of-life features that every music application should ideally have like queue shuffling, queue jumping, and looping.


To use the queue system with Lyra, you must first subclass the `Player` class within your application like so:

```py
from lava_lyra import Player


class CustomPlayer(Player): ...
```

After you have initialized your subclass, you can add a `queue` variable to your class so you can access your queue when you initialize your player:

```py
from lava_lyra import Player, Queue


class CustomPlayer(Player):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.queue = Queue()
```

`Queue()` accepts two optional keyword arguments:

- `max_size` (`int | None`) — caps the number of tracks the queue can hold. `None` (default) means unlimited.
- `overflow` (`bool`) — when `max_size` is set and the queue is full: if `True` (default), the most recently queued track is dropped to make room; if `False`, `QueueFull` is raised instead.

```py
self.queue = Queue(max_size=100, overflow=False)
```

There are also properties the `Queue` class has to access certain values:

:::{list-table}
:header-rows: 1

* - Property
  - Type
  - Description

* - `Queue.size`
  - `int`
  - Returns the amount of items in the queue.

* - `Queue.is_empty`
  - `bool`
  - Returns `True` if the queue has no members.

* - `Queue.is_full`
  - `bool`
  - Returns `True` if the queue's item count has reached `max_size`.

* - `Queue.is_looping`
  - `bool`
  - Returns `True` if the queue is looping either a track or the whole queue.

* - `Queue.loop_mode`
  - `Optional[LoopMode]`
  - Returns the `LoopMode` enum currently set on the queue, or `None` if looping is disabled.

:::

## Adding a song to the queue

To add a song to the queue, we must use `Queue.put()`

```py
Queue.put()
```

After you have initialized your function, we need to pass the item positionally — `put()` doesn't accept `item` as a keyword argument. It accepts a single `Track`, a `list[Track]`, or a `Playlist`, and returns the number of tracks added:

```py

Queue.put(<your Track, list[Track], or Playlist here>)

```

After running the function, your track should be in the queue.

### Adding a song to a specific position

If you want to insert a track at a specific position instead of the end of the queue, use
`Queue.put_at_index()`

```py
Queue.put_at_index(...)
```

After you have initialized your function, we need to include the `index` and `item` parameters:

```py

Queue.put_at_index(index=<your index here>, item=<your Track here>)

```

If you just want to insert a track at the very front of the queue (so it plays next), you can use
`Queue.put_at_front()` instead, which only needs the `item` parameter:

```py

Queue.put_at_front(item=<your Track here>)

```

:::{important}

`put()`, `put_at_index()`, and `put_at_front()` all raise `QueueFull` if the queue was
constructed with `overflow=False` and `max_size` has been reached. With overflow enabled
(the default), the most recently queued track (the back of the queue) is dropped instead —
not the oldest one — to make room for the new item. All three (along with `queue[index] = item`)
also raise `TypeError` if `item` isn't a `Track` instance.

:::

### Adding multiple tracks at once

To add several tracks to the end of the queue in one call (for example, all the tracks from a
search result), we must use `Queue.extend()`

```py
Queue.extend(...)
```

After you have initialized your function, we need to fill in the proper parameters:

:::{list-table}
:header-rows: 1

* - Name
  - Type
  - Description

* - `iterable`
  - `Iterable[Track]`
  - The tracks to add.

* - `atomic`
  - `bool`
  - If set to `True` and the queue was constructed with `overflow=False`, either every track is added or none are — if `max_size` would be exceeded, `QueueFull` is raised and nothing is added. If the queue allows overflow (the default), `atomic=True` still adds every track, dropping the most recently queued existing tracks (not the oldest) to make room instead of raising. If set to `False`, as many tracks are added as fit and the rest are silently dropped, with no exception raised. Default value is `True`.

:::

```py

Queue.extend(iterable=<your list of Tracks here>, atomic=<True/False>)

```

:::{important}

Even with `atomic=True`, if the queue was constructed with `overflow=True` (the default), items
can still be dropped to make room rather than raising `QueueFull`. There's no public accessor
for this setting — track what you passed to `Queue(overflow=...)` yourself.

:::

## Getting the raw queue

If you need the queue's members as a plain `list[Track]` — to iterate, filter, or pass to
something that expects a list — use `Queue.get_queue()`

```py
Queue.get_queue()
```

:::{important}

This returns the queue's internal list directly, not a copy — mutating it (e.g. `.append()`,
`.sort()`) mutates the queue itself. Use `Queue.copy().get_queue()` first if you need an
independent list.

:::

## Getting a track from the queue

To get a track from the queue, we need to do a few things.

To get a track using its position within the queue, you first need to get the position as a number, also known as its index. If you dont have the index and instead want to search for its index using keywords, you have to implement a fuzzy searching algorithm to find said track using a search query as an input and have it compare that query against the titles of the tracks in the queue. After that, you can get the `Track` object by [getting it with its index](queue.md#getting-track-with-its-index)

### Getting index of track

If you have the `Track` object and want to get its index within the queue, we can use `Queue.find_position()`

```py
Queue.find_position()
```

After you have initialized your function, we need to include the `item` parameter, which is a `Track`:

```py

Queue.find_position(item=<your Track here>)

```

After running the function, it should return the position of the track as an integer.

:::{important}

Raises `ValueError` if the item is not in the queue.

:::


### Getting track with its index

If you have the index of the track and want to get the `Track` object, you can index directly into the `Queue` object itself — you don't need to call `Queue.get_queue()` first:

```py

track = queue[<index>]

```

Slicing works too (`queue[start:end]`), returning a `list[Track]`.

### Other operators

`Queue` also implements the standard container dunders:

:::{list-table}
:header-rows: 1

* - Method
  - Behavior

* - `len(queue)`
  - Same as `Queue.size`.

* - `bool(queue)`
  - `False` if empty.

* - `track in queue`
  - Membership check.

* - `for track in queue`
  - Front to back.

* - `reversed(queue)`
  - Back to front.

* - `str(queue)`
  - Renders the queue's current contents.

* - `queue[index] = track`, `del queue[index]`
  - Set/delete by index.

* - `queue(track)`
  - Shorthand for `Queue.put(track)`.

* - `queue += track` / `queue += iterable`
  - Shorthand for `Queue.put(track)` or `Queue.extend(iterable)`.

* - `queue + iterable`
  - New `Queue` with the original members plus `iterable`. If `max_size` would be exceeded,
    original members are dropped to make room the same way `Queue.extend()` does. Doesn't
    mutate the original.

* - `repr(queue)`
  - Debug string with `max_size` and member count.

:::


## Getting the next track in the queue

To get the next track in the queue, we need to use `Queue.get()`

```py
Queue.get()
```

After running this function, it'll return the next track to play and, if the queue isn't
looping, remove it from the queue.

:::{note}

If you have a queue loop mode set, tracks are never removed from the queue: `LoopMode.TRACK`
keeps returning the current track, and `LoopMode.QUEUE` advances through the queue without
popping from it.

:::

Raises `QueueEmpty` if there are no items in the queue — except under `LoopMode.TRACK` once a
current track has been set, which keeps returning that track even after the queue itself has
been emptied.

### Peeking at the next track

If you want to know what `Queue.get()` would return next, without actually removing it from the
queue or advancing the loop state, use `Queue.peek_next()`

```py
Queue.peek_next()
```

This is useful for preloading a gapless "next track" ahead of time. Calling `Queue.get()` twice
for this purpose would double-advance the queue under `LoopMode.QUEUE`, silently skipping tracks —
`Queue.peek_next()` avoids that.

:::{important}

Same `QueueEmpty` behavior as `Queue.get()` above.

:::

### Popping a track from the queue

To remove and return a track at a specific index (default: the last item), use `Queue.pop()`

```py
Queue.pop(...)
```

```py

Queue.pop(index=<your index here>)

```

:::{important}

Raises `QueueEmpty` if there are no items in the queue, and `IndexError` if the index is out of range.

:::

## Removing a track from the queue


To remove a track from the queue, we must use `Queue.remove()`

```py
Queue.remove()
```

After you have initialized your function, we need to include the `item` parameter, which is a `Track`:

```py

Queue.remove(item=<your Track here>)

```

:::{important}

Your `Track` object must be in the queue if you want to remove it — raises `ValueError`
otherwise. Make sure you follow [](queue.md#getting-a-track-from-the-queue) before running this function.

:::

After running this function, your track should be removed from the queue.


## Shuffling the queue

To shuffle the queue, we must use `Queue.shuffle()`

```py
Queue.shuffle()
```

After running this function, your queue should be in a different order than it was originally.

:::{tip}

This function works best if theres atleast **3** tracks in the queue. The more tracks, the more variation the shuffle has.

:::


## Looping the queue

To loop the queue, we must use `Queue.set_loop_mode()`

```py
Queue.set_loop_mode(...)
```

After you have initialized your function, we need to include the `mode` parameter, which is a `LoopMode` enum:

```py

Queue.set_loop_mode(mode=LoopMode.<mode>)

```

The two types of `LoopMode` enums are `LoopMode.QUEUE` and `LoopMode.TRACK`. `QUEUE` loops the entire queue and `TRACK` loops the current track.

After running the function, your queue will now loop using the mode you specify.

### Resetting the loop mode

To reset the loop mode, we must use `Queue.disable_loop()`

```py
Queue.disable_loop()
```

:::{important}

Raises `QueueException` if you do not have a loop mode set.

:::

After running the function, your queue should return to its normal functionality. Under
`LoopMode.QUEUE`, this also drops every item before and including the current track — the
loop's earlier laps aren't kept.

## Jumping to a track in the queue

To jump to a track in the queue, we must use `Queue.jump()`


```py
Queue.jump(...)
```

After you have initialized your function, we need to include the `item` parameter, which is a `Track`:

```py

Queue.jump(item=<your Track here>)

```

:::{important}

Raises `QueueException` if the item is not in the queue, or if the queue is currently looping a
single track (`LoopMode.TRACK`).

:::

When no loop mode is set, items before the target are removed and `Queue.get()` returns it next.
Under `LoopMode.QUEUE`, nothing is removed — only the internal position pointer moves, so the
loop continues from there.

## Clearing the queue

To remove all items from the queue at once, we must use `Queue.clear()`

```py
Queue.clear()
```

After running this function, the queue will be empty. Unlike `Queue.disable_loop()`, this does not
change the current loop mode.

## Copying the queue

To create an independent copy of a queue, including its members, `overflow` flag, loop mode, and
current track, use `Queue.copy()` on the queue instance:

```py
new_queue = queue.copy()
```

This returns a new `Queue` instance — mutating the copy does not affect the original queue.

## Manually syncing the current track

`Queue.get()` normally keeps track of what's "currently playing" for you as you pull tracks from
the queue. If you play a track outside of that normal flow (for example, replaying a track pulled
from an external history stack), you can use `Queue.set_current()` to manually tell the queue
what's currently playing, so that loop-mode aware lookups like `Queue.peek_next()` stay in sync:

```py
Queue.set_current(...)
```

After you have initialized your function, we need to include the `item` parameter, which is a
`Track` (or `None` to clear it):

```py

Queue.set_current(item=<your Track here>)

```

## Clearing track filters

`Track` objects can carry their own per-track filters. To clear the filters set on every track
currently in the queue, use `Queue.clear_track_filters()`

```py
Queue.clear_track_filters()
```
