import collections as c
import importlib as il
import os

__impl__ = 'skadi_ext' if os.environ.get('SKADI_EXT') else 'skadi'
io_mbd = il.import_module(__impl__ + '.io.embed')
io_strm_gnrc = il.import_module(__impl__ + '.io.stream.generic')
io_strm_ntt = il.import_module(__impl__ + '.io.stream.entity')
ndx_mbd_dmpckt = il.import_module(__impl__ + '.index.embed.dem_packet')
stt_cllctn_ntts = il.import_module(__impl__ + '.state.collection.entities')

from protobuf.impl import demo_pb2 as pb_d
from protobuf.impl import dota_modifiers_pb2 as pb_dm
from protobuf.impl import dota_usermessages_pb2 as pb_dum
from protobuf.impl import netmessages_pb2 as pb_n
from protobuf.impl import networkbasetypes_pb2 as pb_nbt
from protobuf.impl import usermessages_pb2 as pb_um
from skadi.state import util as stt_utl
from skadi.state.collection import string_tables as stt_cllctn_strngtbls
from skadi.state.util import enum, Snapshot, UserMessageByKind


THRESHOLD = 64 # user messages less than this are 'common', else 'dota'


O = enum(slim = 0, game_events = 1 << 0, modifiers = 1 << 1,
    user_messages = 1 << 2)


def mk(prologue, full_packets, packets, window=None, o=None):
    full_packets = full_packets or []
    packets = packets or []
    window = window or 2

    st = prologue.string_tables

    if full_packets:
        for peek, message in full_packets:
            pb = pb_d.CDemoFullPacket()
            pb.ParseFromString(message)
            st = stt_cllctn_strngtbls.rebase(pb.string_table, basis=st)

    basis = Snapshot(0, stt_cllctn_ntts.mk(), st, c.defaultdict(dict), {}, {})

    if full_packets:
        peek, message = full_packets[-1]
        pb = pb_d.CDemoFullPacket()
        pb.ParseFromString(message)
        packet_data = pb.packet.data
    else:
        assert packets
        peek, message = packets[-1]
        pb = pb_d.CDemoPacket()
        pb.ParseFromString(message)
        packet_data = pb.data
        packets = packets[1:]

    match = Match(prologue, basis, window=window, o=o)
    match.snapshot(peek.tick, packet_data)

    for peek, message in packets:
        pb = pb_d.CDemoPacket()
        pb.ParseFromString(message)
        match.snapshot(peek.tick, pb.data)

    return match


def process_entities(basis, packet_entities_decoder, svc_packet_entities):
    _, message = svc_packet_entities
    pb = pb_n.CSVCMsg_PacketEntities()
    pb.ParseFromString(message)

    s = io_strm_ntt.mk(pb.entity_data)
    d, n = pb.is_delta, pb.updated_entries
    patch = packet_entities_decoder.decode(s, d, n, basis)

    return basis.apply(patch)


def diff_string_tables(basis, string_table_decoder_by_name,
        all_svc_update_string_table):
    patch_by_name = dict()

    for _, message in all_svc_update_string_table:
        pb = pb_n.CSVCMsg_UpdateStringTable()
        pb.ParseFromString(message)

        stream = io_strm_gnrc.mk(pb.string_data)
        name = basis.mapping[pb.table_id] # table_id index -> name str
        decoder = string_table_decoder_by_name[name]

        patch_by_name[name] = decoder.decode(stream, pb.num_changed_entries)

    return patch_by_name


def process_modifiers(basis, patch_by_name, entities):
    if 'ActiveModifiers' in patch_by_name:
        basis = basis.copy()

        for string in patch_by_name['ActiveModifiers']:
            _pb = pb_dm.CDOTAModifierBuffTableEntry()
            _pb.ParseFromString(string.value)

            basis[_pb.parent][_pb.index] = _pb

        keep = []
        for parent in basis:
            if parent in entities.entry_by_ehandle:
                keep.append(parent)

        return c.defaultdict(dict, {k:basis[k] for k in keep})

    return basis


def process_string_tables(basis, patch_by_name):
    string_list_by_name = dict()

    for name, patch in patch_by_name.items():
        # loop through existing, copying present strings
        string_list = []
        listed = c.OrderedDict([(s.ind,s) for s in patch])

        for string in basis[name]:
            if string.ind in listed:
                string = listed[string.ind]
                del listed[string.ind]

            string_list.append(string)

        # whatever is left over is new
        for string in listed.values():
            string_list.append(string)

        string_list_by_name[name] = string_list

    return basis + stt_cllctn_strngtbls.mk(string_list_by_name)


def mk_game_events(game_event_by_id, all_svc_game_event):
    game_events = c.defaultdict(list)

    for peek, message in all_svc_game_event:
        pb = pb_nbt.CSVCMsg_GameEvent()
        pb.ParseFromString(message)

        keys = game_event_by_id[pb.eventid].keys
        game_events[pb.eventid].append(stt_utl.parse_game_event(pb, keys))

    return game_events


def mk_user_messages(all_svc_user_message):
    user_messages = c.defaultdict(list)

    for peek, message in all_svc_user_message:
        pb = pb_nbt.CSVCMsg_UserMessage()
        pb.ParseFromString(message)

        user_message_type = pb.msg_type

        if user_message_type == pb_dum.DOTA_UM_GamerulesStateChanged:
            # this is a one-off
            namespace = pb_dum
            impl = 'CDOTA_UM_GamerulesStateChanged'
        else:
            namespace = pb_um if user_message_type < THRESHOLD else pb_dum
            infix = 'DOTA' if namespace is pb_dum else ''
            suffix = UserMessageByKind[user_message_type]
            impl = 'C{0}UserMsg_{1}'.format(infix, suffix)

        try:
            _pb = getattr(namespace, impl)()
            _pb.ParseFromString(pb.msg_data)
        except UnicodeDecodeError, e:
            print '! unable to decode protobuf: {}'.format(e)
        except AttributeError, e:
            err = '! protobuf {0}: open issue at github.com/skadistats/skadi'
            print err.format(impl)
            raise e

        user_messages[user_message_type].append(_pb)

    return user_messages


class Match(object):
    def __init__(self, prologue, basis, window=1, o=None):
        if o is None:
            o = O.game_events | O.modifiers | O.user_messages

        self.prologue = prologue
        self.snapshots = c.deque([basis], maxlen=window)
        self.modifiers = o & O.modifiers
        self.game_events = o & O.game_events
        self.user_messages = o & O.user_messages

    def snapshot(self, tick, packet_data):
        prior_snapshot = self.snapshots[-1]

        packet_index = ndx_mbd_dmpckt.mk(list(io_mbd.mk(packet_data)))

        ped = self.prologue.packet_entities_decoder
        spe = packet_index.svc_packet_entities

        st = prior_snapshot.string_tables
        md = prior_snapshot.modifiers
        en = process_entities(prior_snapshot.entities, ped, spe)

        asust = packet_index.all_svc_update_string_table
        if asust:
            stdbn = self.prologue.string_table_decoder_by_name
            stdiff = diff_string_tables(st, stdbn, asust)
            if self.modifiers:
                md = process_modifiers(md, stdiff, en)
            else:
                md = dict()
            st = process_string_tables(st, stdiff)

        gebi = self.prologue.game_event_by_id

        if self.game_events:
            ge = mk_game_events(gebi, packet_index.all_svc_game_event)
        else:
            ge = dict()

        if self.user_messages:
            um = mk_user_messages(packet_index.all_svc_user_message)
        else:
            um = dict()

        snapshot = Snapshot(tick, en, st, md, ge, um)
        self.snapshots.append(snapshot)

        return snapshot
