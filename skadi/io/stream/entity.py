from skadi.io.stream import generic as io_strm_gnrc
from skadi.state.util import PVS


def mk(*args):
    """
    Pass-through for EntityStream instantiation.

    """
    return EntityStream(*args)


class EntityStream(io_strm_gnrc.Stream):
    """
    Implements methods for accessing an entity-specific stream of data.

    Typically, this data occurs in the 'entity_data' field of a
    CSVCMsg_PacketEntities (protobuf.impl.netmessages_pb2) protobuf message,
    which is itself found the 'data' field of a top-level CDemoPacket
    (protobuf.impl.demo_pb2) protobuf message.

    It also occures in the 'instancebaseline' string table, where it specifies
    the state for a newly created instance of a given DT.

    For metadata about the next entity in the stream, classes will call these
    three methods in sequence:

        1. read_entity_index
        2. read_entity_pvs
        3. read_entity_prop_list

    All of these methods read the stream enough to extract required data. In
    Skadi, the 'prop list' establishes an order of recv prop decoders to use
    on the same stream immediately after the prop list is read.

    The recv prop decoders read the state from the stream based on the prop 
    list. See DTDecoder (skadi.decoder.dt) for details.

    """

    def __init__(self, *args):
        super(EntityStream, self).__init__(*args)

    def read_entity_index(self, base_index):
        """
        Read just enough from the stream to establish the index for the entity
        being processed.

        Arguments:
        base_index -- an integer indicating the current working index

        Returns an integer index used for the next call to this method.

        """
        encoded_index = self.read_numeric_bits(6)

        if encoded_index & 0x30:
            # no idea how this actually works, but it does
            a = (encoded_index >> 4) & 3
            b = 16 if a == 3 else 0
            i = self.read_numeric_bits(4 * a + b) << 4
            encoded_index = i | (encoded_index & 0x0f)

        return base_index + encoded_index + 1

    def read_entity_pvs(self):
        """
        Read just enough to determine the PVS for the entity being processed.

        "PVS" is a Source Engine concept for "potentially visible set." It
        indicates whether an entity might be visible in game to a particular
        user, perspective notwithstanding. Not sure what PVS means in Dota 2
        spectator context, since you can see "everything" in game.

        Returns a PVS value (skadi.state.util).

        """
        hi = self.read_numeric_bits(1)
        lo = self.read_numeric_bits(1)

        if lo and not hi:
            pvs = PVS.Enter
        elif not (hi or lo):
            pvs = PVS.Preserve
        elif hi:
            pvs = PVS.Leave
            pvs = pvs | PVS.Delete if lo else pvs

        return pvs

    def read_entity_prop_list(self):
        """
        Read just enough from the stream to determine the prop list for the
        entity being processed.

        Returns a list of int indexes corresponding to recv prop decoders.
        This list is used, in order, to find and use decoders to gather state
        for this entity. Most of this functionality is encapsulated in
        DTDecoder (skadi.decoder.dt).

        Returns a list of int recv prop indexes.

        """
        prop_list = []
        cursor = -1

        while True:
            if self.read_numeric_bits(1):
                cursor += 1
            else:
                offset = self.read_varint()
                if offset == 0x3fff:
                    return prop_list
                else:
                    cursor += offset + 1

            prop_list.append(cursor)
