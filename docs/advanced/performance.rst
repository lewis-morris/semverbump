Performance & caching
=====================

Caching is on by default and speeds up repeated bumps in the same process.
Resolving version file patterns is cached to avoid repeated filesystem
globbing. A simple benchmark scanning 1,000 files shows the impact:

.. code-block:: text

    First call:  0.1167s
    Second call: 0.0001s

Measured on CPython 3.12 using ``time.perf_counter``. Subsequent calls reuse
cached results, dramatically reducing overhead when applying multiple bumps in
one process.

In scenarios where versioned files may be created or removed dynamically,
invoke ``bumpwright.versioning.clear_version_file_cache()`` to drop cached
results before the next bump. The cache is also cleared automatically whenever
``apply_bump`` is called with different ``paths`` or ``ignore`` patterns from
the previous invocation.

