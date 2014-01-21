Skadi
=====

Skadi parses [Dota 2](http://www.dota2.com) replay files.

**This project does not yet use semantic versioning. There is no public/private API distinction at this point, though we are increasingly resisting changes to the main demo/streaming interface. For now, best to use Skadi with some caution. It may not be production ready.**


The Wiki
========

We will be moving everything currently in this README into the [wiki](https://github.com/onethirtyfive/skadi/wiki) soon™.

Be sure to check out the "Pages" section, since organization is a work in progress.


In a Hurry?
===========

Check out some simple usage in [bin/skadi](https://github.com/onethirtyfive/skadi/blob/master/bin/skadi).


Installation
============

Skadi comes in two forms; as a pure Python library and as a cython optimised library. The cython version is significantly faster (from 2x to over 3x the speed), but may not work on all systems. To install the cython version, use:

    python setup.py install

And, if that fails, the pure python version:

    python setup_basic.py install

If you are doing development work on skadi, or don't want to install it but still want to use the cython accelerated modules, you can build the cython modules in place:

    python setup.py build_ext -i

### Dependencies

#### Cython

The following C libraries and development headers are required

 * snappy
 * python-dev

And the python packages

 * protobuf

To install these dependencies with Ubuntu/Debian, the following may work:

    apt-get install python-dev python-snappy python-protobuf

#### Pure Python

The following C libraries and python bindings are required:

 * snappy

And the python packages

 * protobuf
 * bitstring

To install these dependencies with Ubuntu/Debian, the following may work:

    apt-get install python-snappy python-protobuf
    pip install bitstring

Thanks
======

I use the pioneering [edith](https://github.com/dschleck/edith) project as a reference implementation for parsing bit streams.

A big shoutout to the folks in #dota2replay on Quakenet. Feel free to stop by if you have any questions! (Be patient, we're around!)


License
=======

**We're counting on you: please mention Skadi when used in your projects. We ask for "Powered by [Skadi](https://github.com/skadistats/skadi)" in the footer of your site template.**

Skadi is offered under the [MIT license](https://github.com/onethirtyfive/skadi/blob/master/LICENSE).

This license applies to all revisions of source code until otherwise noted in the latest version of this document.
