Usage
=====

The ``bumpwright`` command-line interface provides tools to manage project versions based on public API changes. By default, the ``bump`` subcommand compares the current commit against the last release commit, or the previous commit (``HEAD^``) when no release exists. This page lists shared options and links to individual command guides.

Global options
--------------

``--config``
    Path to the configuration file. Defaults to ``bumpwright.toml`` in the current working directory.

Commands
--------

.. toctree::
   :maxdepth: 1

   init
   bump
