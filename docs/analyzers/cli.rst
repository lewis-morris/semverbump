CLI Analyzer
============

Tracks ``argparse`` or ``click`` command-line interfaces.

Dependencies
~~~~~~~~~~~~

* ``click`` (optional for Click-based CLIs)

Enable or disable
~~~~~~~~~~~~~~~~~

Set ``cli`` under ``[analyzers]`` to ``true`` or ``false``.

.. code-block:: toml

   [analyzers]
   cli = true  # set to false to disable

Severity rules
~~~~~~~~~~~~~~

* Added command → minor
* Removed command → major
* Added optional option → minor
* Added required option → major
* Removed optional option → minor
* Removed required option → major
* Option became optional → minor
* Option became required → major

Detectable change
~~~~~~~~~~~~~~~~~

.. code-block:: diff

   @@
   @click.command()
   def greet(name):
       ...
   +@click.option("--force", required=True)
   +def greet(name, force):
   +    ...

Example output
~~~~~~~~~~~~~~

::

   - [MAJOR] greet: Added required option '--force'
