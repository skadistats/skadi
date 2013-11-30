import importlib as il
import os

__impl__ = 'skadi_ext' if os.environ.get('SKADI_EXT') else 'skadi'
dcdr_dt = il.import_module(__impl__ + '.decoder.dt')

from skadi.state.util import Entity, PVS


def mk(*args):
    """
    Pass-through for PacketEntitiesDecoder instantiation.

    """
    return PacketEntitiesDecoder(*args)


class PacketEntitiesDecoder(object):
    """
    Instances of this class are responsible for decoding the 'entity_data'
    field found in CSVCMsg_PacketEntities protobuf messages. (These messages
    are embedded in 'data' fields of packet-like, top-level demo messages.)

    """

    def __init__(self, recv_table_by_cls):
        self.recv_table_by_cls = recv_table_by_cls
        self.class_bits = len(recv_table_by_cls).bit_length()
        self.decoders = dict()

    def __getitem__(self, cls):
        """
        Fetch DT decoder for provided cls. Create one if it doesn't exist.

        Arguments:
        cls -- an unique integer corresponding to a DT

        Returns a DTDecoder (skadi.decoder.dt).

        """
        if cls in self.decoders:
            return self.decoders[cls]

        decoder = dcdr_dt.mk(self.recv_table_by_cls[cls])
        self.decoders[cls] = decoder

        return decoder

    def decode(self, stream, is_delta, count, world):
        """
        This method should be called upon encountering
        CSVCMsg_PacketEntities protobuf messages.

        Arguments:
        stream -- a Stream (skadi.decoder.stream) wrapping 'entity_data'
        is_delta -- boolean indicates whether deletions read at very end
        count -- number of entities to be decoded
        world -- the World (skadi.state.world), required for PVS.Preserve

        Returns a patch, or list of (pvs, entity) tuples.

        """
        index = -1
        patch = []

        while len(patch) < count:
            pvs, entry = self._decode_diff(stream, index, world)
            index = entry.ind
            patch.append((pvs, entry))

        if is_delta:
            patch += self._decode_deletion_diffs(stream)

        return patch

    def _decode_diff(self, stream, index, entities):
        """
        Read one diff--a (pvs, entity) tuple--from the stream.

        Arguments:
        stream -- a Stream (skadi.decoder.stream) wrapping 'entity_data'
        index -- the current working index, used to calculate next index
        entities -- EntitiesCollection (skadi.state.collection.entities)

        Returns a diff, or (pvs, entity) tuple.

        """
        index = stream.read_entity_index(index)
        pvs = stream.read_entity_pvs()

        if pvs == PVS.Enter:
            cls = stream.read_numeric_bits(self.class_bits)
            serial = stream.read_numeric_bits(10)
            prop_list = stream.read_entity_prop_list()
            state = self[cls].decode(stream, prop_list)
        elif pvs == PVS.Preserve:
            _, entity = entities.entry_by_index[index]
            cls, serial = entity.cls, entity.serial
            prop_list = stream.read_entity_prop_list()
            state = self[cls].decode(stream, prop_list)
        elif pvs in (PVS.Leave, PVS.Delete):
            serial, cls, state = None, None, dict()


        return pvs, Entity(index, serial, cls, state)

    def _decode_deletion_diffs(self, stream):
        """
        CSVCMsg_PacketEntities protobuf messages marked 'is_delta' have an
        optimized list of deletions at the end of their 'entity_data' stream.
        This method decodes those patches.

        Arguments:
        stream -- a Stream (skadi.decoder.stream) wrapping 'entity_data'

        Returns a list of deleted patch, or (PVS.Delete, entity) tuples.

        """
        deletions = []

        while stream.read_numeric_bits(1):
            index = stream.read_numeric_bits(11) # max is 2^11-1, or 2047
            deletions.append((PVS.Delete, Entity(index, None, None, None)))

        return deletions
