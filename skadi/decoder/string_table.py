import collections as c
import math

from skadi.state.util import String


MAX_NAME_LENGTH = 0x400
KEY_HISTORY_SIZE = 32


def mk(pb):
    """
    Using a CSVCMsg_CreateStringTable message, construct a decoder. Notably,
    a Stream (skadi.io.stream) wrapping this message's 'string_data' field
    is later passed to decode() to get its String (skadi.state.util) data.
    This implementation separates decoder creation from data extraction.

    Arguments:
    pb -- CSVCMsg_CreateStringTable (protobuf.impl.netmessages_pb2)

    Returns an instance of StringTableDecoder.

    """
    me = pb.max_entries
    udfs = pb.user_data_fixed_size
    udsb = pb.user_data_size_bits

    return StringTableDecoder(me, udfs, udsb)


class StringTableDecoder(object):
    """
    Instances of this class are responsible for decoding the 'string_data'
    field found in CSVCMsg_CreateStringTable and CSVCMsg_UpdateStringTable
    protobuf messages. (These messages are both embedded in 'data' fields of
    packet-like, top-level demo messages.)

    Instances of this class are reusable: only one StringTableDecoder is
    instantiated for each CSVCMsg_CreateStringTable, and the same instance is
    used upon to decode later CSVCMsg_UpdateStringTable protobuf messages.

    """

    def __init__(self, max_entries, user_data_sz_fixed, user_data_sz_bits):
        """
        Initialize with properties from a CSVCMsg_CreateStringTable protobuf
        message.

        Arguments:
        max_entries -- integer, maximum theoretical size of string table
        user_data_sz_fixed -- boolean, True if entry data is fixed length
        user_data_sz_bits -- integer length of fixed entry data, in bits

        """
        # entry_sz_bits contains the minimum number of bits necessary to
        # represent an entry, i.e. log base 2 of the number of max entries.
        self.entry_sz_bits = int(math.ceil(math.log(max_entries, 2)))
        self.user_data_sz_fixed = user_data_sz_fixed
        self.user_data_sz_bits = user_data_sz_bits

    def decode(self, stream, num_entries):
        """
        This method should be called upon encountering both
        CSVCMsg_CreateStringTable and CSVCMsg_UpdateStringTable protobuf
        messages.

        Arguments:
        stream -- Stream (skadi.decoder.stream) wrapping 'string_data'
        num_entries -- number of string to process for this current message

        Returns a list of decoded String (skadi.state.util) from the stream.

        """
        # The meaning of this one-bit flag is unknown, but we can use it later
        # for sanity checks. It corresponds to unimplemented string table
        # functionality in combination with other bits parsed later.
        mystery_flag = stream.read_numeric_bits(1)
        key_history = c.deque()
        index = -1

        diff = []

        while len(diff) < num_entries:
            index = self._decode_index(stream, index)
            name = self._decode_name(stream, mystery_flag, key_history)
            value = self._decode_value(stream)
            diff.append(String(index, name, value))

        return diff

    def _decode_index(self, stream, index):
        """
        Derive the index of the current entry.

        Arguments:
        stream -- Stream (skadi.decoder.stream) wrapping 'string_data'
        index -- integer index functioning as a basis for return value

        Returns an integer for 'index' of a String (skadi.state.util).

        """
        # first bit indicates whether the index is consecutive
        if stream.read_numeric_bits(1):
            index += 1
        else:
            index = stream.read_numeric_bits(self.entry_sz_bits)

        return index

    def _decode_name(self, stream, mystery_flag, key_history):
        """
        Derive the name of the current entry. Can be None.

        Arguments:
        stream -- Stream (skadi.decoder.stream) wrapping 'string_data'
        mystery_flag -- 1, or 0, indicating unhandled functionality
        key_history -- deque for additively constructing strings

        Returns string for 'name' of a String (skadi.state.util).

        """
        name = None

        # first bit indicates whether the entry has a name
        if stream.read_numeric_bits(1):
            # no idea what these bits mean, but certain value combinations
            # indicate unimplemented string table functionality
            assert not (mystery_flag and stream.read_numeric_bits(1))

            # first bit indicates whether string name based on key history
            if stream.read_numeric_bits(1):
                basis = stream.read_numeric_bits(5)
                length = stream.read_numeric_bits(5)
                name = key_history[basis][0:length]
                name += stream.read_string(MAX_NAME_LENGTH - length)
            else:
                name = stream.read_string(MAX_NAME_LENGTH)

            if len(key_history) == KEY_HISTORY_SIZE:
                key_history.popleft()

            key_history.append(name)

        return name

    def _decode_value(self, stream):
        """
        Derive the value of the current entry. Can be empty string.

        Arguments:
        stream -- Stream (skadi.decoder.stream) wrapping 'string_data'

        Returns binary data string for 'value' of a String (skadi.state.util).

        """
        value = ''

        # first bit indicates whether the entry has a value
        if stream.read_numeric_bits(1):
            if self.user_data_sz_fixed:
                bit_length = self.user_data_sz_bits
            else:
                bit_length = stream.read_numeric_bits(14) * 8

            value = stream.read_bits(bit_length)

        return value
