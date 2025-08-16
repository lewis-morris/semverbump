bumpwright documentation
========================

.. |coverage| image:: _static/badges/coverage.svg
   :alt: test coverage
.. |version| image:: _static/badges/version.svg
   :alt: latest version
.. |python| image:: _static/badges/python.svg
   :alt: supported Python versions
.. |license| image:: _static/badges/license.svg
   :alt: license

|coverage| |version| |python| |license|

Introduction
------------

Bumpwright is a static analysis tool that compares two Git references and
recommends the appropriate semantic version bump. Unlike tools such as
``bump2version`` or ``python-semantic-release`` that rely on manual hints or
commit messages, Bumpwright inspects the public API itself, making it ideal for
libraries and services that expose stable interfaces.

New to Bumpwright? Start with the :doc:`quickstart`.

Benefits
~~~~~~~~

- **Simplicity** – run a single command to see how your API changed.
- **Flexibility** – enable analysers and override defaults to fit your workflow.
- **Accuracy** – catch breaking changes that commit messages may miss.

Trade-offs
~~~~~~~~~~

- Requires a baseline reference to compare against.
- Static heuristics cannot account for runtime behaviour.

Primary use cases
~~~~~~~~~~~~~~~~~

- Library maintainers verifying API stability before release.
- CI/CD pipelines enforcing semantic versioning.
- Release managers reviewing change impact.

Quickstart Guide
----------------

.. toctree::
   :maxdepth: 2

   installation
   quickstart

Core Concepts
-------------

.. toctree::
   :maxdepth: 2

   versioning
   configuration

Basic Usage
-----------

.. toctree::
   :maxdepth: 2

   usage/index

Advanced Usage
--------------

.. toctree::
   :maxdepth: 2

   advanced/index
   guides/index

Reference
---------

.. toctree::
   :maxdepth: 2

   cli_reference
   analysers/index

Examples & Recipes
------------------

.. toctree::
   :maxdepth: 2

   recipes/index

CI integration
--------------

.. toctree::
   :maxdepth: 2

   ci/github-actions

Troubleshooting & FAQ
---------------------

.. toctree::
   :maxdepth: 1

   troubleshooting

Changelog & Contribution Guide
------------------------------

.. toctree::
   :maxdepth: 1

   contributing
   roadmap

