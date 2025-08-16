Installation
============

Requires Python 3.11 or later.

Install ``bumpwright`` from PyPI:

.. code-block:: console

   pip install bumpwright

Optional analysers may require extra dependencies:

- ``click`` (only if your project uses it) for the CLI analyser
- ``flask`` or ``fastapi`` for the web route analyser
- ``alembic`` for the migrations analyser
- ``PyYAML`` for the OpenAPI analyser
- ``graphql-core`` for the GraphQL analyser
