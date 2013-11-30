import struct


def mk(*args):
    """
    Pass-through for Stream instantiation.

    """
    return Stream(*args)


WORD_BYTES = 4
WORD_BITS = WORD_BYTES * 8


class Stream(object):
    def __init__(self, data):
        """
        Initialize instance to be used on provided data.

        Arguments:
        data -- string containing data this stream will operate on

        """
        pad_diff = len(data) % WORD_BYTES

        # expand data to 4 bytes, pad zero
        if pad_diff:
            data = data + '\0' * (WORD_BYTES - pad_diff)

        # [1,2,3,4,1,2,3,4] => [(1,2,3,4), (1,2,3,4)]
        groups = zip(*(iter(bytearray(data)),) * WORD_BYTES)

        # interpret tuple as unsigned LE
        def interpret(group):
            return sum(group[i] << (i * 8) for i in range(WORD_BYTES))

        self.words = [interpret(group) for group in groups]
        self.pos = 0

    def peek_numeric_bits(self, bitlength):
        """
        Peeks bitlength bits as an int without advancing position.

        Arguments:
        bitlength -- int count of bits to peek

        Returns int value.

        """

        assert bitlength <= WORD_BITS

        try:
          l = self.words[self.pos / WORD_BITS]
          r = self.words[(self.pos + bitlength - 1) / WORD_BITS]
        except IndexError:
          raise EOFError()

        pos_shift = self.pos & (WORD_BITS - 1)
        rebuild = r << (WORD_BITS - pos_shift) | l >> pos_shift

        return int(rebuild & ((1 << bitlength) - 1))

    def read_numeric_bits(self, bitlength):
        """
        Reads bitlength bits as an int, advancing position.

        Arguments:
        bitlength -- int count of bits to read

        Returns int value.

        """

        value = self.peek_numeric_bits(bitlength)
        self.pos += bitlength

        return value

    def read_bits(self, bitlength):
        """
        Reads bitlength bits as binary string of data, advancing position.

        Arguments:
        bitlength -- int count of bits to read

        Returns string of binary data.

        """

        remaining, _bytes = bitlength, []

        while remaining > 7:
          remaining -= 8
          _bytes.append(self.read_numeric_bits(8))
        if remaining:
          _bytes.append(self.read_numeric_bits(remaining))

        return str(bytearray(_bytes))

    def read_string(self, bytelength):
        """
        Reads bytelength bytes as string, advancing position. Terminates early
        on zero value, returning bytes accumulated up to that point.

        Arguments:
        bytelength -- int count of bytes to read

        Returns string of binary data.

        """

        remaining, _bytes = bytelength * 8, []

        while remaining > 7:
            byte = self.read_numeric_bits(8)
            if byte == 0:
                break

            _bytes.append(byte)
            remaining -= 8

        return str(bytearray(_bytes))

    def read_varint(self):
        """
        Reads a variable-length int, encoded like a protobuf varint.

        Returns int value.

        """
        run, value = 0, 0

        while True:
            bits = self.read_numeric_bits(8)
            value |= (bits & 0x7f) << run
            run += 7

            if not (bits >> 7) or run == 35:
                break

        return value
