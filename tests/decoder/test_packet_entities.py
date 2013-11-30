import glob
import importlib as il
import io
import os
import unittest

__impl__ = 'skadi_ext' if os.environ.get('SKADI_EXT') else 'skadi'
dcdr_pcktntts = il.import_module(__impl__ + '.decoder.packet_entities')
stt_cllctn_ntts = il.import_module(__impl__ + '.state.collection.entities')

from skadi.decoder import packet_entities as dcdr_pe
from skadi.io.stream import entity as io_strm_ent
from protobuf.impl import demo_pb2 as pb_d
from protobuf.impl import netmessages_pb2 as pb_n
from skadi.state import send_table as state_snd_tbl
from skadi.state import recv_table as state_rcv_tbl
from skadi.state.util import PVS


pwd = os.path.dirname(__file__)
FIX = os.path.abspath(os.path.join(pwd, '..', 'fixtures'))
CI_FIX = os.path.join(FIX, 'CDemoClassInfo')
ST_FIX_DIR = os.path.join(FIX, 'CSVCMsg_SendTable')
PE_FIX_DIR = os.path.join(FIX, 'CSVCMsg_PacketEntities')


class TestPacketEntities(unittest.TestCase):
    def test_fixtures_decode_without_error(self):
        # load class info, mapping cls integers to DTs
        pb = pb_d.CDemoClassInfo()
        with io.open(CI_FIX, 'rb') as infile:
            pb.ParseFromString(infile.read())

        cls_by_dt = {i.table_name:int(i.class_id) for i in pb.classes}
        send_table_by_dt = dict()
        recv_table_by_cls = dict()

        # load send tables
        for fixture in os.listdir(ST_FIX_DIR):
            path = os.path.join(ST_FIX_DIR, fixture)
            if not os.path.isfile(path):
                continue

            with io.open(path, 'rb') as infile:
                pb = pb_n.CSVCMsg_SendTable()
                pb.ParseFromString(infile.read())
                send_table = state_snd_tbl.mk(pb)
                send_table_by_dt[send_table.name] = send_table

        # flatten send tables, storing the resulting recv tables by cls
        for dt, send_table in send_table_by_dt.items():
            if not send_table.needs_flattening:
                continue

            cls = cls_by_dt[dt]
            recv_props = state_snd_tbl.flatten(send_table_by_dt, send_table)
            recv_table_by_cls[cls] = state_rcv_tbl.mk(dt, recv_props)

        # parse the tick 0 full packet
        path = os.path.join(PE_FIX_DIR, '00-full_packet')
        with io.open(path, 'rb') as infile:
            pb = pb_n.CSVCMsg_PacketEntities()
            pb.ParseFromString(infile.read())

        stream = io_strm_ent.mk(pb.entity_data)
        pe_dec = dcdr_pe.mk(recv_table_by_cls)
        entities = stt_cllctn_ntts.mk(dict(), recv_table_by_cls)
        pe_dec.decode(stream, pb.is_delta, pb.updated_entries, entities)

        _glob = glob.glob(os.path.join(PE_FIX_DIR, '??-packet'))
        for path in sorted(_glob):
            pass


if __name__ == '__main__':
    unittest.main()
