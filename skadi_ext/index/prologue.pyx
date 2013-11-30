import collections as c

from skadi_ext.decoder cimport packet_entities as dcdr_pcktntts
from skadi_ext.decoder cimport string_table as dcdr_strngtbl
from skadi_ext.io.stream cimport generic as io_strm_gnrc
from skadi_ext.state cimport recv_table as stt_rcvtbl
from skadi_ext.state cimport send_table as stt_sndtbl
from skadi_ext.index.generic cimport Index

from skadi.index.embed import dem_signon_packet as ndx_mbd_dmsgnnpckt
from skadi.index.embed import dem_send_tables as ndx_mbd_sndtbls
from skadi.io import embed as io_mbd
from protobuf.impl import demo_pb2 as pb_d
from protobuf.impl import netmessages_pb2 as pb_n
from skadi.state import send_table as stt_sndtbl
from skadi.state.collection import string_tables as stt_cllctn_strngtbls
from skadi.state.util import GameEvent


cpdef PrologueIndex parse(object io_demo):
    cdef object entries = []
    cdef object iter_io = iter(io_demo)
    cdef object peek
    cdef object message

    peek, message = next(iter_io)
    while peek.kind is not pb_d.DEM_SyncTick:
        entries.append((peek, message))
        peek, message = next(iter_io)

    return PrologueIndex(entries)


cdef class PrologueIndex(Index):
    cdef object _cls_by_dt
    cdef object _game_event_by_id
    cdef object _game_event_by_name
    cdef object _packet_entities_decoder
    cdef object _recv_table_by_cls
    cdef object _send_table_by_dt
    cdef object _string_table_decoder_by_name
    cdef object _string_tables
    cdef object __game_event_list
    cdef object __signon_packet_index

    def __init__(self, entries):
        super(PrologueIndex, self).__init__(entries)

        self._cls_by_dt = None
        self._game_event_by_id = None
        self._game_event_by_name = None
        self._packet_entities_decoder = None
        self._recv_table_by_cls = None
        self._send_table_by_dt = None
        self._string_table_decoder_by_name = None
        self._string_tables = None
        self.__game_event_list = None
        self.__signon_packet_index = None

    property cls_by_dt:
        def __get__(self):
            if not self._cls_by_dt:
                p, m = self._dem_class_info

                pb = pb_d.CDemoClassInfo()
                pb.ParseFromString(m)

                self._cls_by_dt = \
                  {i.table_name:int(i.class_id) for i in pb.classes}

            return self._cls_by_dt

    property game_event_by_id:
        def __get__(self):
            if not self._game_event_by_id:
                game_event_by_id = dict()

                for desc in self._game_event_list.descriptors:
                    _id, name = desc.eventid, desc.name
                    keys = [(k.type, k.name) for k in desc.keys]
                    game_event_by_id[_id] = GameEvent(_id, name, keys)

                self._game_event_by_id = game_event_by_id

            return self._game_event_by_id

    property game_event_by_name:
        def __get__(self):
            if not self._game_event_by_name:
                game_event_by_name = dict()

                for desc in self._game_event_list.descriptors:
                    _id, name = desc.eventid, desc.name
                    keys = [(k.type, k.name) for k in desc.keys]
                    game_event_by_name[name] = GameEvent(_id, name, keys)

                self._game_event_by_name = game_event_by_name

            return self._game_event_by_name

    property packet_entities_decoder:
        def __get__(self):
            if not self._packet_entities_decoder:
                rtbc = self.recv_table_by_cls
                self._packet_entities_decoder = dcdr_pcktntts.mk(rtbc)

            return self._packet_entities_decoder

    property recv_table_by_cls:
        def __get__(self):
            if not self._recv_table_by_cls:
                recv_table_by_cls = dict()

                for dt, send_table in self.send_table_by_dt.items():
                    if not send_table.needs_flattening:
                        continue
                    cls = self.cls_by_dt[dt]
                    send_table_by_dt = self.send_table_by_dt
                    recv_props = stt_sndtbl.flatten(send_table_by_dt, send_table)
                    recv_table_by_cls[cls] = stt_rcvtbl.mk(dt, recv_props)

                self._recv_table_by_cls = recv_table_by_cls

            return self._recv_table_by_cls

    property send_table_by_dt:
        def __get__(self):
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

    property string_table_decoder_by_name:
        def __get__(self):
            if not self._string_table_decoder_by_name:
                string_table_decoder_by_name = dict()

                spi = self._signon_packet_index
                for _, message in spi.all_svc_create_string_table:
                    pb = pb_n.CSVCMsg_CreateStringTable()
                    pb.ParseFromString(message)
                    string_table_decoder_by_name[pb.name] = dcdr_strngtbl.mk(pb)

                self._string_table_decoder_by_name = string_table_decoder_by_name

            return self._string_table_decoder_by_name

    property string_tables:
        def __get__(self):
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

    property _all_dem_signon_packet:
        def __get__(self):
            return self.find_all_kind(pb_d.DEM_SignonPacket)

    property _dem_class_info:
        def __get__(self):
            return self.find_kind(pb_d.DEM_ClassInfo)

    property _dem_file_header:
        def __get__(self):
            return self.find_kind(pb_d.DEM_FileHeader)

    property _dem_send_tables:
        def __get__(self):
            return self.find_kind(pb_d.DEM_SendTables)

    property _game_event_list:
        def __get__(self):
            if not self.__game_event_list:
                p, m = self._signon_packet_index.svc_game_event_list
                pb = pb_n.CSVCMsg_GameEventList()
                pb.ParseFromString(m)
                self.__game_event_list = pb

            return self.__game_event_list

    property _signon_packet_index:
        def __get__(self):
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
