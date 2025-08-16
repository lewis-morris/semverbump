Cache performance
=================

Resolving version file patterns is cached to avoid repeated filesystem
globbing. A simple benchmark scanning 1,000 files shows the impact:

.. code-block:: text

    First call:  0.1167s
    Second call: 0.0001s

Measured on CPython 3.12 using ``time.perf_counter``. Subsequent calls reuse
cached results, dramatically reducing overhead when applying multiple bumps in
one process.

