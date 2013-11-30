import collections as c
import importlib as il
import os

from protobuf.impl import demo_pb2 as pb_d
from skadi.state.util import Snapshot


def preroll(io_demo, tick):
    """
    Read from a DemoIO (skadi.io.demo) up to the listed tick, gathering first
    all entries of type CDemoFullPacket (protobuf.impl.demo_pb2). After the
    last full packet, gather all entries of type CDemoPacket
    (protobuf.impl.demo_pb2).

    An entry is simply a (peek, message) tuple yielded by DemoIO iteration.

    Arguments:
    io_demo -- DemoIO over which to iterate (peek, message) entries
    tick -- tick (in replay time, not game time) to read up to

    Returns a tuple containing two entry lists: full packets, then packets.

    """
    entries = scan_until(io_demo, tick)

    full_packets = []
    packets = []

    for entry in entries:
        peek, _ = entry
        if peek.kind is pb_d.DEM_FullPacket:
            full_packets.append(entry)
            packets = []
        elif peek.kind is pb_d.DEM_Packet:
            packets.append(entry)

    return full_packets, packets


def play(io_demo, match):
    """
    Iterates over the provided DemoIO (skadi.io.demo), updating the provided
    Match (skadi.state.match) with data from each CDemoPacket
    (protobuf.impl.demo_pb2) entry. This update behavior is encapsulated in
    the Match object.

    Yields the Match snapshots (a python deque collection) at each tick. A
    Snapshot (skadi.state.util) is a python namedtuple with world state
    accessible by named attributes.

    Full packet entries encountered during iteration are skipped.

    Arguments:
    io_demo -- DemoIO over which to iterate (peek, message) entries
    match -- Match instance to update at each tick

    """
    for peek, message in io_demo:
        if peek.kind == pb_d.DEM_FullPacket:
            continue
        elif peek.kind != pb_d.DEM_Packet:
            assert peek.kind == pb_d.DEM_Stop
            break

        pb = pb_d.CDemoPacket()
        pb.ParseFromString(message)
        match.snapshot(peek.tick, pb.data)

        yield match.snapshots


def scan_kind(io_demo, kind):
    """
    Searches DemoIO (skadi.io.demo) for first (peek, message) matching kind.

    Arguments:
    io_demo -- DemoIO over which to iterate (peek, message) entries
    kind -- int from EDemoCommands (protobuf.def.demo_pb2) specifying kind

    Returns a (peek, message) tuple, or (None, None) if no match found.

    """
    gen = ((p, m) for p, m in io_demo if p.kind == kind)

    try:
        peek, message = next(gen)
    except StopIteration:
        return None, None

    return peek, message


def scan_tick(io_demo, tick):
    """
    Searches DemoIO (skadi.io.demo) for first (peek, message) matching tick.

    Arguments:
    io_demo -- DemoIO over which to iterate (peek, message) entries
    tick -- int tick value

    Returns a (peek, message) tuple, or (None, None) if no match found.

    """
    gen = ((p, m) for p, m in io_demo if p.tick >= tick)

    try:
        peek, message = next(gen)
    except StopIteration:
        return None, None

    return peek, message


def scan_since(io_demo, epoch, fn_eligible=None, fn_complete=None):
    """
    Searches DemoIO (skadi.io.demo) for all (peek, message) entries "since"
    epoch (a tick). Allows a lambda eligibility test, and a lambda completion
    test.

    Note: This method depends on the underlying IO object's state.

    Arguments:
    io_demo -- DemoIO over which to iterate (peek, message) entries
    epoch -- int tick value to scan "since" (everything prior ignored)
    fn_eligible -- lambda with one argument testing if current entry valid
    fn_complete -- lambda with one argument allowing short-circuit of search

    Returns list of entries "since" epoch passing "eligible" test, and only
    until "complete" test returns True.

    """
    gen = ((p, m) for p, m in io_demo if p.tick >= tick)
    def fn_timely(entry):
        peek, _ = entry
        return peek.tick >= epoch

    return scan_timely(io_demo, fn_timely, fn_eligible, fn_complete)


def scan_until(io_demo, epoch, fn_eligible=None):
    """
    Searches DemoIO (skadi.io.demo) for all (peek, message) entries from
    current position while peek.tick < epoch. Allows a lambda eligibility
    test.

    Note: This method depends on the underlying IO object's state.

    Arguments:
    io_demo -- DemoIO over which to iterate (peek, message) entries
    epoch -- int tick value to scan "since" (everything prior ignored)
    fn_eligible -- lambda with one argument testing if current entry valid

    Returns a list of entries "until" epoch which also pass "eligible" test.

    """
    def fn_timely(entry):
        peek, _ = entry
        return peek.tick <= epoch

    def fn_complete(entry):
        peek, _ = entry
        return peek.tick >= epoch

    return scan_timely(io_demo, fn_timely, fn_eligible, fn_complete)


def scan_between(io_demo, since, until, fn_eligible=None):
    """
    Searches DemoIO (skadi.io.demo) for all (peek, message) entries from
    current position where since < peek.tick < until. Also allows a lambda
    eligibility test.

    Note: This method depends on the underlying IO object's state.

    Arguments:
    io_demo -- DemoIO over which to iterate (peek, message) entries
    epoch -- int tick value to scan "since" (everything prior ignored)
    fn_eligible -- lambda with one argument testing if current entry valid

    Returns all entries where since < peek.tick < until which also pass
    "eligible" test.

    """
    def fn_timely(entry):
        peek, _ = entry
        return since <= peek.tick <= until

    def fn_complete(entry):
        peek, _ = entry
        return peek.tick >= until

    return scan_timely(io_demo, fn_timely, fn_eligible, fn_complete)


def scan_timely(io_demo, fn_timely, fn_eligible, fn_complete):
    """
    Searches DemoIO (skadi.io.demo) for all (peek, message) entries from
    current position while the three functions return correct values.

    Note: This method depends on the underlying IO object's state.

    Arguments:
    io_demo -- DemoIO over which to iterate (peek, message) entries
    epoch -- int tick value to scan "since" (everything prior ignored)
    fn_timely -- lambda with one argument testing if current entry "timely"
    fn_eligible -- lambda with one argument testing if current entry valid
    fn_complete -- lambda with one argument allowing short-circuit of search

    Returns all entries where fn_timely is True, fn_eligible is True, and
    fn_complete is False.

    """
    matches = []
    complete = False

    while not complete:
        try:
            entry = io_demo.read()
        except EOFError:
            return matches

        timely = fn_timely(entry)
        eligible = fn_eligible(entry) if fn_eligible else True

        if timely and eligible:
            matches.append(entry)

        complete = fn_complete(entry) if fn_complete else False

    return matches
