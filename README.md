Skadi
=====

Skadi parses [Dota 2](http://www.dota2.com) replay files.

**This project is in its early stages, and things are subject to change without much notice. Consequently, Skadi is best used for development purposes at this time. For up-to-date information, join #dota2replay on Quakenet IRC.**


The Wiki
========

I hereby resolve that the Wiki pages of this repository will not suck. In them, you will find as much information as I have time to type. Start [here](https://github.com/onethirtyfive/skadi/wiki/Skadi:-More-Than-You-Ever-Wanted-to-Know).

Be sure to check out the "Pages" section.


In a Hurry?
===========

Check out some simple usage in [bin/skadi](https://github.com/onethirtyfive/skadi/blob/master/bin/skadi).


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


Thanks
======

I use the pioneering [edith](https://github.com/dschleck/edith) project as a reference implementation for parsing bit streams.

A big shoutout to the folks in #dota2replay on Quakenet. Feel free to stop by if you have any questions! (Be patient, we're around!)


License
=======

**Visible attribution is kindly requested. I want Dota 2 fans to know about this project!**

Skadi is offered under the [MIT license](https://github.com/onethirtyfive/skadi/blob/master/LICENSE).

This license applies to all revisions of source code until otherwise stated.
