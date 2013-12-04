Skadi 1.0 README (wip)
======================

Everything in this codebase is subject to change before official release,
though most of it is pretty well done and working.


Important License Change
========================

Please re-read LICENSE, giving special consideration to clause 4. For versions
1.0 and onward (barring any later changes), Skadi now requires attribution,
with additional requirements for web applications built using the library.


Example Usage
=============

    import importlib as il
    import io
    import os

    __impl__ = 'skadi_ext' if os.environ.get('SKADI_EXT') else 'skadi'
    io_dm = il.import_module(__impl__ + '.io.demo')

    from skadi.index import prologue as ndx_prlg
    from skadi.state import match as stt_mtch
    from skadi.state import util as stt_utl
    from skadi.state.util import PVS
    import skadi.demo as demo


    pwd = os.path.dirname(__file__)
    PATH = os.path.abspath(os.path.join(pwd, 'demos', '37633163.dem'))


    with io.open(PATH, mode='rb') as infile:
        io_demo = io_dm.mk(infile)
        io_demo.bootstrap() # read and ensure header
        prologue = ndx_prlg.parse(io_demo) # read and create demo prologue

        full_packets, packets = demo.preroll(io_demo, 20000)
        match = stt_mtch.mk(prologue, full_packets, packets)

        for snapshots in demo.play(io_demo, match):
            for index, entry in snapshots[-1].entities.entry_by_index.items():
                pvs, entity = entry
                recv_table = prologue.recv_tables.by_cls[entity.cls]

                if pvs & PVS.Enter:
                    pvs_desc = 'ENTER'
                elif pvs & PVS.Leave:
                    pvs_desc = 'LEAVE'
                    if pvs & PVS.Delete:
                        pvs_desc += ' (DELETE)'

                print pvs_desc, '#{}'.format(index), recv_table.dt

                for i, v in entity.state.items():
                    recv_prop = recv_table.by_index[i]
                    prop_desc = '({}, {})'.format(recv_prop.src, recv_prop.name)
                    print '  {}: {}'.format(prop_desc, v)

The `snapshots` variable yielded to the `for` loop is a rotating window of
recent game snapshots. You can get the most recent one with `snapshots[-1]`.
This is implemented according to the idea that some data processing might
reasonably want a rolling window of previous world states.

A snapshot has the following attributes, and can be deconstructed like a
regular tuple, or each attribute accessed by name as a property:

1. `tick` (an int tick of the snapshot)
2. `entities` (a specialized collection of entity data)
3. `string_tables` (a specialized collection of string tables)
4. `modifiers` (a dict mapping ehandles to modifier protobuf msgs)
5. `game_events` (a dict mapping int values to a list of game events)
6. `user_messages` (a dict mapping int values to a list of user messages)

The modifiers are guaranteed to have a corresponding entity in the current
snapshot, unlike in the previous version of skadi.

Game events and user messages are transient--each list comes from that
specific tick and no other. These are just regular lists of protobuf messages.

Notes
=====

Ask questions on #dota2replay.
