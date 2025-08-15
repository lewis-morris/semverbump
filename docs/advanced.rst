Advanced Usage
==============

Customize rules for version decisions:

.. code-block:: toml

   [rules]
   return_type_change = "major"

Exclude paths from API scanning:

.. code-block:: toml

   [ignore]
   paths = ["tests/**", "examples/**"]

Specify additional version file locations:

.. code-block:: toml

   [version]
   paths = ["pyproject.toml", "setup.py", "src/pkg/__init__.py"]
   ignore = ["examples/**"]

Apply a bump and commit/tag automatically:

.. code-block:: console

   bumpwright auto --base v1.0.0 --head HEAD --commit --tag

Integrating with CI pipelines
-----------------------------

1. Add a GitHub Actions workflow to run ``bumpwright`` on pull requests:

   .. code-block:: yaml

      name: Version check
      on: [pull_request]
      jobs:
        bumpwright:
          runs-on: ubuntu-latest
          steps:
            - uses: actions/checkout@v4
            - uses: actions/setup-python@v5
              with:
                python-version: '3.x'
            - run: pip install bumpwright
            - run: bumpwright decide --base origin/main --head ${{ github.sha }}

2. Review the workflow logs to see the suggested bump:

   .. code-block:: text

      **bumpwright** suggests: `patch`
      - [PATCH] util.helper: added optional argument 'verbose'

Handling multi-package repositories
-----------------------------------

1. Configure version file paths for each package in ``bumpwright.toml``:

   .. code-block:: toml

      [version]
      paths = [
        "packages/pkg_a/pyproject.toml",
        "packages/pkg_b/pyproject.toml",
      ]

2. Run ``bumpwright`` for the package that changed:

   .. code-block:: console

      bumpwright bump --level minor --pyproject packages/pkg_a/pyproject.toml

   .. code-block:: text

      Updated packages/pkg_a/pyproject.toml from 0.4.1 to 0.5.0

Custom severity mapping and plugin analyzers
--------------------------------------------

1. Create a plugin that reports ``print`` usage:

   .. code-block:: python

      from bumpwright.analyzers import Analyzer, register
      from bumpwright.compare import Impact

      @register("no_prints")
      class NoPrints(Analyzer):
          def __init__(self, cfg):
              self.severity = getattr(cfg.rules, "print_call", "patch")

          def collect(self, ref):
              return Path("example.py").read_text()

          def compare(self, old, new):
              if "print(" in new and "print(" not in old:
                  return [Impact(self.severity, "example.py", "Added print call")]
              return []

2. Enable the plugin and map its finding to a version bump:

   .. code-block:: toml

      [analyzers]
      no_prints = true

      [rules]
      print_call = "patch"

3. Execute the analyzer:

   .. code-block:: console

      bumpwright decide --base HEAD^ --head HEAD

   .. code-block:: text

      **bumpwright** suggests: `patch`
      - [PATCH] example.py: Added print call
