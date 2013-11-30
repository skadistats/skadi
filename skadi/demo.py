import collections as c
import importlib as il
import os

from protobuf.impl import demo_pb2 as pb_d
from skadi.state.util import Snapshot


def preroll(io_demo, tick):
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
    gen = ((p, m) for p, m in io_demo if p.kind == kind)

    try:
        peek, message = next(gen)
    except StopIteration:
        return None, None

    return peek, message


def scan_tick(io_demo, tick):
    gen = ((p, m) for p, m in io_demo if p.tick >= tick)

    try:
        peek, message = next(gen)
    except StopIteration:
        return None, None

    return peek, message


def scan_since(io_demo, epoch, fn_eligible=None, fn_complete=None):
    def fn_timely(entry):
        peek, _ = entry
        return peek.tick >= epoch

    return scan_timely(io_demo, fn_timely, fn_eligible, fn_complete)


def scan_until(io_demo, epoch, fn_eligible=None):
    def fn_timely(entry):
        peek, _ = entry
        return peek.tick <= epoch

    def fn_complete(entry):
        peek, _ = entry
        return peek.tick >= epoch

    return scan_timely(io_demo, fn_timely, fn_eligible, fn_complete)


def scan_between(io_demo, since, until, fn_eligible=None):
    def fn_timely(entry):
        peek, _ = entry
        return since <= peek.tick <= until

    def fn_complete(entry):
        peek, _ = entry
        return peek.tick >= until

    return scan_timely(io_demo, fn_timely, fn_eligible, fn_complete)


def scan_timely(io_demo, fn_timely, fn_eligible, fn_complete):
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
