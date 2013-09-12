Skadi
=====

Skadi parses [Dota 2](http://www.dota2.com) replay files.

**This project does not yet use semantic versioning. There is no public/private API distinction at this point, though we are increasingly resisting changes to the main demo/streaming interface. For now, best to use skadi with some caution. It may not be production ready.**


The Wiki
========

We will be moving everything currently in this README into the [wiki](https://github.com/onethirtyfive/skadi/wiki) soon™.

Be sure to check out the "Pages" section, since organization is a work in progress.


In a Hurry?
===========

Check out some simple usage in [bin/skadi](https://github.com/onethirtyfive/skadi/blob/master/bin/skadi).


Dependencies
============

Über-hacker @Noxville points out a helpful way of installing everything in Ubuntu:

    (might need to be superuser to execute)
    easy_install --allow-hosts pypi.python.org protobuf
    apt-get install python-snappy

The `--allow-hosts` option is important, since the default hosted version on Google Code is broken.

If you're on a different distribution or have environmental particularities, you're going for **libraries** (including dev libs) and **bindings** for:

* snappy

And python **bindings** for:

* protobuf


Thanks
======

I use the pioneering [edith](https://github.com/dschleck/edith) project as a reference implementation for parsing bit streams.

A big shoutout to the folks in #dota2replay on Quakenet. Feel free to stop by if you have any questions! (Be patient, we're around!)


License
=======

**We're counting on you: please mention Skadi when used in your projects. We ask for "Powered by [Skadi](https://github.com/skadistats/skadi)" in the footer of your site template.**

Skadi is offered under the [MIT license](https://github.com/onethirtyfive/skadi/blob/master/LICENSE).

This license applies to all revisions of source code until otherwise noted in the latest version of this document.
