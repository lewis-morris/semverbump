Migrations Analyser
===================

Scans Alembic migrations for schema impacts.

Dependencies
~~~~~~~~~~~~

* ``Alembic``

Enable or disable
~~~~~~~~~~~~~~~~~

Configure ``[migrations]`` paths and enable the analyser:

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

.. code-block:: text

   - [MAJOR] migrations/20240401_add_email.py: Added non-nullable column
