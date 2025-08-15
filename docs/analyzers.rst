Additional Analyzers
====================

Enable optional analyzers in ``bumpwright.toml``:

.. code-block:: toml

   [analyzers]
   cli = true
   web_routes = true
   migrations = true

   [migrations]
   paths = ["migrations"]

Plugin utilities
----------------

The :mod:`bumpwright.analyzers` module provides helpers for managing
analyzer plugins. Plugins register themselves via
``bumpwright.analyzers.register`` and can be introspected using
``available`` and ``get``.

.. code-block:: python

   from bumpwright.analyzers import available, get, register

Attempting to register a plugin with a duplicate name raises
``AnalyzerRegistrationError``. ``get`` returns the analyzer class for a
given name and raises ``AnalyzerNotFoundError`` if the analyzer is not
registered.

CLI Analyzer
------------

Tracks ``argparse`` or ``click`` command-line interfaces.

Dependencies
~~~~~~~~~~~~

* ``click`` (optional for click-based CLIs)

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

Web Route Analyzer
------------------

Detects HTTP route changes in Flask or FastAPI apps.

Dependencies
~~~~~~~~~~~~

* ``Flask`` or ``FastAPI``

Enable or disable
~~~~~~~~~~~~~~~~~

Set ``web_routes`` under ``[analyzers]``.

.. code-block:: toml

   [analyzers]
   web_routes = true  # set to false to disable

Severity rules
~~~~~~~~~~~~~~

* Added route → minor
* Removed route → major
* Added optional param → minor
* Added required param → major
* Removed optional param → minor
* Removed required param → major
* Param became optional → minor
* Param became required → major

Detectable change
~~~~~~~~~~~~~~~~~

.. code-block:: diff

   @@
   @app.get("/users/{user_id}")
   -def get_user(user_id: int):
   -    ...
   +def get_user(user_id: int, verbose: bool = False):
   +    ...

Example output
~~~~~~~~~~~~~~

::

   - [MINOR] GET /users/{user_id}: Added optional param 'verbose'

Migrations Analyzer
-------------------

Scans Alembic migrations for schema impacts.

Dependencies
~~~~~~~~~~~~

* ``Alembic``

Enable or disable
~~~~~~~~~~~~~~~~~

Configure ``[migrations]`` paths and enable the analyzer:

.. code-block:: toml

   [analyzers]
   migrations = true  # set to false to disable

   [migrations]
   paths = ["migrations"]

Severity rules
~~~~~~~~~~~~~~

* Dropped column → major
* Added non-nullable column without default → major
* Added column → minor
* Added index → minor

Detectable change
~~~~~~~~~~~~~~~~~

.. code-block:: diff

   @@
   def upgrade():
   -    pass
   +    op.add_column("users", sa.Column("email", sa.String(), nullable=False))

Example output
~~~~~~~~~~~~~~

::

   - [MAJOR] migrations/20240401_add_email.py: Added non-nullable column
