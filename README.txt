Installing
==========

Installing PyOLS is as simple as::

    $ sudo python setup.py install

PyOLS can now be started by running::

    $ pyols -c env_dir
    $ pyols !$

It is worth examining the output of ``pyols --help`` to see the options
that are available (espeically the ``--wrapper`` option).

After PyOLS is installed, ``init.d/README.txt`` will help you start
PyOLS when your system starts.

Developing
==========

Developing With PyOLS
---------------------

When developing with PyOLS (that is, writing an application which calls
PyOLS), it will be useful to have a copy of the PyOLS API documentation
close at hand.  This can be found in the ``doc`` subdirectory.

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
with the neww functionality then execute the file (``python foo.py``)
to verify that both your changes and doctests are correct.

.. _doctests: http://docs.python.org/lib/module-doctest.html
