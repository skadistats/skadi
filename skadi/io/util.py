import collections as c


# A Peek is just a dumb named tuple of an ordered list of descriptive state.
Peek = c.namedtuple('Peek', 'compressed, kind, tick, size')


class VarintTooLongError(RuntimeError):
    pass


VI_MAX_BYTES, VI_SHIFT = 5, 7
VI_MASK = (1 << 32) - 1


def read_varint(handle):
    """
    Given an object responding to .read(), reads a varint one byte at a time.

    Unfortunately, because of the quirks of generic (skadi.stream.generic) and
    entity (skadi.stream.entity) streams, this approach isn't compatible.

    This is used by DemoIO (skadi.io.demo) and EmbedIO (skadi.io.embed).

    Arguments:
    handle -- python io object

    Returns int value.

    """
    size, value, shift = 0, 0, 0

    while True:
        byte = handle.read(1)

        if len(byte) == 0:
            raise EOFError()

        size += 1
        value |= (ord(byte) & 0x7f) << shift
        shift += VI_SHIFT

        if not (ord(byte) & 0x80):
            return value & VI_MASK

        if shift >= VI_SHIFT * VI_MAX_BYTES:
            raise VarintTooLongError()
