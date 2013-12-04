import collections as c
import importlib as il
import os

__impl__ = 'skadi_ext' if os.environ.get('SKADI_EXT') else 'skadi'
dcdr_pcktntts = il.import_module(__impl__ + '.decoder.packet_entities')
dcdr_strngtbl = il.import_module(__impl__ + '.decoder.string_table')
ndx_gnrc = il.import_module(__impl__ + '.index.generic')
io_strm_gnrc = il.import_module(__impl__ + '.io.stream.generic')
stt_rcvtbl = il.import_module(__impl__ + '.state.recv_table')
stt_sndtbl = il.import_module(__impl__ + '.state.send_table')

from skadi.index.embed import dem_signon_packet as ndx_mbd_dmsgnnpckt
from skadi.index.embed import dem_send_tables as ndx_mbd_sndtbls
from skadi.io import embed as io_mbd
from protobuf.impl import demo_pb2 as pb_d
from protobuf.impl import netmessages_pb2 as pb_n
from skadi.state import send_table as stt_sndtbl
from skadi.state.collection import recv_tables as stt_cllctn_rcvtbls
from skadi.state.collection import string_tables as stt_cllctn_strngtbls
from skadi.state.util import GameEvent


def parse(io_demo):
    """
    Process a specialized 'demo' IO wrapper into a PrologueIndex.

    Don't forget to bootstrap() the IO first, since there are 16 bytes of
    non-protobuf header data at the beginning of a demo file. Your use case
    may vary, so this method does not bootstrap.

    Arguments:
    io_demo -- DemoIO (skadi.io.demo) wrapping a file stream

    """
    entries = []
    iter_io = iter(io_demo)

    peek, message = next(iter_io)
    while peek.kind is not pb_d.DEM_SyncTick:
        entries.append((peek, message))
        peek, message = next(iter_io)

    return PrologueIndex(entries)


class PrologueIndex(ndx_gnrc.Index):
    """
    This index is concerned with top-level 'dem' messages encountered before
    CDemoSyncTick (protobuf.impl.demo_pb2). Unlike other indexes, it translates
    these messages into useful domain objects like send tables, recv tables,
    game events, and decoders. These objects are useful in processing actual
    replay data.

    """

    def __init__(self, entries):
        """
        Initialize instance of index.

        Argument:
        entries -- list of (peek, message) to index

        """
        super(PrologueIndex, self).__init__(entries)

        self._cls_by_dt = None
        self._game_event_by_id = None
        self._game_event_by_name = None
        self._packet_entities_decoder = None
        self._recv_tables = None
        self._send_table_by_dt = None
        self._string_table_decoder_by_name = None
        self._string_tables = None
        self.__game_event_list = None
        self.__signon_packet_index = None

    @property
    def cls_by_dt(self):
        """
        Dictionary relating source engine data type ("DT") to integer value.

        Lazily creates and/or returns dict with (dt, cls) items.

        """
        if not self._cls_by_dt:
            p, m = self._dem_class_info

            pb = pb_d.CDemoClassInfo()
            pb.ParseFromString(m)

            self._cls_by_dt = \
              {i.table_name:int(i.class_id) for i in pb.classes}

        return self._cls_by_dt

    @property
    def game_event_by_id(self):
        """
        Dictionary relating integer value to GameEvent (skadi.state.util).

        Lazily creates and/or returns dict with (int, GameEvent) items.

        """
        if not self._game_event_by_id:
            game_event_by_id = dict()

            for desc in self._game_event_list.descriptors:
                _id, name = desc.eventid, desc.name
                keys = [(k.type, k.name) for k in desc.keys]
                game_event_by_id[_id] = GameEvent(_id, name, keys)

            self._game_event_by_id = game_event_by_id

        return self._game_event_by_id

    @property
    def game_event_by_name(self):
        """
        Dictionary relating string value to GameEvent (skadi.state.util).

        Lazily creates and/or returns dict with (str, GameEvent) items.

        """
        if not self._game_event_by_name:
            game_event_by_name = dict()

            for desc in self._game_event_list.descriptors:
                _id, name = desc.eventid, desc.name
                keys = [(k.type, k.name) for k in desc.keys]
                game_event_by_name[name] = GameEvent(_id, name, keys)

            self._game_event_by_name = game_event_by_name

        return self._game_event_by_name

    @property
    def packet_entities_decoder(self):
        """
        To read a CSVCMsg_PacketEntities message's 'entity_data,' we need
        this. Packet entities decoder maintains a dict of DTDecoder by cls.
        Just one instance (i.e. this one) is capable of decoding everything
        in CSVCMsg_PacketEntities read during the match part of the replay.

        Lazily creates and/or returns a PacketEntitiesDecoder
        (skadi.decoder.packet_entities).

        """
        if not self._packet_entities_decoder:
            rtbc = self.recv_tables.by_cls
            self._packet_entities_decoder = dcdr_pcktntts.mk(rtbc)

        return self._packet_entities_decoder

    @property
    def recv_tables(self):
        """
        RecvTablesCollection (skadi.state.collection.recv_tables)
        encapsulating a set of this replay's recv tables.

        Notably, this method flattens send tables to produce its result.
        It can take around 1 second to complete.

        Lazily creates and/or returns RecvTablesCollection instance.

        """
        if not self._recv_tables:
            recv_table_by_cls = dict()

            for dt, send_table in self.send_table_by_dt.items():
                if not send_table.needs_flattening:
                    continue
                cls = self.cls_by_dt[dt]
                send_table_by_dt = self.send_table_by_dt
                recv_props = stt_sndtbl.flatten(send_table_by_dt, send_table)
                recv_table_by_cls[cls] = stt_rcvtbl.mk(dt, recv_props)

            self._recv_tables = stt_cllctn_rcvtbls.mk(recv_table_by_cls)

        return self._recv_tables


    @property
    def send_table_by_dt(self):
        """
        Dictionary relating string value to SendTable
        (skadi.state.recv_table).

        This method processes CDemoSendTables (protobuf.impl.demo_pb2), which
        it finds using private index-like methods. It then processes 
        CSVCMsg_SendTable (protobuf.impl.netmessages_pb2) 'svc' messages
        embedded in the 'data' field into send tables, one each.

        Lazily creates and/or returns dict with (str, SendTable) items.

        """
        if not self._send_table_by_dt:
            p, m = self._dem_send_tables

            pb = pb_d.CDemoSendTables()
            pb.ParseFromString(m)
            io_embed = io_mbd.mk(pb.data)
            send_tables_index = ndx_mbd_sndtbls.mk(io_embed)

            send_table_by_dt = dict()

            for p, m in send_tables_index.all_svc_send_table:
                pb = pb_n.CSVCMsg_SendTable()
                pb.ParseFromString(m)
                send_table = stt_sndtbl.mk(pb)
                send_table_by_dt[send_table.name] = send_table

            self._send_table_by_dt = send_table_by_dt

        return self._send_table_by_dt

    @property
    def string_table_decoder_by_name(self):
        """
        Dictionary relating string value to StringTableDecoder
        (skadi.decoder.string_table).

        This method uses an amalgamate index from jammed-together data in
        'signon'-flavored CDemoPacket (protobuf.impl.demo_pb2) messages. From
        this index, it extracts CSVCMsg_CreateStringTable
        (protobuf.impl.netmessages_pb2) 'svc' messages and creates one decoder
        for each.

        Lazily creates and/or returns dict with (str, StringTableDecoder)
        items.

        """
        if not self._string_table_decoder_by_name:
            string_table_decoder_by_name = dict()

            spi = self._signon_packet_index
            for _, message in spi.all_svc_create_string_table:
                pb = pb_n.CSVCMsg_CreateStringTable()
                pb.ParseFromString(message)
                string_table_decoder_by_name[pb.name] = dcdr_strngtbl.mk(pb)

            self._string_table_decoder_by_name = string_table_decoder_by_name

        return self._string_table_decoder_by_name

    @property
    def string_tables(self):
        """
        StringTablesCollection (skadi.state.collection.string_tables)
        encapsulating a 'base set' of string tables. Necessary for creating
        initial world state.

        This method uses an amalgamate index from jammed-together data in
        'signon'-flavored CDemoPacket (protobuf.impl.demo_pb2) messages. From
        this index, it extracts CSVCMsg_CreateStringTable
        (protobuf.impl.netmessages_pb2) 'svc' messages and decodes each.

        Lazily creates and/or returns StringTablesCollection.

        """
        if not self._string_tables:
            string_list_by_name = c.OrderedDict()

            spi = self._signon_packet_index
            for _, message in spi.all_svc_create_string_table:
                pb = pb_n.CSVCMsg_CreateStringTable()
                pb.ParseFromString(message)
                decoder = self.string_table_decoder_by_name[pb.name]
                stream = io_strm_gnrc.mk(pb.string_data)
                string_list_by_name[pb.name] = \
                  decoder.decode(stream, pb.num_entries)

            self._string_tables = stt_cllctn_strngtbls.mk(string_list_by_name)

        return self._string_tables

    @property
    def _all_dem_signon_packet(self):
        """
        Returns list of (peek, message) for 'signon packet.'

        """
        return self.find_all_kind(pb_d.DEM_SignonPacket)

    @property
    def _dem_class_info(self):
        """
        Returns (peek, message) for 'class info.'

        """
        return self.find_kind(pb_d.DEM_ClassInfo)

    @property
    def _dem_file_header(self):
        """
        Returns (peek, message) for 'file header.'

        """
        return self.find_kind(pb_d.DEM_FileHeader)

    @property
    def _dem_send_tables(self):
        """
        Returns (peek, message) for 'send tables.'

        """
        return self.find_kind(pb_d.DEM_SendTables)

    @property
    def _game_event_list(self):
        """
        Private accessor for pure CSVCMsg_GameEventList protobuf message.

        This method uses an amalgamate index from jammed-together data in
        'signon'-flavored CDemoPacket (protobuf.impl.demo_pb2) messages. From
        this index, it extracts a CSVCMsg_GameEventList
        (protobuf.impl.netmessages_pb2) 'svc' message.

        Lazily creates and/or returns CSVCMsg_GameEventList.

        """
        if not self.__game_event_list:
            p, m = self._signon_packet_index.svc_game_event_list
            pb = pb_n.CSVCMsg_GameEventList()
            pb.ParseFromString(m)
            self.__game_event_list = pb

        return self.__game_event_list

    @property
    def _signon_packet_index(self):
        """
        Because I'm lazy, I didn't want to repeatedly search all signon
        packets to find which one contains 'create string tables' messages, or
        which one has the 'game event list.' So I grab all of their data, jam
        it together, and index all the signon packets' messages in aggregate
        using an Index (skadi.index.generic).

        Lazily creates and/or returns Index.

        """
        if not self.__signon_packet_index:
            signon_packets = list(self._all_dem_signon_packet)

            pb_sp = []
            for p, m in signon_packets:
                pb = pb_d.CDemoPacket()
                pb.ParseFromString(m)
                pb_sp.append(pb)

            data = ''.join([pb.data for pb in pb_sp])
            io_embed = io_mbd.mk(data)
            self.__signon_packet_index = ndx_mbd_dmsgnnpckt.mk(io_embed)

        return self.__signon_packet_index
