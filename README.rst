Installing
==========

Installing PyOLS is as simple as::

    $ sudo python setup.py install

PyOLS can now be started by running::

    $ pyols -c env_dir
    $ pyols !$

It is worth examining the output of ``pyols --help`` to see the options
that are available (especially the ``--wrapper`` option).

After PyOLS is installed, ``init.d/README.txt`` will help you start
PyOLS when your system starts.

SCGI Setup
----------

If the SCGI wrapper is going to be used a webserver needs to be setup
to act as the frontend.

While many web servers support the SCGI proticol, I will only describe
the setup procedure for Apache here.  Instructions for other servers,
such as lighttpd, can be easily found on Google.

  1. Make sure the SCGI module is installed (for example, on Debian,
     run: ``apt-get isntall libapache2-mod-scgi``).

  2. Enable the SCGI module.  With Apache 2 on Debian, the command
     is ``a2enmod scgi``.  On other distributions, a line similar to
     ``LoadModule scgi_module mod_scgi.so`` will need to be added
     to ``apache.conf`` (or ``httpd.conf``, or ``modules.conf``,
     depending on your distribution's naming standard).

  3. Add the line ``SCGIMount /$PATH $HOST:$PORT`` to ``apache.conf``
     (or ``httpd.conf``, depending on your distribution's naming
     scheme), where ``$PATH`` is replaced by the path which PyOLS
     will be accessable from (eg, ``/pyols``), ``$HOST`` is the host
     PyOLS will be running on (probably ``localhost``) and ``$PORT``
     is the port PyOLS will be running on (probably ``4000``).

Developing
==========

Developing With PyOLS
---------------------

When developing with PyOLS (that is, writing an application which calls
PyOLS), it will be useful to have a copy of the PyOLS API documentation
close at hand.  This can be found in the ``doc/api`` subdirectory of
the tarball.  The most relevant file will be be
``doc/api/pyols.api.OntologyTool-class.html``, which contains all the
functions available over RPC.

Developing on PyOLS
-------------------

To get started working with PyOLS, setup a "development" installation::

    $ python setup.py develop

This will do two things:  install a ``pyols`` package which will link
to the current directory (so there is no need to fuss with symlinks or
re-run setup.py after each change), and it will install the ``nose``
and  ``pyparsing`` packages (used for testing)

Running Tests
^^^^^^^^^^^^^

Running the PyOLS unit tests is simple... So you'd better do it!  Simply
run ``nosetests`` in whatever directory you want tested.  For example::

    ~/pyOLS/pyols/$ nosetests
    ...........................................
    ----------------------------------------------------------------------
    Ran 43 tests in 6.059s
    
    OK

Many files also contain doctests_, and at the bottom of these files
there will be the lines::

    from pyols.tests import run_doctests
    run_doctests()

As the name suggests, this will run doctets on the module (but, if you
care to look at the implementation of ``run_doctests``, only if the
module is being run directly from the command line).

So, after editing a function with doctests, always update the doctests
with the new functionality then execute the file (``python foo.py``)
to verify that both your changes and doctests are correct.

.. _doctests: http://docs.python.org/lib/module-doctest.html

Gotchas
^^^^^^^

The Namespace.copy_to method makes some SQLite-specific
assumptions... Check it if you are migrating to a new database.
