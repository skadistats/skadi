Skadi
=====

Skadi parses [Dota 2](http://www.dota2.com) replay files.


The Wiki
========

I hereby resolve that the Wiki pages of this repository will not suck. In them, you will find as much information as I have time to type. Start [here](https://github.com/onethirtyfive/skadi/wiki/Skadi:-More-Than-You-Ever-Wanted-to-Know).

About Dota 2 Replay Files
=========================

Dota 2 is based on Valve's Source Engine. Source allows Dota 2 and the game server your game is hosted on to exchange game data efficiently.

Skadi parses Dota 2 replays, which are in essence a one-way stream of messages from an imaginary server to the Dota 2 client. These messages contain information describing:

* server info
* the types (aka **entity classes**) of things (aka **entities**) in the game, and their associated properties
* the entities in the game at each 1/30th of a second in the game (aka **tick**)

And, finally, the way these entities' data changes over time during the game.

This is a simplified explanation, but it's good enough to get started.

**tl;dr** There is no tl;dr. You need to know this stuff right now to use Skadi.

Included in Skadi is a simple script [script](https://github.com/onethirtyfive/skadi/blob/master/bin/skadi) which illustrates some usage. This script will evolve alongside the library, and will eventually be a command-line tool for extracting data.


For the Curious
===============

\[Definitely a work in progress.\]

Dota 2 replays are comprised entirely of Google protobuf messages. Enquiring minds can inspect the protobuf language definitions in the [protobuf](https://github.com/onethirtyfive/skadi/blob/master/protobuf) directory.

`demo.proto` defines messages that are immediately readable from the demo file. (I refer to them as 'top-level' messages.) Confusingly, some `demo.proto` messages have *their own* messages embedded within a `bytes` property. `CDemoPacket`, `CDemoSendTables`, and a few others, do this. These embedded messages are defined in `netmessages.proto`. These include `CSVCMsg_PacketEntities` (where the magic happens!), `CSVCMsg_UserMsg` (many things, including mouse clicks and chat!), and more.

Skadi indexes all **top-level** messages into `peeks` when it opens a demo file. Peeks are a little summary of the messages Skadi encountered as it was indexing. You don't have to worry about this, but it helps to know if you're peeking into index data structures.

Demo messages between the `CDemoSyncTick` message and the `CDemoStop` are what comprise the actual game.

Actual game data is encapsulated in two types of `demo.proto` messages, each with a different purpose: `CDemoFullPacket` is a snapshot of the game's *entire* state at that tick, and `CDemoPacket` is a "diff" between the previous tick and this one, entity-state-wise. Consequently, `CDemoFullPacket` is used only when scanning to a particular point in the game--that's why they're there!

What complicates things is what happens before `CDemoSyncTick`. You can find this implementation in `skadi.replay.demo` if interested, but it will likely leave you scratching your head. There is much complexity setting up a demo.


For the Hurried
===============

But when you do want to stream, you'll need a `demo`:

    from skadi.replay import demo as rd

    with io.open('123123123.dem', 'r+b') as infile:
      demo = rd.construct(infile)

      # And then you'll ask it for a `stream`:
      stream = demo.stream(tick=12345) # tick arg is optional

      # And iterate over each tick:
      for tick, string_tables, world in stream:

        # world contains information about all the entities:
        for ehandle, state in world.items():
          # an ehandle is a replay-wide unique identifier for an entity
          # the state is just a plain old hash of keys and values
          print ehandle, len(state)

Entity state is based off of the "associated properties" I mentioned at the beginning of this document. I build these when you construct a demo.

Each key in the state is a two-item tuple:

    (property origin, property name)

To uniquely identify a piece of state, you need both of these bits of info. This is because entity classes are part of an elaborate hierarchy--they inherit properties from parent, all the way up to their `baseclass`. Investigate the state. The property names should make sense. Play with the values you get from the keys and you'll start discovering a wealth of game data.

One last caveat: if you encounter a property name with the prefix 'm_h', or if the name indicates something relational, you might have found an `ehandle`. You can ask the `world` for an entity by ehandle with the method `find`. It will return that entity's state. With this, you can relate entities to one another--the data does that a lot!

**This API is under heavy development. We don't even know what all the data means. But someone gets to discover it. You, hopefully! Please share your discoveries on #dota2replay or by a pull request, and keep your eyes open for a better interface soon.**


Development Notice
==================

I haven't really adopted a formal development versioning scheme for Skadi yet, because it's needs more utility before being generally useful. Consequently, the APIs are subject to change. Be mindful of the version you have checked out when you accomplish something with the library.

This will not be the case forever.


Dependencies
============

Über-hacker @Noxville points out a helpful way of installing everything in Ubuntu:

    (might need to be superuser to execute)
    easy_install --allow-hosts pypi.python.org protobuf
    easy_install bitstring 
    apt-get install python-snappy

The `--allow-hosts` option is important, since the default hosted version on Google Code is broken.

If you're on a different distribution or have environmental particularities, you're going for **libraries** (including dev libs) and **bindings** for:

* snappy

And python **bindings** for:

* protobuf
* bitstring


Attribution
===========

I will use the pioneering [edith](https://github.com/dschleck/edith) project as a reference implementation for parsing bit streams.

Special thanks to the folks in #dota2replay on quakenet. Feel free to stop by if you have any questions! (Be patient, we're around!)


License
=======

**Visible (textual) attribution is kindly requested. I want Dota 2 fans to know about this project!**

Skadi is offered under the [MIT license](https://github.com/onethirtyfive/skadi/blob/master/LICENSE).

This license applies to all revisions of source code until otherwise stated.
